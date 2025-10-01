# -*- coding: utf-8 -*-
import os
import math
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from tqdm import tqdm

from logger import setup_logger
from process_dataset import load_and_prepare_dataset,prepare_examples,save_output_parquet
import copy
import shlex
import subprocess
from pathlib import Path
from typing import List, Optional

def fix_newlines_in_cpp_strings(code: str) -> str:
    """
    将 C++ 源码中【双引号字符串内部】的真实换行符替换为字面量 '\\n'，
    以修复像 printf("%d %d\n", ...) 被错误写成 printf("%d %d
    ", ...) 的情况。
    仅处理双引号字符串，不动原本的 \\n、\\t、外部换行、注释等。
    """
    out = []
    in_str = False      # 是否在双引号字符串内部
    escaped = False     # 上一个字符是否是反斜杠（处理 \" \\ 等）
    i = 0
    while i < len(code):
        ch = code[i]

        if in_str:
            if escaped:
                # 前一个字符是反斜杠，当前字符原样放入（保持已有的转义如 \"、\\n）
                out.append(ch)
                escaped = False
            else:
                if ch == '\\':
                    out.append(ch)
                    escaped = True
                elif ch == '"':   # 结束字符串
                    out.append(ch)
                    in_str = False
                elif ch == '\r':  # 处理 \r\n 或单独 \r
                    # 丢弃 \r，自行判断下一位是否 \n
                    # 不把它输出到源码字符串里
                    if i + 1 < len(code) and code[i+1] == '\n':
                        # 将 CRLF 作为一个换行处理
                        out.append('\\n')
                        i += 1  # 跳过 \n
                    else:
                        out.append('\\n')
                elif ch == '\n':
                    # 这是不合法的：字符串内部的真实换行，替换为字面量 \n
                    out.append('\\n')
                else:
                    out.append(ch)
        else:
            if ch == '"':         # 进入字符串
                out.append(ch)
                in_str = True
                escaped = False
            else:
                out.append(ch)

        i += 1

    # 保证文件末尾有换行
    if not out or out[-1] != '\n':
        out.append('\n')
    return ''.join(out)

