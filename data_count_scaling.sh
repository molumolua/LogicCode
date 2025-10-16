#!/usr/bin/env bash
set -euo pipefail

SANDBOX_URL="https://nat-notebook-inspire.sii.edu.cn/ws-6e6ba362-e98e-45b2-9c5a-311998e93d65/project-4493c9f7-2fbf-459a-ad90-749a5a420b91/user-ffe43f44-3d3b-44eb-8c68-ea76d13211e5/vscode/5036c53a-7e0f-4cb7-8546-d1481ce410ef/0bb00492-4106-40c2-abf1-64a8b368ade8/proxy/8080/run_code"
# Loading Args
MAX_ROWS=-1
LOAD_DIR="./Code-Contest-Plus/default_single"
LOAD_TYPE="parquet"

# API Args
# MODEL="gpt-5-mini-2025-08-07"
MODEL="glm-4.6"
TEMPERATURE=0.6
N_PROCESSES=16

# File Names
JSON_FILE_NAME="output_problems.jsonl"
META_NAME="output_problems_meta.json"
PARQUET_FILE_NAME="logic_problems.parquet"

# Generator Args
CHECK_NUMBER_FOR_TEST_CASE=3
MAX_NUMBER_IN_TEST_CASE=200
MAX_LEN_OF_TEST_CASE=1000

# Test Case Args
NUM_OF_TEST_CASE=10000
MAX_TRY_OF_TEST_CASE=50000
ERROR_CNT_LIMIT=100

# Verify group logic problem
CHECK_NUMBER_FOR_VERIFY_PROBLEMS=3

# Train args
MAX_TOKENS=2048
TRAIN_MODEL_PATH="/inspire/hdd/global_public/public_models/Qwen/Qwen2.5-7B"

# Scaling args
SIZE_LIST=(10 50 100 500 1000 2000)
# Paths
# 以json格式存储的代码问题
SAVE_TEST_CASE="./Code-Contest-Plus/with_generator_test_case"
SAVE_LOGIC_FUNCTION_DIR="./Code-Contest-Plus/with_logic_function_and_generator"

# 以parquet格式存储的逻辑问题
SAVE_LOGIC_PROBLEM_DIR="./Code-Contest-Plus/logic_problem"
SAVE_VERIFY_PROBLEM_DIR="./Code-Contest-Plus/logic_problem_verify"
SAVE_TRAIN_PROBLEM_DIR="./Code-Contest-Plus/train_logic_filter"

SAVE_VERIFY_LOGIC_FUNCTION_DIR="./Code-Contest-Plus/verified_with_logic_function_and_generator"
SAVE_SCALING_CODE_PROBLEM_DIR="./Code-Contest-Plus/scaling_code_problem"
SAVE_SCALING_LOGIC_PROBLEM_DIR="./Code-Contest-Plus/scaling_logic_problem"
SAVE_SCALING_TRAIN_PROBLEM_DIR="./Code-Contest-Plus/scaling_train_logic"

SAVE_DIFF_TRAIN_PROBLEM_DIR="./Code-Contest-Plus/scaling_diff_train_logic"

# python from_logic_find_mutiple_code.py \
#     --load_type "parquet" \
#     --load_dir ${SAVE_VERIFY_PROBLEM_DIR} \
#     --file_glob ${PARQUET_FILE_NAME} \
#     --code_load_type "json" \
#     --code_load_dir ${SAVE_LOGIC_FUNCTION_DIR} \
#     --code_file_glob ${JSON_FILE_NAME} \
#     --save_dir ${SAVE_VERIFY_LOGIC_FUNCTION_DIR} \
#     --save_name ${JSON_FILE_NAME} \
#     --save_meta_name ${META_NAME} \
#     --ref_load_type "json" \
#     --ref_load_dir ${SAVE_TEST_CASE} \
#     --ref_file_glob ${JSON_FILE_NAME} \
#     --use_ref

# python with_generator_to_mutiple_case.py \
#     --max_rows ${MAX_ROWS} \
#     --load_type "json" \
#     --load_dir ${SAVE_VERIFY_LOGIC_FUNCTION_DIR} \
#     --save_dir ${SAVE_SCALING_CODE_PROBLEM_DIR} \
#     --file_glob ${JSON_FILE_NAME} \
#     --save_name ${JSON_FILE_NAME} \
#     --save_meta_name ${META_NAME} \
#     --sandbox_url ${SANDBOX_URL} \
#     --filter_numerical \
#     --check_number ${CHECK_NUMBER_FOR_TEST_CASE} \
#     --max_number ${MAX_NUMBER_IN_TEST_CASE} \
#     --max_len ${MAX_LEN_OF_TEST_CASE} \
#     --num_of_test_case ${NUM_OF_TEST_CASE} \
#     --max_try_of_test_case ${MAX_TRY_OF_TEST_CASE} \
#     --sandbox_url ${SANDBOX_URL} \
#     --error_cnt_limit ${ERROR_CNT_LIMIT}


# python generate_group_logic_problem.py \
#     --max_rows ${MAX_ROWS} \
#     --load_type "json" \
#     --load_dir ${SAVE_SCALING_CODE_PROBLEM_DIR} \
#     --save_dir ${SAVE_SCALING_LOGIC_PROBLEM_DIR} \
#     --file_glob ${JSON_FILE_NAME} \
#     --save_name ${PARQUET_FILE_NAME} \
#     --save_meta_name ${META_NAME} \
#     --sandbox_url ${SANDBOX_URL}


# python process_train_data.py \
#     --max_rows -1 \
#     --max_tokens ${MAX_TOKENS} \
#     --train_model_path ${TRAIN_MODEL_PATH} \
#     --load_type "parquet" \
#     --load_dir ${SAVE_SCALING_LOGIC_PROBLEM_DIR} \
#     --save_dir ${SAVE_SCALING_TRAIN_PROBLEM_DIR} \
#     --file_glob ${PARQUET_FILE_NAME} \
#     --save_name ${PARQUET_FILE_NAME} \
#     --save_meta_name ${META_NAME} \
#     --example_level 2


python generate_different_scale_train_problems.py \
    --max_rows -1 \
    --load_type "parquet" \
    --load_dir ${SAVE_SCALING_TRAIN_PROBLEM_DIR} \
    --save_dir ${SAVE_DIFF_TRAIN_PROBLEM_DIR} \
    --file_glob ${PARQUET_FILE_NAME} \
    --size_list "${SIZE_LIST[@]}"





