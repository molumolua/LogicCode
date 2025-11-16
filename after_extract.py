from process_dataset import load_and_prepare_dataset,prepare_examples
from extract import extract_last_code_block,parse_gen_script,parse_one_gen_script,get_function_code_from_str
from logger import setup_logger
import copy
from typing import Tuple, Optional, List, Dict, Any
import inspect
import json
from exec_and_verify import build_and_run_reference_solution,write_and_build_referenece_solution,run_reference_solution,import_needed_module_for_python,fix_newlines_in_python_strings,run_generator_with_alarm,sandboxfusion_run
from tqdm import tqdm
import json
from pathlib import Path
from collections import defaultdict
def exec_and_return_values(code_str: str, var_names: List[str], logger) -> Optional[Dict[str, Any]]:
    """
    在隔离的命名空间中执行代码字符串，并返回指定变量的值。
    如果执行失败或变量缺失，返回 None 并记录日志。
    """
    _logger = logger
    try:
        ns: Dict[str, Any] = {}
        exec(code_str, {}, ns)

        result = {}
        for var in var_names:
            if var not in ns:
                _logger.error("Missing required variable: %s", var)
                return None
            result[var] = ns[var]
        return result

    except Exception as e:
        _logger.exception("exec_and_return_values failed: %s", e)
        return None
    


def verify_logic_problem_generation(default_problems,logger):
    _logger = logger
    
    left_problems=[]
    success_problems=[]
    for example in default_problems:
        code,lang = extract_last_code_block(example['answer'])
        success_flag=False
        if lang and lang =="python":
            function_code = get_function_code_from_str(code,"generate_logic_problem")
            if function_code is None:
                _logger.error("Failed to extract required function from code.")
            else:
                success_flag=True
                # print(function_code)
                success_problems.append({
                    **example,
                    "generate_logic_problem":{
                        "raw_code":code,
                        "lang":lang,
                        "function":function_code
                    }
                })
                
        if not success_flag:
            left_problems.append(example)
    return success_problems,left_problems

def verify_and_get_test_case_output(solution_submissions,input_json_list,check_number,logger,debug=False):
    input_list = [item['test_case'] for item in input_json_list]
    # solution_codes = [item['code'] for item in solution_submissions]
    compare_to_check_list = [] # [K个不同的submssions, N个input]
    for solution_item in solution_submissions:
        solution_code = solution_item['code']
        solution_lang = solution_item['language']
        if solution_lang == "cpp" or solution_lang == "python": 
            # 获取 input、output、运行是否成功
            checked_list = build_and_run_reference_solution(solution_code=solution_code,inputs=input_list,logger=logger,debug=debug)
            if checked_list: compare_to_check_list.append(checked_list)
    
        if len(compare_to_check_list) >= check_number:
            break
    if len(compare_to_check_list) <= 2 :
        if logger and debug :logger.error("Not enough submission to check test case correctness.")
        return None
    
    final_checked_list = []
    N = len(input_list)
    for idx in range(N):
        final_flag = True
        for k,checked_list in enumerate(compare_to_check_list[:-1]):
            now_submission_output =  checked_list[idx]['output']
            nxt_submission_output = compare_to_check_list[k+1][idx]['output']
            if str(now_submission_output).rstrip("\n") != str(nxt_submission_output).rstrip("\n"):
                final_flag = False
        if final_flag:
            final_checked_list.append({
                "input":compare_to_check_list[0][idx]['input'],
                "output":compare_to_check_list[0][idx]['output']
            })
            
    if len(final_checked_list)>= 1:        
        return final_checked_list
    else:
        return None
        
        
import re

def is_valid_number(s: str) -> bool:
    # 使用正则表达式检查是否是有效的整数或浮点数
    return bool(re.fullmatch(r'^\s*-?\d+(\.\d+)?\s*$', s.strip()))

def filter_only_numerical_problem(correct_test_cases):
    numerical_flag = True
    for test_case in correct_test_cases:
        if not is_valid_number(test_case['output']):
            numerical_flag = False
    return numerical_flag
            
        
