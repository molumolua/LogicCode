#!/usr/bin/env bash
set -euo pipefail

# Loading Args
MAX_ROWS=256
LOAD_DIR="./Code-Contest-Plus/default_single"
LOAD_TYPE="parquet"

# API Args
# MODEL="gpt-5-mini-2025-08-07"
MODEL="glm-4.5"
TEMPERATURE=0.6
N_PROCESSES=10

# File Names
FILE_NAME="output_problems.jsonl"
META_NAME="output_problems_meta.json"
FINAL_SAVE_NAME="logic_problems.parquet"

# Generator Args
CHECK_NUMBER_FOR_TEST_CASE=3
MAX_NUMBER_IN_TEST_CASE=100
MAX_LEN_OF_TEST_CASE=500

NUM_OF_TEST_CASE=100
MAX_TRY_OF_TEST_CASE=1000

# Verify group logic problem
CHECK_NUMBER_FOR_VERIFY_PROBLEMS=5

# Paths
SAVE_TEST_CASE="./Code-Contest-Plus/with_generator_test_case"
SAVE_LOGIC_FUNCTION_DIR="./Code-Contest-Plus/with_logic_function_and_generator"

SAVE_LOGIC_PROBLEM_DIR="./Code-Contest-Plus/logic_problem"
SAVE_VERIFY_PROBLEM_DIR="./Code-Contest-Plus/logic_problem_verify"
SAVE_TRAIN_PROBLEM_DIR="./Code-Contest-Plus/train_logic"



python api_generate_generator.py \
    --max_rows ${MAX_ROWS} \
    --load_type ${LOAD_TYPE} \
    --load_dir ${LOAD_DIR} \
    --model ${MODEL} \
    --save_dir ${SAVE_TEST_CASE} \
    --temperature ${TEMPERATURE} \
    --file_glob "part-*.parquet" \
    --n_processes ${N_PROCESSES} \
    --save_name ${FILE_NAME} \
    --save_meta_name ${META_NAME} \
    --filter_numerical \
    --check_number ${CHECK_NUMBER_FOR_TEST_CASE} \
    --max_number ${MAX_NUMBER_IN_TEST_CASE} \
    --max_len ${MAX_LEN_OF_TEST_CASE} \
    --num_of_test_case ${NUM_OF_TEST_CASE} \
    --max_try_of_test_case ${MAX_TRY_OF_TEST_CASE}


# python api_generate_logic_problem_function.py \
#     --max_rows ${MAX_ROWS} \
#     --load_type "json" \
#     --load_dir ${SAVE_TEST_CASE} \
#     --model ${MODEL} \
#     --save_dir ${SAVE_LOGIC_FUNCTION_DIR} \
#     --temperature ${TEMPERATURE} \
#     --file_glob ${FILE_NAME} \
#     --n_processes ${N_PROCESSES} \
#     --save_name ${FILE_NAME} \
#     --save_meta_name ${META_NAME}


# python generate_group_logic_problem.py \
#     --max_rows ${MAX_ROWS} \
#     --load_type "json" \
#     --load_dir ${SAVE_TEST_CASE} \
#     --save_dir ${SAVE_LOGIC_PROBLEM_DIR} \
#     --file_glob ${FILE_NAME} \
#     --save_name ${FINAL_SAVE_NAME} \
#     --save_meta_name ${META_NAME}

# python api_verify_group_logic_problem.py \
#     --model ${MODEL} \
#     --temperature ${TEMPERATURE} \
#     --max_rows ${MAX_ROWS} \
#     --load_type "parquet" \
#     --load_dir ${SAVE_LOGIC_PROBLEM_DIR} \
#     --save_dir ${SAVE_VERIFY_PROBLEM_DIR} \
#     --file_glob ${FINAL_SAVE_NAME} \
#     --save_name ${FINAL_SAVE_NAME} \
#     --save_meta_name ${META_NAME} \
#     --n_processes ${N_PROCESSES} \
#     --check_number  ${CHECK_NUMBER_FOR_VERIFY_PROBLEMS}

# python process_train_data.py \
#     --max_rows -1 \
#     --load_type "parquet" \
#     --load_dir ${SAVE_VERIFY_PROBLEM_DIR} \
#     --save_dir ${SAVE_TRAIN_PROBLEM_DIR} \
#     --file_glob ${FINAL_SAVE_NAME} \
#     --save_name ${FINAL_SAVE_NAME} \
#     --save_meta_name ${META_NAME}
