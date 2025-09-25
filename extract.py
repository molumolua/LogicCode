import re
from typing import Optional, Tuple
from typing import Any, Dict, List, Optional
# from process_dataset import load_and_prepare_dataset
from logger import setup_logger

CANDIDATE_CODE_KEYS = [
    "code", "program", "source_code", "final_code", "solution", "answer", "submission",
]

def _extract_code_from_row(row: Dict[str, Any]) -> Optional[str]:
    """尽量从一条样本中拿到可用的代码字符串，兼容多种字段结构。"""
    # 1) 直接可用的字符串字段
    for k in CANDIDATE_CODE_KEYS:
        v = row.get(k)
        if isinstance(v, str) and v.strip():
            return v

    # 2) solutions 可能是 list[str] 或 list[dict]
    v = row.get("solutions") or row.get("solution_set")
    if isinstance(v, list) and v:
        # 优先取第一个非空字符串
        for item in v:
            if isinstance(item, str) and item.strip():
                return item
            if isinstance(item, dict):
                # dict 场景再走一次候选键
                for k2 in CANDIDATE_CODE_KEYS + ["code_text", "content", "data"]:
                    vv = item.get(k2)
                    if isinstance(vv, str) and vv.strip():
                        return vv
    # 3) dict(list)
    if isinstance(v,dict) and v:
        for k in CANDIDATE_CODE_KEYS + ["code_text", "content", "data"]:
            vv = v.get(k)
            if isinstance(vv, str) and vv.strip():
                return vv
            if isinstance(vv,list) and vv:
                for item in vv:
                    if isinstance(item, str) and item.strip():
                        # code_contest
                        return item
    return None


def extract_last_code_block(answer: str) -> Tuple[Optional[str], Optional[str]]:
    """
    从文本中提取“最后一个”```fenced code block```。
    支持形如:
        ```python
        ...code...
        ```
        ``` cpp
        ...code...
        ```
        ```
        ...code...
        ```

    返回: (code:str|None, lang:str|None)，若未找到返回 (None, None)
    """
    if not answer:
        return None, None

    # 匹配：``` [可选空格][可选语言] 换行 代码 ```   —— 非贪婪捕获代码
    fence_pat = re.compile(
        r"```[ \t]*([A-Za-z0-9_+\-\.]*)[ \t]*\r?\n(.*?)```",
        re.DOTALL
    )

    matches = list(fence_pat.finditer(answer))
    if matches:
        m = matches[-1]  # 取最后一个
        lang = (m.group(1) or "").strip().lower() or None
        code = m.group(2).strip()
        return code, lang

    # 兜底：如果有开头的 ``` 但缺少收尾 ```，取到文本末尾
    open_pat = re.compile(
        r"```[ \t]*([A-Za-z0-9_+\-\.]*)[ \t]*\r?\n(.*)$",
        re.DOTALL
    )
    m = open_pat.search(answer)
    if m:
        lang = (m.group(1) or "").strip().lower() or None
        code = m.group(2).strip()
        return code, lang

    return None, None


# if __name__ == "__main__":
#     logger=setup_logger()
#     dataset = load_and_prepare_dataset("/inspire/hdd/global_user/xucaijun-253108120121/Dataset/hf_datasets/code_contest_upgrade_1",file_glob="output_problems.jsonl",logger=logger,load_type="json")
#     for item in dataset:
#         code = extract_last_code_block(item['answer'])
#         print(code)