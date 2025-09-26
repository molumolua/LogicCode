from datasets import load_dataset
from typing import Any, Dict, List, Optional
from pathlib import Path
from extract import _extract_code_from_row
from datetime import datetime
import json


def _drop_heavy_columns(ds, drop_list: list, logger):
    # 根据需要删除超大列
    if not drop_list:
        return ds
    ds = ds.remove_columns(drop_list)
    logger.info(f"Dropped columns: {drop_list}")
    return ds


def _build_parquet_data_files(parquet_dir: Path, split=None, file_glob=None) -> List[str]:
    """根据 split 和通配符收集本地 parquet 分片。"""
    if file_glob:
        patterns = [file_glob]
    else:
        # 默认按 split 前缀收集：train-*.parquet / test-*.parquet / valid-*.parquet
        patterns = [f"{split}-*.parquet"]

    files: List[str] = []
    for pat in patterns:
        files.extend([str(p) for p in sorted(parquet_dir.glob(pat))])

    return files

def _build_jsonl_data_files(jsonl_dir: Path, split=None, file_glob=None) -> List[str]:
    """根据 split 和通配符收集本地 parquet 分片。"""
    if file_glob:
        patterns = [file_glob]
    else:
        # 默认按 split 前缀收集：train-*.jsonl / test-*.jsonl / valid-*.jsonl
        patterns = [f"{split}-*.jsonl"]

    files: List[str] = []
    for pat in patterns:
        files.extend([str(p) for p in sorted(jsonl_dir.glob(pat))])

    return files


def load_and_prepare_dataset(
    load_dir,
    load_type:str,
    logger,
    split=None,
    file_glob=None,
    drop_list=[]
) -> List[Dict[str, Any]]:
    """从本地读取 -> 删除大列 -> 抽取 code -> 转换为 examples(list)。"""
    if isinstance(load_dir,str):
        load_dir = Path(load_dir)
    if load_type=="json":
        data_files = _build_jsonl_data_files(load_dir, split, file_glob)
    elif load_type=="parquet":
        data_files = _build_parquet_data_files(load_dir, split, file_glob)
        
        
    if not data_files:
        raise FileNotFoundError(f"No {load_type} files matched in {load_dir} (split={split}, glob={file_glob or f'{split}*.{load_type}'})")

    logger.info(f"Loading {load_type} files ({len(data_files)} found). Example paths: {data_files[:3]}{' ...' if len(data_files) > 3 else ''}")
    ds = load_dataset(load_type, data_files=data_files, split="train")  # 合并为一个 split
    logger.info(f"Columns: {ds.column_names}")

    ds = _drop_heavy_columns(ds, drop_list=drop_list, logger=logger)
    
    return ds

def prepare_examples(ds,logger,start_idx=0,max_rows=None,extract_code=False):
    '''
    从 各种可能的字段中获取code，并且存在code字段中
    '''
    total = len(ds)
    if start_idx >= total:
        logger.warning(f"start_problem_idx ({start_idx}) >= dataset size ({total}); nothing to do.")
        return []

    # 决定要取多少条
    end_idx = total if max_rows is None else min(total, start_idx + max_rows)
    n_rows = end_idx - start_idx
    logger.info(f"Dataset size={total}, taking rows [{start_idx}:{end_idx}) -> {n_rows} rows")
    # 为了稳定、低内存：分块 to_list
    # 这里的块大小跟 batch_size 无关，只是读取阶段的切片大小
    CHUNK = 10_000
    examples: List[Dict[str, Any]] = []
    taken = 0
    for begin in range(start_idx, end_idx, CHUNK):
        end = min(begin + CHUNK, end_idx)
        rows = ds.select(range(begin, end)).to_list()

        for r in rows:
            ex = dict(r)
            if extract_code:
                code = _extract_code_from_row(r)
                if not code:
                    # 没拿到代码就跳过
                    continue
                ex["code"] = code  # 统一字段名，供 pre_fun 使用
            examples.append(ex)

        taken += len(rows)
        logger.info(f"Prepared examples: {len(examples)} / scanned rows: {taken}")

    if not examples:
        logger.warning("No example with usable code was found. Check column mapping / dataset schema.")

    return examples



def save_output_jsonl(output_problems: List[Dict[str, Any]], save_dir_path: Path, logger, save_name=None,meta_name=None):
    def _to_jsonable(o):
        if isinstance(o, (str, int, float, bool)) or o is None:
            return o
        if isinstance(o, dict):
            return {k: _to_jsonable(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_to_jsonable(x) for x in o]
        return str(o)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    if save_name:
        out_jsonl = save_dir_path / save_name
    else:
        out_jsonl = save_dir_path / f"output_problems.jsonl"

    if meta_name:
        out_meta = save_dir_path / meta_name
    else:
        out_meta = save_dir_path / f"meta.json"

    # Write output jsonl
    with out_jsonl.open("w", encoding="utf-8") as wf:
        for ex in output_problems:
            wf.write(json.dumps(_to_jsonable(ex), ensure_ascii=False) + "\n")

    # Prepare metadata
    meta = {
        "timestamp": ts,
        "total_completed": len(output_problems),
        "output_path": str(out_jsonl),
    }

    # Write meta data to meta.json
    with out_meta.open("w", encoding="utf-8") as mf:
        json.dump(meta, mf, ensure_ascii=False, indent=2)

    # Log the results
    logger.info(f"Saved outputs: {out_jsonl}  (rows={len(output_problems)})")
    logger.info(f"Saved meta:    {out_meta}")