def generator_validator_pipeline(
    generator_str: str,
    validator_str: str,
    generator_cmd_str_list: List,
    logger=None,
    *,
    cpp_std: str = "c++17",
    compile_timeout_sec: int = 60,
    run_timeout_sec: int = 20,
) -> Optional[List[str]]:
    """
    Compile & run a testlib-based generator and validator, then collect valid inputs.
    On any compile error/timeout/missing binary, return None instead of raising.
    """

    # --- logger fallback ---
    class _NullLogger:
        def info(self, *a, **k): pass
        def warning(self, *a, **k): pass
        def error(self, *a, **k): pass
    logger = logger or _NullLogger()

    cwd = Path.cwd()

    # Where to WRITE source files (as requested): ../testlib
    src_dir = (cwd / ".." / "testlib").resolve()
    src_dir.mkdir(parents=True, exist_ok=True)

    # Where to PUT binaries (as requested): ./testlib
    bin_dir = (cwd / "testlib").resolve()
    bin_dir.mkdir(parents=True, exist_ok=True)

    gen_cpp = src_dir / "generator.cpp"
    val_cpp = src_dir / "validator.cpp"
    gen_bin = bin_dir / "gen"
    val_bin = bin_dir / "val"

    # --- Write sources (with minimal de-escaping) ---
    try:
        logger.info(f"Writing generator to {gen_cpp}")
        gen_src_fixed = fix_newlines_in_cpp_strings(generator_str)
        gen_cpp.write_text(gen_src_fixed, encoding="utf-8")

        logger.info(f"Writing validator to {val_cpp}")
        val_src_fixed = fix_newlines_in_cpp_strings(validator_str)
        val_cpp.write_text(val_src_fixed, encoding="utf-8")
    except Exception as e:
        logger.error(f"Writing sources failed: {e}")
        return None

    # --- Detect compiler ---
    cxx = os.environ.get("CXX", "g++")

    # Optional extra include dir if user set TESTLIB_INCLUDE
    extra_inc = os.environ.get("TESTLIB_INCLUDE")
    include_flags = ["-I", str(src_dir)]
    if extra_inc:
        include_flags += ["-I", extra_inc]

    common_flags = ["-std=" + cpp_std, "-O2", "-pipe", "-static-libstdc++", "-static-libgcc"]
    # If your environment can't link static, remove -static-* flags above.

    # Small helper
    def _compile_or_none(src: Path, out: Path, what: str) -> bool:
        logger.info(f"Compiling {what}...")
        try:
            res = subprocess.run(
                [cxx, str(src), "-o", str(out), *include_flags, *common_flags],
                check=False, timeout=compile_timeout_sec, capture_output=True
            )
        except subprocess.TimeoutExpired:
            logger.error(f"{what} compilation timed out after {compile_timeout_sec}s.")
            return False
        except Exception as e:
            logger.error(f"{what} compilation crashed: {e}")
            return False

        if res.returncode != 0:
            stderr = (res.stderr or b"").decode(errors="ignore")
            stdout = (res.stdout or b"").decode(errors="ignore")
            logger.error(f"{what} compilation failed (exit {res.returncode}).")
            if stdout.strip():
                logger.error(f"[{what} stdout]\n{stdout.strip()}")
            if stderr.strip():
                logger.error(f"[{what} stderr]\n{stderr.strip()}")
            return False

        if not out.exists():
            logger.error(f"{what} binary not found at {out}")
            return False

        logger.info(f"{what} compiled OK → {out}")
        return True

    # --- Compile generator & validator; return None on failure ---
    if not _compile_or_none(gen_cpp, gen_bin, "Generator"):
        return None
    if not _compile_or_none(val_cpp, val_bin, "Validator"):
        return None

    # --- Helper to normalize "./gen" path in commands ---
    def _normalize_cmd(cmd: str) -> List[str]:
        parts = shlex.split(cmd)
        if not parts:
            return parts
        head = parts[0]
        if head in ("./gen", "gen"):
            parts[0] = str(gen_bin)
        return parts

    passed_inputs: List[str] = []

    # --- Run pipeline for each command ---
    for idx, raw_cmd in enumerate(generator_cmd_str_list, 1):
        logger.info(f"[{idx}] Raw command: {raw_cmd}")
        cmd_parts = _normalize_cmd(raw_cmd)
        if not cmd_parts:
            logger.warning(f"[{idx}] Empty command, skipping.")
            continue
        if Path(cmd_parts[0]).name == "gen" and Path(cmd_parts[0]).parent == Path("."):
            cmd_parts[0] = str(gen_bin)

        logger.info(f"[{idx}] Running generator: {' '.join(cmd_parts)}")
        try:
            gen_proc = subprocess.run(
                cmd_parts,
                check=False,
                timeout=run_timeout_sec,
                capture_output=True,
                text=True
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"[{idx}] Generator timed out after {run_timeout_sec}s; skipping.")
            continue
        except FileNotFoundError:
            logger.error(f"[{idx}] Generator binary not found: {cmd_parts[0]}")
            continue
        except Exception as e:
            logger.error(f"[{idx}] Generator run crashed: {e}")
            continue

        gen_out = gen_proc.stdout if isinstance(gen_proc.stdout, str) else ""
        if gen_proc.returncode != 0:
            logger.warning(f"[{idx}] Generator exited with code {gen_proc.returncode}. Stderr:\n{gen_proc.stderr}")
            continue
        if not gen_out.strip():
            logger.warning(f"[{idx}] Generator produced empty output; skipping.")
            continue

        # Validate
        logger.info(f"[{idx}] Validating generator output with {val_bin}")
        try:
            val_proc = subprocess.run(
                [str(val_bin)],
                input=gen_out,
                text=True,
                check=False,
                timeout=run_timeout_sec,
                capture_output=True
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"[{idx}] Validator timed out after {run_timeout_sec}s; skipping.")
            continue
        except FileNotFoundError:
            logger.error(f"[{idx}] Validator binary missing: {val_bin}")
            continue
        except Exception as e:
            logger.error(f"[{idx}] Validator run crashed: {e}")
            continue

        if val_proc.returncode == 0:
            logger.info(f"[{idx}] ✅ Passed validation.")
            passed_inputs.append(gen_out)
        else:
            msg = (val_proc.stderr or "") + (("\n" + val_proc.stdout) if val_proc.stdout else "")
            logger.warning(f"[{idx}] ❌ Failed validation (exit {val_proc.returncode}). Message:\n{msg.strip()}")

    return passed_inputs

