
#!/usr/bin/env bash
set -euo pipefail

SANDBOX_URL="https://nat-notebook-inspire.sii.edu.cn/ws-6e6ba362-e98e-45b2-9c5a-311998e93d65/project-a75d443b-88d5-4461-859f-548caa0b38a7/user-ffe43f44-3d3b-44eb-8c68-ea76d13211e5/vscode/343f415d-2080-49db-8901-0d11ad76754c/da4db590-2d65-4162-9d58-7ddf81e88f36/proxy/8080/run_code"
# Loading Args
MAX_ROWS=-1
LOAD_DIR="/inspire/hdd/global_user/xucaijun-253108120121/Dataset/hf_datasets/code_contest"
LOAD_TYPE="parquet"
FILE_GLOB="train-*.parquet"
GENERATOR_FILE_GLOB="*_after_filter.jsonl"
# Save Args
SAVE_DIR="/inspire/hdd/global_user/xucaijun-253108120121/Code/FORGE"
FILTER_PROBLEM_SAVE_NAME="after_filter.jsonl"
FILTER_PROBLEM_META_NAME="after_filter.json"
GENERATOR_SAVE_NAME="2_with_generator_after_filter.jsonl"
GENERATOR_META_NAME="2_with_generator_after_filter.json"

HACK_SAVE_NAME="checked_hack.jsonl"
HACK_META_NAME="checked_hack.json"

TRAIN_SAVE_NAME="FORGE_train_data.parquet"
TRAIN_META_NAME="FORGE_train_data.json"
# API Args
# MODEL="gpt-5-mini-2025-08-07"
MODEL="glm-4.6"
TEMPERATURE=0.6
N_PROCESSES=20


# Verify group logic problem
CHECK_NUMBER_FOR_VERIFY_PROBLEMS=3
TEST_TIMES=100
ERROR_CNT_LIMIT=1 

# Train args
MAX_PROMPT_LENGTH=2048
TRAIN_MODEL_PATH="/inspire/hdd/global_public/public_models/Qwen/Qwen2.5-7B"
BATCH_SIZE=512

DIFFERENT_OUTPUT_LIMIT=10
MAX_OUTPUT_RATE=0.3

# python api_filter_problem_for_environment.py \
#  --load_type ${LOAD_TYPE} \
#  --load_dir ${LOAD_DIR} \
#  --file_glob ${FILE_GLOB} \
#  --max_rows ${MAX_ROWS} \
#  --save_dir ${SAVE_DIR} \
#  --save_name ${FILTER_PROBLEM_SAVE_NAME} \
#  --save_meta_name ${FILTER_PROBLEM_META_NAME} \
#  --model ${MODEL}\
#  --batch_szie ${BATCH_SIZE}


# python api_generate_generator_for_environment.py \
#  --load_type json \
#  --load_dir ${SAVE_DIR} \
#  --file_glob ${FILTER_PROBLEM_SAVE_NAME} \
#  --max_rows ${MAX_ROWS} \
#  --save_dir ${SAVE_DIR} \
#  --save_name ${GENERATOR_SAVE_NAME} \
#  --save_meta_name ${GENERATOR_META_NAME} \
#  --model ${MODEL}\
#  --check_number ${CHECK_NUMBER_FOR_VERIFY_PROBLEMS} \
#  --test_times ${TEST_TIMES} \
#  --sandbox_url ${SANDBOX_URL} \
#  --error_cnt_limit ${ERROR_CNT_LIMIT} \
#  --batch_size ${BATCH_SIZE} \
#  --filter_numerical \
#  --n_processes ${N_PROCESSES} \

# python filter_easy_hack_environment.py \
#  --load_type json \
#  --load_dir ${SAVE_DIR} \
#  --file_glob ${GENERATOR_FILE_GLOB} \
#  --max_rows ${MAX_ROWS} \
#  --save_dir ${SAVE_DIR} \
#  --save_name ${HACK_SAVE_NAME} \
#  --save_meta_name ${HACK_META_NAME} \
#  --model ${MODEL}\
#  --different_output_limit ${DIFFERENT_OUTPUT_LIMIT} \
#  --max_output_rate ${MAX_OUTPUT_RATE} \
#  --test_times ${TEST_TIMES} \
#  --sandbox_url ${SANDBOX_URL} \
#  --batch_size ${BATCH_SIZE} \
#  --n_processes ${N_PROCESSES}


 python set_max_difficulty_and_process_train_data.py \
 --load_type json \
 --load_dir ${SAVE_DIR} \
 --file_glob ${HACK_SAVE_NAME} \
 --max_rows ${MAX_ROWS} \
 --save_dir ${SAVE_DIR} \
 --save_name ${TRAIN_SAVE_NAME} \
 --save_meta_name ${TRAIN_META_NAME} \
 --model ${MODEL}\
 --max_prompt_length ${MAX_PROMPT_LENGTH} \
 --sandbox_url ${SANDBOX_URL} \
 --batch_size ${BATCH_SIZE} \
 --n_processes ${N_PROCESSES} 
 
