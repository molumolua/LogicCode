# -*- coding: utf-8 -*-
import os
import math
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


from api import batch_get_chat_api
from prompt import generator_cmd_prompt
from logger import setup_logger
from process_dataset import load_and_prepare_dataset,save_output_jsonl,prepare_examples
from after_extract import assemble_description
from extract import safe_format_template
import copy

def process_code_example_to_different_scale_problems(code_example):
    before_input=code_example['description_before_input']
    after_input=code_example['description_after_input']
    input_template = code_example['extract_number']['template']

    small_scale_decrease = code_example['extract_number']['small_scales']
    large_scale_increase = code_example['extract_number']['large_scales']
    default_scale=code_example['extract_number']['default_scale']
    scale_list = list(reversed(small_scale_decrease)) + [default_scale] +large_scale_increase

    generator_template = code_example["extract_generator"]["generator_code"]

    validator_tempalte = code_example["extract_validator"]["validator_code"]

    # group_gen_cmd = code_example["extract_generator_cmd"]["group_gen_cmd"]


    # assert len(scale_list) == len(group_gen_cmd)
    # print(len(group_gen_cmd))
    # print(group_gen_cmd[0])
    problems = []
    # accumlate_gen_cmd = []
    # accumlate_flag = True

    # print(validator_tempalte)
    # print(scale_list)
    for idx,scale in enumerate(scale_list):
    # for idx,(scale,gen_cmd) in enumerate(zip(scale_list,group_gen_cmd)):
        # if accumlate_flag:
        #     accumlate_gen_cmd.extend(gen_cmd['commands'])
        # if scale == default_scale:
        #     accumlate_flag = False
        try:    
            problem = {
                "source":code_example['source'],
                "id":code_example["id"]+"_{idx}".format(idx=idx),
                "title":code_example["title"],
                "description":assemble_description(before_input=before_input, input_section=safe_format_template(input_template,scale), after_input=after_input),
                "time_limit":code_example["time_limit"],
                "memory_limit":code_example["memory_limit"],
                "validator":safe_format_template(validator_tempalte,scale),
                "generator":safe_format_template(generator_template,scale),
                # "generator_cmd":copy.deepcopy(accumlate_gen_cmd),
                # "generator_time_limit_cmd":gen_cmd['commands'],
                "checker":code_example["checker"],
                "correct_submissions":code_example["correct_submissions"],
                "incorrect_submissions":code_example["incorrect_submissions"]
            }

            problems.append(problem)
        except Exception as e:
            print("Error in formatting problem id:",code_example["id"]," scale:",scale)
            print("Error message:",e)
            continue
    
    return problems


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="Batch prompting on local Parquet (CodeContests-like)")
    # 数据与加载
    parser.add_argument("--load_type",type=str,default="json",help="json or parquet")
    parser.add_argument("--load_dir", type=str,
                        default="../Dataset",
                        help="Directory containing local parquet shards")
    parser.add_argument("--split", type=str, default="train", choices=["train", "test", "valid", "validation"],
                        help="Which split to load (matched by filename prefix e.g., train-*.parquet)")
    parser.add_argument("--file_glob", type=str, default=None,
                        help="Optional custom glob, e.g. 'train-*.parquet'; if set, overrides --split matching")
    parser.add_argument("--drop_list", type=list, default=[],
                        help="Drop heavy columns if needed (e.g., 'private_test_cases')")
    parser.add_argument("--start_problem_idx", type=int, default=0,
                        help="Start index in the merged dataset")
    parser.add_argument("--max_rows", type=int, default=None,
                        help="Limit number of rows to load after start_problem_idx (None = all)")
    parser.add_argument("--save_dir", type=str, default="./save")
    # 推理与并行
    parser.add_argument("--model", type=str, default="gpt-5", help="Model name for batch_get_chat_api")
    parser.add_argument("--n_processes", type=int, default=16, help="Parallel processes for API calls")
    parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout (seconds)")
    parser.add_argument("--think", action="store_true", default=False, help="Enable think mode for API (if supported)")
    parser.add_argument("--extract_code", action="store_true", default=False, help="Whether to extract code from dataset")

    # 批次与重试
    parser.add_argument("--batch_size", type=int, default=256, help="Batch size per attempt")
    parser.add_argument("--max_attempts", type=int, default=3, help="Outer retry attempts over remaining problems")
    parser.add_argument("--inner_max_try", type=int, default=3, help="Inner retry count passed to batch_get_chat_api")

    args = parser.parse_args()

    logger = setup_logger()
    logger.info(f"Args: {vars(args)}")

    save_dir_path = Path(args.save_dir)
    save_dir_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output dir: {save_dir_path}")

    # 读取 parquet + 组装为带 "code" 的 examples
    dataset = load_and_prepare_dataset(
        load_type=args.load_type,
        load_dir=Path(args.load_dir),
        split=args.split,
        file_glob=args.file_glob,
        drop_list=args.drop_list,
        logger=logger
    )
    examples = prepare_examples(
        ds=dataset,
        start_idx=args.start_problem_idx,
        max_rows=args.max_rows,
        logger=logger,
        extract_code=args.extract_code)
    
    if not examples:
        logger.info("No examples with usable code. Exit.")
        return
    output_problems = []
    for code_example in examples:
        output_problems.extend(process_code_example_to_different_scale_problems(code_example))
    
    save_output_jsonl(output_problems,save_dir_path=save_dir_path,logger=logger)



if __name__ == "__main__":
    main()