def verify_and_extract_test_case(code_list, logger, debug=False,check_number=3,filter_numerical=True):
    _logger = logger
    success_problems = []
    left_problems = []

    for example in tqdm(code_list, desc="Processing test cases", unit="problem", ncols=100, ascii=True):
        code, lang = extract_last_code_block(example['answer'])
        todo_flag = False
        if lang and lang == "json":
            try:
                # print(code)
                json_input_list = json.loads(code)
                correct_test_cases = verify_and_get_test_case_output(
                    example['correct_submissions'],
                    json_input_list,
                    check_number=check_number,
                    logger=_logger,
                    debug=debug
                )
                if correct_test_cases:
                    todo_flag = True
                    if filter_numerical and (not filter_only_numerical_problem(correct_test_cases)):
                        continue
                    
                    success_problems.append({
                        **example,
                        "raw_input_list": json_input_list,
                        "test_case_list": correct_test_cases
                    })
                else:
                    _logger.error("No test case passed the test.")
            except Exception as e:
                _logger.error(f"Error in loading JSON list: {e}")
        else:
            _logger.error("No JSON code.")
        
        if not todo_flag:
            left_problems.append(example)

    return success_problems, left_problems


def heuristic_estimate_function(input_str,
                                max_len=500,
                                max_number=1000,
                                avg_enable=True,
                                max_number_bit=18,
                                standard_deviation_enable=False,
                                logger=None,
                                debug =False):
    invalid_flag = False
    items = input_str.split()
    
    len_score = len(input_str)/max_len
    
    if len_score > 1.0:
        if logger and debug: logger.warning(f"Input length {len(input_str)} exceeds max_len {max_len}.")
        invalid_flag = True
    
    standard_deviation_score = None
    avg_score = None
    
    all_numerical_flag = True
    numbers= []
    total_sum = 0.0  # 初始化总和
    for item in items:
        try:
            if len(item)<=max_number_bit:
                num = float(item)
                total_sum += num
                if num > max_number:
                    if logger and debug: logger.warning(f"Number {num} exceeds max_number {max_number}.")
                    invalid_flag = True
                numbers.append(num)
        except ValueError:
            all_numerical_flag = False
            break
    
    if invalid_flag:
        if logger and debug: logger.warning("Input is invalid.")
        return None
    
    if all_numerical_flag and len(items)>0:
        
        if avg_enable:
            avg_sum = total_sum/len(items)
            avg_score = avg_sum/max_number
            
        if standard_deviation_enable:
            standard_deviation_score = (sum((x - (total_sum/len(items))) ** 2 for x in numbers) / len(items)) ** 0.5 / max_number
    
    return {
        "len_score": len_score,
        "avg_score": avg_score,
        "standard_deviation_score": standard_deviation_score
    }

def sort_and_deduplicate_test_case_list(test_case_list):
    len_score_flag = True
    avg_score_flag = True
    standard_deviation_flag = True
    
    # Check if each score field exists
    for test_case in test_case_list:
        if not test_case['difficulty'].get('len_score'):
            len_score_flag = False
        if not test_case['difficulty'].get('avg_score'):
            avg_score_flag = False
        if not test_case['difficulty'].get('standard_deviation_score'):
            standard_deviation_flag = False
    
    # Define a function to calculate the sum of available scores for each test case
    def score_sum(test_case):
        total_score = 0
        if len_score_flag:
            total_score += test_case['difficulty'].get('len_score', 0)
        if avg_score_flag:
            total_score += test_case['difficulty'].get('avg_score', 0)
        if standard_deviation_flag:
            total_score += test_case['difficulty'].get('standard_deviation_score', 0)
        return total_score

    # Use a set to store unique test cases (based on a unique field like 'input' or 'id')
    seen = set()
    unique_test_case_list = []
    
    for test_case in test_case_list:
        test_case_id = test_case.get('input')  # Assuming 'input' field is unique, you can change this if necessary
        if test_case_id not in seen:
            seen.add(test_case_id)
            unique_test_case_list.append(test_case)

    # Sort the unique test case list based on the total sum of scores
    sorted_test_case_list = sorted(unique_test_case_list, key=lambda x: score_sum(x))
    
    return sorted_test_case_list

    
      
