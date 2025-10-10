# -*- coding: utf-8 -*-
import os
import math
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional



from prompt import answer_problem_prompt,train_prompt
from logger import setup_logger
from process_dataset import load_and_prepare_dataset,prepare_examples,save_output_parquet
from extract import show_literal_newlines
from after_extract import verify_and_extract_test_case
import copy
from exec_and_verify import sandboxfusion_run
from tqdm import tqdm




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
    parser.add_argument("--save_name",type=str,default="output_problems.jsonl")
    parser.add_argument("--save_meta_name",type=str,default="output_problems_meta.json")

    parser.add_argument("--extract_code", action="store_true", default=False, help="Whether to extract code from dataset")
    parser.add_argument("--sandbox_url",type=str,default=None,help="The sandboxfusion url for code execution.")
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
    
    group_problem_list = []
    for example in tqdm(examples):
        generate_logic_problem_function = example['generate_logic_problem']['raw_code']
        group_problems = []
        
        if args.sandbox_url:
            for idx,test_case in enumerate(example['test_case_list']):
                try:
                    literal_input = show_literal_newlines(test_case['input'])
                    sandbox_generate_logic_problem_function = generate_logic_problem_function + f'''
if __name__ == "__main__":
    print(generate_logic_problem("{literal_input}"))
'''
                    # print(sandbox_generate_logic_problem_function)
                    ret = sandboxfusion_run(args.sandbox_url, sandbox_generate_logic_problem_function, logger=logger,
                                    language='python', stdin="")
                    
                    if ret["ok"]:
                        logic_problem = ret['run_result']["stdout"]
                    else:
                        logger.error(f"Error in sandboxfusion_run for test case {test_case},{ret}")
                        continue
                    
                    if logic_problem.startswith("None"):
                        logger.error("Error logic_problem is None.")
                    else:
                        group_problems.append({
                            "problem":logic_problem,
                            "reward_model":{
                                "ground_truth":f"\\boxed{{{test_case['output']}}}"
                            },
                            "source":f"logic_{example['source']}",
                            "id":f"{example['id']}_{idx}",
                            "raw_id":example['id'],
                            "title":f"{example['title']}_{idx}"
                        })
                        
                except Exception as e:
                    logger.error(f"Error in generate logic problem for test case {test_case},{e}") 
            
        else:
            try:
                exec(generate_logic_problem_function, globals()) 
            except Exception as e:
                logger.error(f"Error in exec generate_logic_problem function.{e}")
                continue
            for idx,test_case in enumerate(example['test_case_list']):
                try:
                    logic_problem = generate_logic_problem(test_case['input'])
                    if logic_problem:
                        group_problems.append({
                            "problem":logic_problem,
                            "reward_model":{
                                "ground_truth":f"\\boxed{{{test_case['output']}}}"
                            },
                            "source":f"logic_{example['source']}",
                            "id":f"{example['id']}_{idx}",
                            "raw_id":example['id'],
                            "title":f"{example['title']}_{idx}"
                        })
                except Exception as e:
                    logger.error(f"Error in generate logic problem for test case {test_case},{e}")
                
        if len(group_problems)>0:
            group_problem_list.append(group_problems)
            
    save_output_parquet(group_problem_list,save_dir_path,logger,args.save_name,args.save_meta_name)

if __name__ == "__main__":
    main()
