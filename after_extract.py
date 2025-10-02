from process_dataset import load_and_prepare_dataset,prepare_examples
from extract import extract_last_code_block,parse_gen_script,parse_one_gen_script,get_function_code_from_str
from logger import setup_logger
import copy
from typing import Tuple, Optional, List, Dict, Any
import inspect
import json
from exec_and_verify import *
def assemble_description(before_input, input_section, after_input):
    parts = []
    if before_input:
        parts.append(before_input.strip())
    if input_section:
        parts.append("Input:\n" + input_section.strip())
    if after_input:
        parts.append(after_input.strip())
    return "\n\n".join(parts)


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
    

def build_problems_from_string(
    code_str: str,
    logger
) -> Tuple[Optional[str], Optional[List[str]], Optional[List[str]]]:
    """
    传入：包含 template / default_scale / small_scales / large_scales 的 Python 源码字符串
    返回：default_problem, small_problems(list[str]), large_problems(list[str])
    若任一步出错：记录日志并返回 (None, None, None)
    """
    _logger = logger
    try:

        
        required_keys = ["template", "default_scale", "small_scales", "large_scales"]
        vars_dict = exec_and_return_values(code_str, required_keys, logger)
        if vars_dict is None:
            _logger.error("Failed to extract required variables from code.")
            return None, None, None, None, None, None, None
        template = vars_dict["template"]
        default_scale = vars_dict["default_scale"]
        small_scales = vars_dict["small_scales"]
        large_scales = vars_dict["large_scales"]


        if not isinstance(template, str):
            _logger.error("`template` must be str, got %r", type(template))
            return None, None, None, None, None, None, None
        if not isinstance(default_scale, dict):
            _logger.error("`default_scale` must be dict, got %r", type(default_scale))
            return None, None, None, None, None, None, None
        if not isinstance(small_scales, list) or not all(isinstance(x, dict) for x in small_scales):
            _logger.error("`small_scales` must be List[dict], got %r", small_scales)
            return None, None, None, None, None, None, None
        if not isinstance(large_scales, list) or not all(isinstance(x, dict) for x in large_scales):
            _logger.error("`large_scales` must be List[dict], got %r", large_scales)
            return None, None, None, None, None, None, None

        # 3) 干跑验证：确保 format 所需键齐全且可渲染
        try:
            _ = template.format(**default_scale)
        except Exception as e:
            _logger.exception("Failed to format template with default_scale: %s", e)
            return None, None, None, None, None, None, None

        for i, sc in enumerate(small_scales):
            try:
                _ = template.format(**sc)
            except Exception as e:
                _logger.exception("Failed to format template with small_scales[%d]: %s", i, e)
                return None, None, None, None, None, None, None

        for i, lc in enumerate(large_scales):
            try:
                _ = template.format(**lc)
            except Exception as e:
                _logger.exception("Failed to format template with large_scales[%d]: %s", i, e)
                return None, None, None, None, None, None, None

        # 4) 真正生成题面
        default_problem = template.format(**default_scale)
        small_problems = [template.format(**sc) for sc in small_scales]
        large_problems = [template.format(**lc) for lc in large_scales]

        return default_problem, small_problems, large_problems,template, default_scale, small_scales, large_scales

    except Exception as e:
        # 捕获所有其它异常，保证不抛出到调用方
        _logger.exception("build_problems_from_string failed: %s", e)
        return None, None, None, None, None, None, None
    

def verify_default_problem_and_extract_large_small_problems(default_problems,logger):
    left_problems=[]
    code_list=[]
    for example in default_problems:
        code,lang = extract_last_code_block(example['answer'])
        success_flag=False
        if lang and lang =="python":
            # print(code)
            # exit(1)
            default_problem, small_problems, large_problems,template, default_scale, small_scales, large_scales = build_problems_from_string(code,logger)
            if default_problem and small_problems and large_problems:
                code_list.append({
                    "extract_number":{
                        "code":code,
                        "lang":lang,
                        "template":template,
                        "default_scale":default_scale,
                        "small_scales":small_scales,
                        "large_scales":large_scales
                    },
                    **example
                })

                success_flag = True
                # default_example = copy.deepcopy(example)
                # default_example['description']=default_problem
                # success_problems.append(default_example)
                # for problem in small_problems:
                #     small_example = copy.deepcopy(example)
                #     small_example['description']=problem
                #     success_problems.append(small_example)

                # for problem in large_problems:
                #     large_example = copy.deepcopy(example)
                #     large_example['description']=problem
                #     success_problems.append(large_example)

                

        if not success_flag:
            left_problems.append(example)
        
    
    return None,left_problems, code_list


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
                        "lang":lang,
                        "function":function_code
                    },
                    **example
                })
                
        if not success_flag:
            left_problems.append(example)
    return success_problems,left_problems


def verify_and_extract_generator(code_list,logger):
    _logger = logger

    left_problems = []
    return_code_list = []
    for example in code_list:
        code,lang = extract_last_code_block(example['answer'])
        success_flag=False
        if lang and lang =="python":
            vars_dict=exec_and_return_values(code, ["generator_code"], logger)
            if vars_dict is None:
                _logger.error("Failed to extract required variables from code.")
            else:
                success_flag=True
                return_code_list.append({
                    "extract_generator":{
                        "code":vars_dict["generator_code"],
                        "lang":lang,
                        "generator_code":vars_dict["generator_code"]
                    },
                    **example
                })
        else:
            _logger.error("No python code.")


        if not success_flag:
            left_problems.append(example)

    return None,left_problems,return_code_list


def verify_and_extract_validator(code_list,logger):
    _logger = logger

    left_problems = []
    return_code_list = []
    for example in code_list:
        code,lang = extract_last_code_block(example['answer'])
        success_flag=False
        if lang and lang =="python":
            vars_dict=exec_and_return_values(code, ["validator_code"], logger)
            if vars_dict is None:
                _logger.error("Failed to extract required variables from code.")
            else:
                success_flag=True
                return_code_list.append({
                    "extract_validator":{
                        "code":vars_dict["validator_code"],
                        "lang":lang,
                        "validator_code":vars_dict["validator_code"]
                    },
                    **example
                })
        else:
            _logger.error("No python code.")


        if not success_flag:
            left_problems.append(example)

    return None,left_problems,return_code_list

def verify_and_extract_generator_cmd(code_list,logger):
    _logger = logger
    success_problems=[]
    left_problems = []
    return_code_list = []
    for example in code_list:
        code,lang = extract_last_code_block(example['answer'])
        if lang and lang =="bash":
            # print("ok! verify!")
            # print(code)
            group_gen_cmd = parse_gen_script(code)
            return_code_list.append({
                "extract_generator_cmd":
                {
                    "code":code,
                    "lang":lang,
                    "group_gen_cmd":group_gen_cmd
                },
                **example
            })
        else:
            _logger.error("No Bash code.")
            left_problems.append(example)

    return None,left_problems,return_code_list


def verify_and_extract_test_case(code_list,logger):
    _logger = logger
    success_problems=[]
    left_problems = []
    for example in code_list:
        code,lang = extract_last_code_block(example['answer'])
        if lang and lang =="json":
            try:
                # print(code)
                json_list = json.loads(code)
                
                success_problems.append({
                    "test_case_list":json_list,
                    **example
                })
            except Exception as e:
                _logger.error("Error in load json list.")
        else:
            _logger.error("No Bash code.")
            left_problems.append(example)

    return success_problems,left_problems


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