def _detect_solution_lang(code: str) -> str:
    """
    简单启发式：判断参考解是 C++ 还是 Python。
    返回 'cpp' 或 'python'。默认偏向 C++。
    """
    cxx_signals = ["#include", "int main(", "using namespace std", "std::", "cstdio", "iostream"]
    py_signals = ["def main", "print(", "import ", "sys.stdin", "input()", "from "]
    if any(s in code for s in cxx_signals):
        return "cpp"
    if any(s in code for s in py_signals) and "#include" not in code:
        return "python"
    # fallback：大多数平台参考解是 C++
    return "cpp"


def build_and_run_reference_solution(
    solution_code: str,
    inputs: List[str],
    logger=None,
    *,
    cpp_std: str = "c++17",
    compile_timeout_sec: int = 60,
    run_timeout_sec: int = 20,
) -> List[str]:
    """
    编译/准备参考解，并对每个 input 运行获得标准输出。
    支持 C++ (g++) 与 Python（系统 python）。
    返回 outputs（与 inputs 一一对应；若某个失败则放置空串）。
    """
    cwd = Path.cwd()
    src_dir = (cwd / ".." / "testlib").resolve()
    bin_dir = (cwd / "testlib").resolve()
    src_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    lang = _detect_solution_lang(solution_code)
    checked_outputs: List[str] = []
    checked_inputs:List[str] = []

    if lang == "cpp":
        sol_cpp = src_dir / "solution.cpp"
        sol_bin = bin_dir / "sol"
        # 处理字符串里的裸换行，避免 printf("...\n") 被拆断
        sol_cpp.write_text(fix_newlines_in_cpp_strings(solution_code), encoding="utf-8")

        cxx = os.environ.get("CXX", "g++")
        common_flags = ["-std=" + cpp_std, "-O2", "-pipe", "-static-libstdc++", "-static-libgcc"]

        if logger: logger.info("Compiling reference C++ solution...")
        try:
            subprocess.run(
                [cxx, str(sol_cpp), "-o", str(sol_bin), *common_flags],
                check=True, timeout=compile_timeout_sec, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            if logger:
                logger.error("Failed to compile reference solution.")
                logger.error(e.stderr.decode(errors="ignore"))
            # 编译失败，返回空 outputs（长度与 inputs 对齐）
            return [""] * len(inputs)
        except subprocess.TimeoutExpired:
            if logger: logger.error("Reference solution compilation timed out.")
            return [""] * len(inputs)

        for i, inp in enumerate(inputs, 1):
            try:
                proc = subprocess.run(
                    [str(sol_bin)],
                    input=inp,
                    text=True,
                    check=False,
                    timeout=run_timeout_sec,
                    capture_output=True
                )
            except subprocess.TimeoutExpired:
                if logger: logger.warning(f"[ref #{i}] Solution timed out.")
                continue
            except FileNotFoundError:
                if logger: logger.error("Reference binary missing unexpectedly.")
                continue

            if proc.returncode == 0:
                checked_inputs.append(inp)
                checked_outputs.append(proc.stdout)
            else:
                if logger:
                    logger.warning(f"[ref #{i}] Non-zero exit {proc.returncode}. stderr:\n{proc.stderr}")

    else:  # python
        sol_py = bin_dir / "sol.py"
        sol_py.write_text(solution_code, encoding="utf-8")
        python_exe = os.environ.get("PYTHON", "python")

        if logger: logger.info("Prepared reference Python solution.")
        for i, inp in enumerate(inputs, 1):
            try:
                proc = subprocess.run(
                    [python_exe, str(sol_py)],
                    input=inp,
                    text=True,
                    check=False,
                    timeout=run_timeout_sec,
                    capture_output=True
                )
            except subprocess.TimeoutExpired:
                if logger: logger.warning(f"[ref #{i}] Python solution timed out.")
                continue
            except FileNotFoundError:
                if logger: logger.error("Python interpreter not found.")
                continue

            if proc.returncode == 0:
                checked_inputs.append(inp)
                checked_outputs.append(proc.stdout)
            else:
                if logger:
                    logger.warning(f"[ref #{i}] Non-zero exit {proc.returncode}. stderr:\n{proc.stderr}")

    return checked_inputs,checked_outputs


def process_and_save_examples(batch_idx,examples, save_dir_path, logger):
    save_name = "examples_batch_{idx}.parquet".format(idx=batch_idx)  # Default save name for the first batch
    meta_name = "meta_batch_{idx}.json".format(idx=batch_idx)
    logger.info(f"Saving examples to {save_name}.")
    save_output_parquet(examples, save_dir_path=save_dir_path, logger=logger, save_name=save_name,meta_name=meta_name)
    examples.clear()  # Clear examples from memory after saving
    
def main():
    parser = argparse.ArgumentParser(description="Batch prompting on local Parquet (CodeContests-like)")
    # Parse arguments
    parser.add_argument("--load_type",type=str,default="json",help="json or parquet")
    parser.add_argument("--load_dir", type=str, default="../Dataset", help="Directory containing local parquet shards")
    parser.add_argument("--split", type=str, default="train", choices=["train", "test", "valid", "validation"], help="Which split to load (matched by filename prefix e.g., train-*.parquet)")
    parser.add_argument("--file_glob", type=str, default=None, help="Optional custom glob, e.g. 'train-*.parquet'; if set, overrides --split matching")
    parser.add_argument("--drop_list", type=list, default=[], help="Drop heavy columns if needed (e.g., 'private_test_cases')")
    parser.add_argument("--start_problem_idx", type=int, default=0, help="Start index in the merged dataset")
    parser.add_argument("--max_rows", type=int, default=None, help="Limit number of rows to load after start_problem_idx (None = all)")
    parser.add_argument("--save_dir", type=str, default="./save")
    # 推理与并行
    parser.add_argument("--model", type=str, default="gpt-5", help="Model name for batch_get_chat_api")
    parser.add_argument("--n_processes", type=int, default=16, help="Parallel processes for API calls")
    parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout (seconds)")
    parser.add_argument("--think", action="store_true", default=False, help="Enable think mode for API (if supported)")
    parser.add_argument("--extract_code", action="store_true", default=False, help="Whether to extract code from dataset")

    # 批次与重试
    parser.add_argument("--batch_size", type=int, default=128, help="Batch size for save.")
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
        extract_code=args.extract_code
    )

    if not examples:
        logger.info("No examples with usable code. Exit.")
        return

    enriched_examples = []  # ← 用于保存带 ground_truth 的样本
    batch_idx = 1  # Start with the first batch
    

    for example in tqdm(examples, desc="Processing examples", unit="example", ncols=100, ascii=True):
        generator_cmd = example["generator_cmd"]
        if isinstance(generator_cmd, dict):
            generator_cmd_str_list = generator_cmd['commands']
        elif isinstance(generator_cmd, List):
            generator_cmd_str_list = generator_cmd
        else:
            logger.error("No generator cmd found.")
        
        # 1) 运行 generator + validator 得到通过校验的 inputs
        passed_inputs = generator_validator_pipeline(
            generator_str=example['generator'],
            validator_str=example['validator'],
            generator_cmd_str_list=generator_cmd_str_list,
            logger=logger
        )

        if not passed_inputs:
            logger.info("No valid inputs generated for this example.")
            continue

        # 2) 运行参考解，得到标准 outputs
        ref_code = None
        try:
            for code in example['correct_submissions']:
                lang = _detect_solution_lang(code['code'])
                if lang:
                    ref_code = code['code']
                    break
        except Exception:
            logger.warning("No python/C++ correct_submissions found.")
            continue

        if ref_code:
            checked_inputs,checked_outputs = build_and_run_reference_solution(
                solution_code=ref_code,
                inputs=passed_inputs,
                logger=logger
            )
        else:
            logger.warning("No python/C++ correct_submissions found.")
            continue

        # 3) 组装 ground_truth 字段
        enriched_example = copy.deepcopy(example)
        enriched_example['ground_truth'] = {
            "inputs": checked_inputs,
            "outputs": checked_outputs,
            "checker": example['checker']
        }

        enriched_examples.append(enriched_example)

        # Check if examples array has reached the batch size and save it
        if len(enriched_examples) >= args.batch_size:
            logger.info(f"Saving batch {batch_idx}.")
            process_and_save_examples(batch_idx,enriched_examples, save_dir_path, logger)
            batch_idx += 1  # Increment the batch index
            

    # Save remaining examples if any
    if enriched_examples:
        logger.info(f"Saving batch {batch_idx}.")
        process_and_save_examples(batch_idx,enriched_examples, save_dir_path, logger)

if __name__ == "__main__":
    main()