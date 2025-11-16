# -*- coding: utf-8 -*-
import os
import math
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from api import batch_get_chat_api
from prompt import generate_generator_prompt
from logger import setup_logger
from process_dataset import load_and_prepare_dataset, save_output_parquet, prepare_examples,save_output_jsonl
from extract import extract_last_code_block, split_with_input_section, safe_format_template
from after_extract import verify_json,find_max_difficulty
import copy
from prompt import scale_param_extractor_prompt


import numpy as np

import numpy as np

def generate_difficulty_dict(vmin, vmax):
    # 计算区间大小
    range_size = vmax - vmin
    
    # 确定 difficulty 数量，至少保证 10 个 difficulty，但最多 100 个
    num_difficulties = min(100, range_size//5)
    difficulty_dict = {}

    # 对于较小范围，使用等差数列（确保没有两个相邻的 difficulty 是相同的）
    if range_size <= 30:
        step = range_size / num_difficulties
        for difficulty in range(num_difficulties):
            v = int(vmin + step * difficulty)
            while difficulty > 0 and difficulty_dict[difficulty - 1] == v:
                v += 1 
            difficulty_dict[difficulty] = v

    # 对于较大的范围，使用对数级别的增长，先慢后快
    elif range_size <= 100:
        step = range_size / num_difficulties
        for difficulty in range(num_difficulties):
            v = int(vmin + step * difficulty)
            # 确保不同的 difficulty 值之间有差异
            while difficulty > 0 and difficulty_dict[difficulty - 1] == v:
                v += 1
            difficulty_dict[difficulty] = v

    elif range_size <= 1000:
        # 使用反向对数增长方式，先慢后快
        step = range_size / np.log10(range_size)
        for difficulty in range(num_difficulties):
            v = int(vmin + step * np.log10(num_difficulties - difficulty))  # 使用反向对数
            # 确保不同的 difficulty 值之间有差异
            while difficulty > 0 and difficulty_dict[difficulty - 1] == v:
                v += 1
            difficulty_dict[difficulty] = v
    
    else:
        # 使用更强的反向对数增长方式
        for difficulty in range(num_difficulties):
            v = int(vmin + (range_size) * np.log10(num_difficulties - difficulty) / np.log10(num_difficulties))
            # 确保不同的 difficulty 值之间有差异
            while difficulty > 0 and difficulty_dict[difficulty - 1] == v:
                v += 1
            difficulty_dict[difficulty] = v
    
    return difficulty_dict


def main():
    parser = argparse.ArgumentParser(description="Batch prompting on local Parquet (CodeContests-like)")
    # Load args
    parser.add_argument("--load_type",type=str,default="json",help="json or parquet")
    parser.add_argument("--load_dir", type=str,
                        default="../Dataset",
                        help="Directory containing local parquet shards")
    parser.add_argument("--split", type=str, default="train", choices=["train", "test", "valid", "validation"],
                        help="Which split to load (matched by filename prefix e.g., train-*.parquet)")
    parser.add_argument("--file_glob", type=str, default=None,
                        help="Optional custom glob, e.g. 'train-*.parquet'; if set, overrides --split matching")
    parser.add_argument("--start_problem_idx", type=int, default=0,
                        help="Start index in the merged dataset")
    parser.add_argument("--max_rows", type=int, default=None,
                        help="Limit number of rows to load after start_problem_idx (None = all)")
    # Save args
    parser.add_argument("--save_dir", type=str, default="./save")
    parser.add_argument("--save_name",type=str,default="output_problems.jsonl")
    parser.add_argument("--save_meta_name",type=str,default="output_problems_meta.json")

    # 推理与并行
    parser.add_argument("--model", type=str, default="gpt-5", help="Model name for batch_get_chat_api")
    parser.add_argument("--n_processes", type=int, default=16, help="Parallel processes for API calls")
    parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout (seconds)")
    parser.add_argument("--think", action="store_true", default=False, help="Enable think mode for API (if supported)")
    
    parser.add_argument("--max_prompt_length", type=int, default=2048)
    parser.add_argument("--sandbox_url",type=str,default=None,help="The sandboxfusion url for code execution.")
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
        drop_list=[],
        logger=logger
    )
    
    examples = prepare_examples(
        ds=dataset,
        start_idx=args.start_problem_idx,
        max_rows=args.max_rows,
        logger=logger,
        extract_code=False)
    
    if not examples:
        logger.info("No examples with usable code. Exit.")
        return
    examples=find_max_difficulty(examples,logger,debug=True,sandboxfusion_url=args.sandbox_url,max_prompt_length=args.max_prompt_length)
    examples_processed = []
    for example in examples:
        print(example)
        vmin = -1
        vmax = -1
        example['parsed_json'] = example['parsed_json'].replace("'", '"')
        json_obj = json.loads(example['parsed_json'])   
        for k,v in json_obj.items():
            vmin = v["min"]
            vmax = v["max"]
            
        if vmin == -1 or vmax == -1:
            continue
        examples_processed.append({
            **example,
            "difficulty_dict":generate_difficulty_dict(vmin,vmax)
        })
    save_output_jsonl(examples_processed, save_dir_path=save_dir_path,  logger=logger, save_name=args.save_name, meta_name=args.save_meta_name)
if __name__ == "__main__":
    main()