def verify_and_exec_generator(code_list, logger, debug=False,check_number=3,filter_numerical=True,max_try_num=1000,test_case_num=30,test_case_max_len=500,test_case_max_number=1000.0,sandboxfusion_url=None,error_cnt_limit=100):
    _logger = logger
    success_problems = []
    left_problems = []

    cwd = Path.cwd()
    src_dir = (cwd / ".." / "testlib").resolve()
    bin_dir = (cwd / "testlib").resolve()
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    
    
    for example in tqdm(code_list, desc="Processing test cases", unit="problem", ncols=100, ascii=True):
        code, lang = extract_last_code_block(example['answer'])
        todo_flag = False
        code = fix_newlines_in_python_strings(import_needed_module_for_python(code)) 
        # print(code)
        if lang and lang == "python":
            try:
                #过滤获得cpp/py的correct_submissions
                cpp_py_solution_list = []
                for solution_item in example['correct_submissions']:
                    solution_code = solution_item['code']
                    solution_lang = solution_item['language']
                    if solution_lang == "cpp" or solution_lang == "python": 
                        cpp_py_solution_list.append({
                            "code":solution_code,
                            "language":solution_lang
                        })
                    if len(cpp_py_solution_list)>=check_number:
                        break
                    
                if len(cpp_py_solution_list) <= 1 :
                    # correct_submissions不够，不用加入todo
                    if logger and debug :logger.error("Not enough submission to check test case correctness.")
                    continue
                # 把correct_submissions 编译并且存好在规定位置,标程无需sandbox
                error_write_and_build_flag = False
                for idx,cpp_py_solution_item in enumerate(cpp_py_solution_list):
                    solution_code = cpp_py_solution_item['code']
                    lang = solution_item['language']
                    if lang == "cpp":
                        sol_code = src_dir / f"solution_{idx}.cpp"
                        sol_bin = bin_dir / f"sol_{idx}"
                    elif lang == "python":  # python
                        sol_code = bin_dir / f"sol_{idx}.py"
                        sol_bin = None
                        
                    success_flag = write_and_build_referenece_solution(
                        solution_code_str=solution_code,
                        lang=lang,
                        sol_code=sol_code,
                        sol_bin=sol_bin,
                        debug=debug,
                        logger=logger
                    )
                   
                    cpp_py_solution_item['sol_code']=sol_code
                    cpp_py_solution_item['sol_bin']=sol_bin
                        
                    if not success_flag:
                        error_write_and_build_flag = True
                        break
                    
                if error_write_and_build_flag:
                    # 如果本身的代码有问题，也不用加入todo
                    if logger and debug :logger.error("Error during write_and_build.")
                    continue
                
                
                error_cnt = 0 #最多允许连续error_cnt_limit次不生成任何一个合法数据
                
                #  执行generator获取input，并且
                # 1. 通过多组submission检验input的合法性  
                # 2. 检验是否是一个纯数字问题  
                # 3. 检测难度是否合格
                numerical_flag = True
                final_input_output_item_list = []
                bar = tqdm(range(max_try_num), dynamic_ncols=True)
                for _ in bar:
                    ok = len(final_input_output_item_list)
                    bar.set_description(f"Get {ok}/{test_case_num}")
                    bar.set_postfix(errors=error_cnt,  refresh=True)
                    
                    if error_cnt >= error_cnt_limit:
                        logger.error(f"Too many continuous errors exceed {error_cnt_limit}, skip this problem.")
                        # 连续错误过多，直接跳过，如果之前都没有正确样本在final_input_output_item_list中
                        # 那么直接加入todo,放置至后面重写geneartor
                        break
                    
                    if sandboxfusion_url is None:
                        # step1：执行generator获取数据
                        payload = run_generator_with_alarm(code, seconds=10,logger=logger)
                        if payload :
                            test_case_input = payload
                        else:
                            if logger and debug:
                                _logger.error(f"Error in exec generator in environment! {payload}")
                            error_cnt = error_cnt +1
                            continue
                    else:
                        sandbox_code = code+r'''
if __name__ == "__main__":
    print(generator())
'''
                        ret = sandboxfusion_run(sandboxfusion_url, sandbox_code,logger=logger,
                                                language='python',stdin="")
                        if ret["ok"]:
                            test_case_input = ret['run_result']["stdout"]
                        else:
                            if logger and debug:
                                _logger.error(f"Error in exec generator with SandboxFusion! {ret}")
                            error_cnt = error_cnt +1
                            continue
                    # step 1.5： 执行难度estimate函数，获取难度是否符合
                    
                    difficulty_dict = heuristic_estimate_function(
                        input_str=test_case_input,
                        max_len = test_case_max_len,
                        max_number= test_case_max_number,
                        max_number_bit=len(str(abs(test_case_max_number))),
                        logger=logger,
                        debug=debug
                    )
                    if not difficulty_dict:
                        if logger and debug: logger.error("Difficulty estimate function return None.")
                        error_cnt = error_cnt +1
                        continue
                    
                    # step2：跑多组solution，并获取每一组solution的输出
                    compare_to_check_list = []
                    error_flag = False
                    for cpp_py_solution_item in cpp_py_solution_list:
                        checked_list = run_reference_solution(inputs=[test_case_input],
                                            sol_code=cpp_py_solution_item['sol_code'],
                                            sol_bin = cpp_py_solution_item['sol_bin'],
                                            logger=logger,
                                            debug=debug,
                                            lang=cpp_py_solution_item['language'])
                        if checked_list[0]['flag']==False:
                            error_flag = True
                            break
                        compare_to_check_list.append(checked_list[0]) # {input:xxx,output:xxx,flag:ture/false}
                    
                    if error_flag:
                        error_cnt = error_cnt +1
                        continue
                    
                    # step3: 检查多组输入是否都一致
                    for k,checked_list in enumerate(compare_to_check_list[:-1]):
                        now_submission_output =  checked_list['output']
                        nxt_submission_output = compare_to_check_list[k+1]['output']
                        if str(now_submission_output).rstrip("\n") != str(nxt_submission_output).rstrip("\n"):
                            logger.error("Verifying and find two output not equal.")
                            error_flag = True
                            break
                            
                    if error_flag:
                        error_cnt = error_cnt +1
                        continue
                    
                    # step4: 如果生成的合法数据不是数值类型的，直接break
                    if filter_numerical and (not filter_only_numerical_problem([compare_to_check_list[0]])):
                        numerical_flag = False
                        final_input_output_item_list = []
                        break
                    
                    final_input_output_item_list.append({
                        "input":compare_to_check_list[0]['input'],
                        "output":compare_to_check_list[0]['output'],
                        "difficulty":difficulty_dict,
                    })
                    error_cnt = 0 # reset error cnt 
                       
                    if len(final_input_output_item_list)>= test_case_num:
                        break
                    
                if not numerical_flag:
                    #合法数据的输出不是数值类型，直接continue，也不用再加入todo了
                    logger.info("Not numerical problem,skip.")
                    continue
                
                
                if final_input_output_item_list:
                    todo_flag = True
                    test_case_list = sort_and_deduplicate_test_case_list(final_input_output_item_list)
                    success_problems.append({
                        **example,
                        "generator_code":code,
                        "test_case_list": test_case_list,
                        "test_case_len": len(test_case_list),
                    })
                else:
                    _logger.error("No test case passed the test.")
            except Exception as e:
                _logger.error(f"Error in loading Python Function Generator: {e}")
        else:
            _logger.error("No Python code.")
        
        if not todo_flag:
            left_problems.append(example)

    return success_problems, left_problems



