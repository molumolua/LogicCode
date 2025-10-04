from process_dataset import load_and_prepare_dataset,prepare_examples
from extract import extract_last_code_block,parse_gen_script,parse_one_gen_script,get_function_code_from_str
from logger import setup_logger
import copy
from typing import Tuple, Optional, List, Dict, Any
import inspect
import json
from exec_and_verify import build_and_run_reference_solution
from tqdm import tqdm
import json

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
                    "generate_logic_problem":{
                        "raw_code":code,
                        "lang":lang,
                        "function":function_code
                    },
                    **example
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
                        "raw_input_list": json_input_list,
                        "test_case_list": correct_test_cases,
                        **example
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


if __name__ == "__main__":
    logger = setup_logger()
    dataset = load_and_prepare_dataset(load_dir="./save",load_type="json",logger=logger,file_glob="output_problems.jsonl")
    examples = prepare_examples(ds=dataset,logger=logger)

    # for example in examples:
    #     code,lang = extract_last_code_block(example['answer'])
    #     print(code)
    #     if lang and lang =="python":
    #         default_problem, small_problems, large_problems = build_problems_from_string(code)
    #         print(small_problems[0])

    success_problems,left_problems =verify_default_problem_and_extract_large_small_problems(examples,logger)
    print(len(success_problems))

