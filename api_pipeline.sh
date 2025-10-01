#!/usr/bin/env bash
set -euo pipefail

MAX_ROWS=200
LOAD_DIR=".\\Code-Contests-Plus\default_single"
LOAD_TYPE="parquet"
# MODEL="gpt-5-mini-2025-08-07"
MODEL="glm-4.5"
TEMPERATURE=0.6
FILE_GLOB="extracted_code.jsonl"
SAVE_DESCRIPTION_DIR=".\\Code-Contests-Plus\\extract_description"
SAVE_GENERATOR_DIR=".\\Code-Contests-Plus\\extract_generator"
SAVE_VALIDATOR_DIR=".\\Code-Contests-Plus\\extract_validator"
SAVE_GENERATOR_CMD_DIR=".\\Code-Contests-Plus\\extract_generator_cmd"
SAVE_FINAL_DIR=".\\Code-Contests-Plus\\different_scales"
N_PROCESSES=10
# python api_extract_description.py \
#     --max_rows ${MAX_ROWS} \
#     --load_type ${LOAD_TYPE} \
#     --load_dir ${LOAD_DIR} \
#     --model ${MODEL} \
#     --save_dir ${SAVE_DESCRIPTION_DIR} \
#     --temperature ${TEMPERATURE} \
#     --file_glob "part-*.parquet" \
#     --n_processes ${N_PROCESSES}





# python api_extract_validator.py \
#     --max_rows ${MAX_ROWS} \
#     --load_type "json" \
#     --load_dir ${SAVE_GENERATOR_DIR} \
#     --model ${MODEL} \
#     --save_dir ${SAVE_VALIDATOR_DIR} \
#     --temperature ${TEMPERATURE} \
#     --file_glob ${FILE_GLOB} \
#     --n_processes ${N_PROCESSES}

python api_get_generator_cmd.py \
    --max_rows ${MAX_ROWS} \
    --load_type "json" \
    --load_dir ${SAVE_VALIDATOR_DIR} \
    --model ${MODEL} \
    --save_dir ${SAVE_GENERATOR_CMD_DIR} \
    --temperature ${TEMPERATURE} \
    --file_glob ${FILE_GLOB} \
    --n_processes ${N_PROCESSES}



python generate_different_scale_problems.py \
    --max_rows ${MAX_ROWS} \
    --load_type "json" \
    --load_dir ${SAVE_GENERATOR_CMD_DIR} \
    --save_dir ${SAVE_FINAL_DIR} \
    --file_glob ${FILE_GLOB}