def verify_json(examples, logger=None, debug=False):
    """
    检查每个 example['answer'] 是否是符合约定结构的 JSON 代码块。
    要求：
      - 有且只有一个 JSON code block（我们取最后一个）
      - code block 标记语言为 `json`
      - 能被 json.loads
      - 顶层是非空 dict
      - 每个字段的值是形如 {"min": int, "max": int} 的对象（int 且不是 bool）
    返回 (valid_examples, invalid_examples) 两个列表。
    """
    valid_examples = []
    invalid_examples = []

    for example in examples:
        ok = True

        # 1. 提取最后一个 code block
        try:
            code, lang = extract_last_code_block(example['answer'])
        except Exception as e:
            if logger and debug:
                logger.error(f"Failed to extract code block: {e}")
            invalid_examples.append(example)
            continue

        # 2. 必须是 json 代码块
        if lang != "json":
            if logger and debug:
                logger.error("Not json code block.")
            invalid_examples.append(example)
            continue

        # 3. 能否 parse 成 JSON
        try:
            obj = json.loads(code)
        except json.JSONDecodeError as e:
            if logger and debug:
                logger.error(f"JSON decode error: {e}")
            invalid_examples.append(example)
            continue

        # 4. 顶层必须是 dict，且非空
        if not isinstance(obj, dict):
            if logger and debug:
                logger.error("Top-level JSON is not an object.")
            invalid_examples.append(example)
            continue

        # if len(obj) == 0:
        #     if logger and debug:
        #         logger.error("Top-level JSON object is empty.")
        #     invalid_examples.append(example)
        #     continue

        # 5. 检查每个参数的结构
        for key, val in obj.items():
            if not isinstance(val, dict):
                ok = False
                if logger and debug:
                    logger.error(f"Value for key '{key}' is not an object.")
                break

            keys = set(val.keys())
            if keys != {"min", "max"}:
                ok = False
                if logger and debug:
                    logger.error(
                        f"Key '{key}' must have exactly 'min' and 'max', got {keys}."
                    )
                break

            for bound_name in ("min", "max"):
                v = val[bound_name]
                # int 且不是 bool（因为 bool 是 int 的子类）
                if not isinstance(v, int) or isinstance(v, bool):
                    ok = False
                    if logger and debug:
                        logger.error(
                            f"Value '{bound_name}' for key '{key}' "
                            f"must be an integer, got {type(v)}."
                        )
                    break
            if not ok:
                break

        if ok:
            # 如果你想顺手存一下解析结果，可以在这里加:
            example["parsed_json"] = code
            valid_examples.append(example)
        else:
            invalid_examples.append(example)

    return valid_examples, invalid_examples
