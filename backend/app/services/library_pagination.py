"""项目实训库分页 + 合并 union 算法 (pure function, 无 db 依赖, 易测).

抽出原因 (Codex 审计 R3 收尾发现 2 P0):
- P0 #1: 老逻辑 trainings paginate 后 practices 全部追加 page=1, 跳过 practices[1+] 永久丢失
- P1 #5: practices 硬 prepend 不参与 sort, sort_order=asc 时违反排序合同

设计:
- 输入 list of dict (trainings + practices), 输出 paginated dict
- 所有副作用 (db query, filter, fetch creator) 留给 caller (endpoint)
- 100% pytest 单元测试可达
"""
from typing import List, Dict, Any, Optional


def merge_paginated_library(
    practices: List[Dict[str, Any]],
    trainings: List[Dict[str, Any]],
    page: int,
    page_size: int,
    sort_key: str = "created_at",
    sort_desc: bool = True,
) -> Dict[str, Any]:
    """合并 practices + trainings, 按 sort_key + sort_desc 全表排序后再分页.

    Args:
        practices: list of practice-as-training dict (含 id/title/created_at/source_type='practice'/...)
        trainings: list of training dict (含 id/title/created_at/source_type='training'/...)
        page: 页码 (1-based)
        page_size: 每页大小 (>= 1)
        sort_key: 排序字段名 (默认 created_at)
        sort_desc: True=降序 / False=升序

    Returns:
        {"list": [items_on_this_page], "total": int, "page": int, "page_size": int}

    Raises:
        ValueError: page < 1 / page_size < 1
        TypeError: 输入不是 list / dict
    """
    # 1) 输入校验
    if not isinstance(practices, list):
        raise TypeError(f"practices must be list, got {type(practices).__name__}")
    if not isinstance(trainings, list):
        raise TypeError(f"trainings must be list, got {type(trainings).__name__}")
    if not isinstance(page, int) or isinstance(page, bool):
        raise TypeError("page must be int")
    if not isinstance(page_size, int) or isinstance(page_size, bool):
        raise TypeError("page_size must be int")
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")

    # 2) 合并 + 标记 source_type (兜底 default 'training', 防 caller 漏传)
    combined = []
    for p in practices:
        if not isinstance(p, dict):
            raise TypeError(f"practice item must be dict, got {type(p).__name__}")
        item = dict(p)
        item.setdefault("source_type", "practice")
        combined.append(item)
    for t in trainings:
        if not isinstance(t, dict):
            raise TypeError(f"training item must be dict, got {type(t).__name__}")
        item = dict(t)
        item.setdefault("source_type", "training")
        combined.append(item)

    # 3) 排序 — 缺字段时用空串当 fallback (datetime/str 都可比), reverse=sort_desc
    def _sort_key(item):
        v = item.get(sort_key)
        if v is None:
            return ""
        return v
    combined.sort(key=_sort_key, reverse=sort_desc)

    # 4) 分页
    total = len(combined)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = combined[start:end]

    return {
        "list": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