import random
def random_get_json_object(json_obj_form,max_number = 10000,min_number = 1):
    if isinstance(json_obj_form,str):
        json_obj_form = json.loads(json_obj_form)
        
    example_json_obj = dict()
    for k,v in json_obj_form.items():
        v_min = int(v["min"])
        v_max = int(v["max"])
        v_true = max(min_number,min(max_number,random.randint(v_min,v_max)))
        example_json_obj[k] = v_true
    
    return example_json_obj
def verify_and_exec_generator_for_environment(examples, logger, debug=False,check_number=3,filter_numerical=True,test_times=100,sandboxfusion_url=None,error_cnt_limit=1):
    _logger = logger
    success_problems = []
    left_problems = []

    cwd = Path.cwd()
    src_dir = (cwd / ".." / "testlib").resolve()
    bin_dir = (cwd / "testlib").resolve()
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    
    
    for example in tqdm(examples, desc="Processing test cases", unit="problem", ncols=100, ascii=True):
        code, lang = extract_last_code_block(example['answer'])
        todo_flag = False
        numerical_flag = True
        code = fix_newlines_in_python_strings(import_needed_module_for_python(code)) 
        # print(code)
        if lang and lang == "python":
            try:
                #过滤获得cpp/py的correct_submissions
                cpp_py_solution_list = []
                for solution_code , solution_lang in zip(example['solutions']['solution'],example['solutions']['language']):
                    
                    if  solution_lang == 2: 
                        cpp_py_solution_list.append({
                            "code":solution_code,
                            "language":"cpp"
                        })
                    elif solution_lang == 3:
                        cpp_py_solution_list.append({
                            "code":solution_code,
                            "language":"python"
                        })
                    if len(cpp_py_solution_list)>=check_number:
                        break

                if len(cpp_py_solution_list) <= 1 :
                    # correct_submissions不够，不用加入todo
                    if logger and debug :logger.error("Not enough submission to check test case correctness.")
                    continue
                
                # 把correct_submissions 编译并且存好在规定位置,标程无需sandbox
                error_write_and_build_flag = False
                for idx,cpp_py_solution_item in enumerate(cpp_py_solution_list):
                    solution_code = cpp_py_solution_item['code']
                    lang = cpp_py_solution_item['language']
                    if lang == "cpp":
                        sol_code = src_dir / f"solution_{idx}.cpp"
                        sol_bin = bin_dir / f"sol_{idx}"
                    elif lang == "python":  # python
                        sol_code = bin_dir / f"sol_{idx}.py"
                        sol_bin = None
                        
                    success_flag = write_and_build_referenece_solution(
                        solution_code_str=solution_code,
                        lang=lang,
                        sol_code=sol_code,
                        sol_bin=sol_bin,
                        debug=debug,
                        logger=logger
                    )
                   
                    cpp_py_solution_item['sol_code']=sol_code
                    cpp_py_solution_item['sol_bin']=sol_bin
                        
                    if not success_flag:
                        error_write_and_build_flag = True
                        break
                    
                if error_write_and_build_flag:
                    # 如果本身的代码有问题，也不用加入todo
                    if logger and debug :logger.error("Error during write_and_build.")
                    continue
                
                error_cnt = 0 #最多允许连续error_cnt_limit次不生成任何一个合法数据
                
                #  执行generator获取input，并且
                # 1. 通过多组submission检验input的合法性  
                # 2. 检验是否是一个纯数字问题  
                bar = tqdm(range(test_times), dynamic_ncols=True)
                for _ in bar:
                    # bar.set_description(f"Get {ok}/{test_case_num}")
                    bar.set_postfix(errors=error_cnt,  refresh=True)
                    
                    if error_cnt >= error_cnt_limit:
                        logger.error(f"Too many continuous errors exceed {error_cnt_limit}, skip this problem.")
                        # 连续错误过多，直接跳过，如果之前都没有正确样本在final_input_output_item_list中
                        # 那么直接加入todo,放置至后面重写geneartor
                        break
                    
                    if sandboxfusion_url is None:
                        raise NotImplementedError
                    else:
                        test_obj = random_get_json_object(example['parsed_json'],min_number=100)
                        sandbox_code = code+f'''
if __name__ == "__main__":
    print(generate_testcase({test_obj}))
'''
                        ret = sandboxfusion_run(sandboxfusion_url, sandbox_code,logger=logger,
                                                language='python',stdin="")
                        if ret["ok"]:
                            test_case_input = ret['run_result']["stdout"]
                        else:
                            if logger and debug:
                                _logger.error(f"Error in exec generator with SandboxFusion! {ret}")
                            error_cnt = error_cnt +1
                            continue

                    # step2：跑多组solution，并获取每一组solution的输出
                    compare_to_check_list = []
                    error_flag = False
                    for cpp_py_solution_item in cpp_py_solution_list:
                        checked_list = run_reference_solution(inputs=[test_case_input],
                                            sol_code=cpp_py_solution_item['sol_code'],
                                            sol_bin = cpp_py_solution_item['sol_bin'],
                                            logger=logger,
                                            debug=debug,
                                            lang=cpp_py_solution_item['language'])
                        if checked_list[0]['flag']==False:
                            error_flag = True
                            break
                        compare_to_check_list.append(checked_list[0]) # {input:xxx,output:xxx,flag:ture/false}
                    
                    if error_flag:
                        error_cnt = error_cnt +1
                        continue
                    
                    # step3: 检查多组输入是否都一致
                    for k,checked_list in enumerate(compare_to_check_list[:-1]):
                        now_submission_output =  checked_list['output']
                        nxt_submission_output = compare_to_check_list[k+1]['output']
                        if str(now_submission_output).rstrip("\n") != str(nxt_submission_output).rstrip("\n"):
                            logger.error("Verifying and find two output not equal.")
                            error_flag = True
                            break
                            
                    if error_flag:
                        error_cnt = error_cnt +1
                        continue
                    
                    # step4: 如果生成的合法数据不是数值类型的，直接break
                    if filter_numerical and (not filter_only_numerical_problem([compare_to_check_list[0]])):
                        numerical_flag = False
                        break
                    
                       
                  
                if not numerical_flag:
                    #合法数据的输出不是数值类型，直接continue，也不用再加入todo了
                    logger.info("Not numerical problem,skip.")
                    continue
                
                
                if error_cnt == 0:
                    todo_flag = True
                else:
                    _logger.error("No test case passed the test.")
            except Exception as e:
                _logger.error(f"Error in loading Python Function Generator: {e}")
        else:
            _logger.error("No Python code.")
            
        if todo_flag:
            success_problems.append({
                **example,
                "generate_testcase":code
            })
        else:
            if numerical_flag:
                left_problems.append(example)

    return success_problems, left_problems

def filter_easy_hack_environment(examples, logger, debug=False,test_times=100,sandboxfusion_url=None,error_cnt_limit=1,different_output_limit=10,max_output_rate=0.3):
    _logger = logger
    success_problems = []
    left_problems = []
    

    cwd = Path.cwd()
    src_dir = (cwd / ".." / "testlib").resolve()
    bin_dir = (cwd / "testlib").resolve()
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    
    
    for example in tqdm(examples, desc="Processing test cases", unit="problem", ncols=100, ascii=True):
        code, lang = extract_last_code_block(example['answer'])
        todo_flag = False
        numerical_flag = True
        num_of_groups = 0
        max_group_size = 0
        code = fix_newlines_in_python_strings(import_needed_module_for_python(code)) 
        # print(code)
        if lang and lang == "python":
            try:
                #过滤获得cpp/py的correct_submissions
                cpp_py_solution_list = []
                for solution_code , solution_lang in zip(example['solutions']['solution'],example['solutions']['language']):
                    
                    if  solution_lang == 2: 
                        cpp_py_solution_list.append({
                            "code":solution_code,
                            "language":"cpp"
                        })
                    elif solution_lang == 3:
                        cpp_py_solution_list.append({
                            "code":solution_code,
                            "language":"python"
                        })
                    break


                # 把correct_submissions 编译并且存好在规定位置,标程无需sandbox
                error_write_and_build_flag = False
                for idx,cpp_py_solution_item in enumerate(cpp_py_solution_list):
                    solution_code = cpp_py_solution_item['code']
                    lang = cpp_py_solution_item['language']
                    if lang == "cpp":
                        sol_code = src_dir / f"solution_{idx}.cpp"
                        sol_bin = bin_dir / f"sol_{idx}"
                    elif lang == "python":  # python
                        sol_code = bin_dir / f"sol_{idx}.py"
                        sol_bin = None
                        
                    success_flag = write_and_build_referenece_solution(
                        solution_code_str=solution_code,
                        lang=lang,
                        sol_code=sol_code,
                        sol_bin=sol_bin,
                        debug=debug,
                        logger=logger
                    )
                   
                    cpp_py_solution_item['sol_code']=sol_code
                    cpp_py_solution_item['sol_bin']=sol_bin
                        
                    if not success_flag:
                        error_write_and_build_flag = True
                        break
                    
                if error_write_and_build_flag:
                    # 如果本身的代码有问题，也不用加入todo
                    if logger and debug :logger.error("Error during write_and_build.")
                    continue
                
                error_cnt = 0 #最多允许连续error_cnt_limit次不生成任何一个合法数据
                
                #  执行generator获取input，并且
                # 1. 通过多组submission检验input的合法性  
                # 2. 检验是否是一个纯数字问题  
                test_obj = random_get_json_object(example['parsed_json'])
                
                
                compare_to_check_list = []
                bar = tqdm(range(test_times), dynamic_ncols=True)
                for _ in bar:
                    # bar.set_description(f"Get {ok}/{test_case_num}")
                    bar.set_postfix(errors=error_cnt,  refresh=True)
                    
                    if error_cnt >= error_cnt_limit:
                        logger.error(f"Too many continuous errors exceed {error_cnt_limit}, skip this problem.")
                        # 连续错误过多，直接跳过，如果之前都没有正确样本在final_input_output_item_list中
                        # 那么直接加入todo,放置至后面重写geneartor
                        break
                    
                    sandbox_code = code+f'''
if __name__ == "__main__":
    print(generate_testcase({test_obj}))
'''
                    ret = sandboxfusion_run(sandboxfusion_url, sandbox_code,logger=logger,
                                                language='python',stdin="",time_limit=3)
                    if ret["ok"]:
                        test_case_input = ret['run_result']["stdout"]
                    else:
                        if logger and debug:
                            _logger.error(f"Error in exec generator with SandboxFusion! {ret}")
                        error_cnt = error_cnt +1
                        continue
                
                
                    error_flag = False
                    for cpp_py_solution_item in cpp_py_solution_list:
                        checked_list = run_reference_solution(inputs=[test_case_input],
                                            sol_code=cpp_py_solution_item['sol_code'],
                                            sol_bin = cpp_py_solution_item['sol_bin'],
                                            logger=logger,
                                            debug=debug,
                                            lang=cpp_py_solution_item['language'])
                        if checked_list[0]['flag']==False:
                            error_flag = True
                            break
                        compare_to_check_list.append(checked_list[0]) # {input:xxx,output:xxx,flag:ture/false}
                    
                    if error_flag:
                        error_cnt = error_cnt +1
                        continue
                    
                    
                if not numerical_flag:
                    #合法数据的输出不是数值类型，直接continue，也不用再加入todo了
                    logger.info("Not numerical problem,skip.")
                    continue
                
                output_count = defaultdict(int)

                # 统计每个output的个数
                for checked_list in compare_to_check_list:
                    output_count[str(checked_list['output']).rstrip("\n")] += 1

                # 计算族的数量
                num_of_groups = len(output_count)

                # 找到最大族的大小
                max_group_size = max(output_count.values())
                _logger.info(f"Num of Groups: {num_of_groups}, Max Group Size: {max_group_size}")
                if error_cnt == 0 and num_of_groups >= different_output_limit and max_group_size <= max_output_rate * test_times:
                    todo_flag = True
                else:
                    _logger.error("No test case passed the test.")
                    
            except Exception as e:
                _logger.error(f"Error in loading Python Function Generator: {e}")
        else:
            _logger.error("No Python code.")
            
        if todo_flag:
            success_problems.append({
                **example,
                "num_of_groups":num_of_groups,
                "max_group_siz":max_group_size
                })
        else:
            if numerical_flag:
                left_problems.append(example)

    return success_problems, left_problems

def find_max_difficulty(examples, logger, debug=False, sandboxfusion_url=None, max_prompt_length=2048):
    _logger = logger
    success_problems = []
    cwd = Path.cwd()
    src_dir = (cwd / ".." / "testlib").resolve()
    bin_dir = (cwd / "testlib").resolve()
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    for example in tqdm(examples, desc="Processing test cases", unit="problem", ncols=100, ascii=True):
        code, lang = extract_last_code_block(example['answer'])
        code = fix_newlines_in_python_strings(import_needed_module_for_python(code))
        todo_flag = True
        if lang and lang == "python":
            try:
                # 二分查找测试输入的最大长度
                low, high = 1, 10000  # 假设v_max范围为[1, 10000]
                true_low = low
                json_object = json.loads(example['parsed_json'])
                for k,v in json_object.items():
                    low = v['min']
                    high = v['max']
                while low <= high:
                    mid = (low + high) // 2
                    
                    # 直接将mid作为v_max代入
                    test_obj = {k: mid for k, v in json_object.items()}

                    sandbox_code = code + f'''
if __name__ == "__main__":
    print(generate_testcase({test_obj}, "dict" ))
'''
                    ret = sandboxfusion_run(sandboxfusion_url, sandbox_code, logger=logger,
                                             language='python', stdin="")
                    # print(ret)
                    if ret["ok"]:
                        test_case_input = ret['run_result']["stdout"]

                        # 如果输入的长度小于等于最大长度，尝试增大v_max
                        if len(test_case_input) <= max_prompt_length:
                            low = mid + 1
                        else:
                            # 否则减小v_max
                            high = mid - 1
                    else:
                        todo_flag = False
                        break
                    
                if todo_flag:
                    # 最终的最大v_max
                    final_vmax = high
                    logger.info(f"Max v_max found: {final_vmax}")
                    logger.info(test_case_input)
                    if final_vmax == true_low:
                        logger.error("MAX v_max == v_min,skip.")
                        continue
                    
                    new_json_object = {
                        k:{
                            "min":v['min'],
                            "max":max(v['min'],final_vmax),
                        }for k,v in json_object.items()
                    }
                    
                    example['parsed_json'] = str(new_json_object)
                    
                    success_problems.append(example)
            except Exception as e:
                _logger.error(f"Error in loading Python Function Generator: {e}")
        else:
            _logger.error("No Python code.")

    return success_problems

def generate_problem_detail_and_ground_truth(example,problem_scale,sandboxfusion_url,logger=None):
    problem_detail={}
    ground_truth = ""
    test_case_input=""
    code = fix_newlines_in_python_strings(import_needed_module_for_python(example['generate_testcase']))
    problem_detail_sandbox_code = code + f'''
if __name__ == "__main__":
    print(generate_testcase({problem_scale}, "dict" ))
'''
    ret = sandboxfusion_run(sandboxfusion_url, problem_detail_sandbox_code,logger=logger,
                                             language='python', stdin="")
    
    if ret["ok"]:
        problem_detail = ret['run_result']["stdout"]
        
    test_case_sandbox_code = code + f'''
if __name__ == "__main__":
    print(generate_testcase({problem_scale}))
'''
    ret = sandboxfusion_run(sandboxfusion_url, test_case_sandbox_code,logger=logger,
                                             language='python', stdin="")
    
    if ret["ok"]:
        test_case_input = ret['run_result']["stdout"]
    for solution_code,lang in zip(example['solutions']['solution'],example['solutions']['language']):
        if lang == 2:
            ret = sandboxfusion_run(sandboxfusion_url, solution_code, logger=logger,
                                    language='cpp', stdin=test_case_input)
        elif lang == 3:
            ret = sandboxfusion_run(sandboxfusion_url, solution_code,logger=logger,
                                    language='python', stdin=test_case_input)
        if ret['ok']:
            ground_truth = ret['run_result']["stdout"]
    return problem_detail,ground_truth
        
if __name__ == "__main__":
    logger = setup_logger()
    examples=  load_and_prepare_dataset("/inspire/hdd/global_user/xucaijun-253108120121/Code/FORGE",load_type="json",logger=logger,split="Train",file_glob="with_generator_after_filter.jsonl")
    
    success_problems, left_problems= verify_and_exec_generator_for_environment(examples=examples,logger=logger,debug=True,sandboxfusion_url="https://nat-notebook-inspire.sii.edu.cn/ws-6e6ba362-e98e-45b2-9c5a-311998e93d65/project-a75d443b-88d5-4461-859f-548caa0b38a7/user-ffe43f44-3d3b-44eb-8c68-ea76d13211e5/vscode/343f415d-2080-49db-8901-0d11ad76754c/da4db590-2d65-4162-9d58-7ddf81e88f36/proxy/8080/run_code")

    print(len(success_problems))
    print(len(left_problems))