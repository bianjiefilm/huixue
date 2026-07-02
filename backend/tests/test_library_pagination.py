"""单元测试 services/library_pagination.merge_paginated_library.

100% 覆盖率: 正常路径 + 边界 + 异常.

跑法 (本地):
    cd backend && python3 -m pytest tests/test_library_pagination.py -v
    cd backend && python3 -m pytest tests/test_library_pagination.py --cov=app.services.library_pagination --cov-report=term-missing
"""
import pytest
from app.services.library_pagination import merge_paginated_library


# ============================================================
# 工具: 构造测试 fixture
# ============================================================

def _p(id_, title, created_at, **extra):
    """构造 practice dict."""
    return {"id": id_, "title": title, "created_at": created_at, "source_type": "practice", **extra}

def _t(id_, title, created_at, **extra):
    """构造 training dict."""
    return {"id": id_, "title": title, "created_at": created_at, "source_type": "training", **extra}


# ============================================================
# 正常路径 (5 cases)
# ============================================================

def test_basic_2practices_3trainings_page1_size3():
    """2 practices + 3 trainings, page=1 size=3, sort_desc=True."""
    practices = [_p(1, "P1", "2026-04-28"), _p(2, "P2", "2026-04-26")]
    trainings = [_t(101, "T1", "2026-04-25"), _t(102, "T2", "2026-04-20"), _t(103, "T3", "2026-04-15")]
    r = merge_paginated_library(practices, trainings, page=1, page_size=3)
    assert r["total"] == 5
    assert r["page"] == 1
    assert r["page_size"] == 3
    assert len(r["list"]) == 3
    # 按 created_at desc: P1 (28) > P2 (26) > T1 (25)
    assert [x["id"] for x in r["list"]] == [1, 2, 101]


def test_basic_page2_takes_remainder():
    """page=2 取剩余."""
    practices = [_p(1, "P1", "2026-04-28")]
    trainings = [_t(101, "T1", "2026-04-25"), _t(102, "T2", "2026-04-20"), _t(103, "T3", "2026-04-15")]
    r = merge_paginated_library(practices, trainings, page=2, page_size=2)
    assert r["total"] == 4
    # full sorted desc: [P1, T1, T2, T3]; page 2 size 2 = [T2, T3]
    assert [x["id"] for x in r["list"]] == [102, 103]


def test_sort_asc():
    """sort_desc=False 升序."""
    practices = [_p(1, "P1", "2026-04-28")]
    trainings = [_t(101, "T1", "2026-04-25")]
    r = merge_paginated_library(practices, trainings, page=1, page_size=10, sort_desc=False)
    # asc: T1 (25) < P1 (28)
    assert [x["id"] for x in r["list"]] == [101, 1]


def test_only_practices():
    practices = [_p(1, "P1", "2026-04-28"), _p(2, "P2", "2026-04-26")]
    r = merge_paginated_library(practices, [], page=1, page_size=10)
    assert r["total"] == 2
    assert [x["id"] for x in r["list"]] == [1, 2]


def test_only_trainings():
    trainings = [_t(101, "T1", "2026-04-25"), _t(102, "T2", "2026-04-20")]
    r = merge_paginated_library([], trainings, page=1, page_size=10)
    assert r["total"] == 2
    assert [x["id"] for x in r["list"]] == [101, 102]


# ============================================================
# 边界条件 (8 cases)
# ============================================================

def test_empty_inputs():
    """两个 list 都空 → total=0, list=[]."""
    r = merge_paginated_library([], [], page=1, page_size=10)
    assert r == {"list": [], "total": 0, "page": 1, "page_size": 10}


def test_page_beyond_total():
    """page > 总页数, list 空."""
    practices = [_p(1, "P1", "2026-04-28")]
    r = merge_paginated_library(practices, [], page=99, page_size=10)
    assert r["list"] == []
    assert r["total"] == 1


def test_page_size_1_2practices_drops_none():
    """P0 #1 修复关键 case: page_size=1 + 2 practices, practices 都能拿到不丢."""
    practices = [_p(1, "P1", "2026-04-28"), _p(2, "P2", "2026-04-26")]
    trainings = [_t(101, "T1", "2026-04-25")]

    p1 = merge_paginated_library(practices, trainings, page=1, page_size=1)
    p2 = merge_paginated_library(practices, trainings, page=2, page_size=1)
    p3 = merge_paginated_library(practices, trainings, page=3, page_size=1)
    p4 = merge_paginated_library(practices, trainings, page=4, page_size=1)

    # full sorted desc: [P1, P2, T1]
    assert p1["list"] == [practices[0]]
    assert p2["list"] == [practices[1]]
    assert p3["list"] == [trainings[0]]
    assert p4["list"] == []  # 超出
    # total 全等
    assert all(r["total"] == 3 for r in [p1, p2, p3, p4])


def test_page_size_exact_total_returns_all():
    practices = [_p(1, "P1", "2026-04-28")]
    trainings = [_t(101, "T1", "2026-04-25"), _t(102, "T2", "2026-04-20")]
    r = merge_paginated_library(practices, trainings, page=1, page_size=3)
    assert len(r["list"]) == 3


def test_page_size_huge():
    """page_size 远大于 total."""
    practices = [_p(1, "P1", "2026-04-28")]
    r = merge_paginated_library(practices, [], page=1, page_size=10_000)
    assert r["total"] == 1
    assert len(r["list"]) == 1


def test_sort_key_with_none_value_falls_back_empty_string():
    """sort_key 字段缺失时, fallback 空串排序 (不 crash)."""
    practices = [{"id": 1, "title": "no_date_p", "source_type": "practice"}]  # 无 created_at
    trainings = [_t(101, "T1", "2026-04-25")]
    r = merge_paginated_library(practices, trainings, page=1, page_size=10)
    # T1 有 date "2026-04-25" > "" (P1) → desc: T1, P1
    assert [x["id"] for x in r["list"]] == [101, 1]


def test_source_type_default_when_missing():
    """caller 漏传 source_type, pure function 兜底."""
    practices = [{"id": 1, "title": "P1", "created_at": "2026-04-28"}]  # no source_type
    trainings = [{"id": 101, "title": "T1", "created_at": "2026-04-25"}]
    r = merge_paginated_library(practices, trainings, page=1, page_size=10)
    assert r["list"][0]["source_type"] == "practice"  # 兜底
    assert r["list"][1]["source_type"] == "training"


def test_input_immutability():
    """输入 list 不被原地修改."""
    practices = [_p(1, "P1", "2026-04-28")]
    trainings = [_t(101, "T1", "2026-04-25")]
    p_copy = [dict(x) for x in practices]
    t_copy = [dict(x) for x in trainings]
    merge_paginated_library(practices, trainings, page=1, page_size=10)
    assert practices == p_copy
    assert trainings == t_copy


# ============================================================
# 异常路径 (8 cases)
# ============================================================

def test_raises_on_practices_not_list():
    with pytest.raises(TypeError, match="practices must be list"):
        merge_paginated_library("not list", [], page=1, page_size=10)


def test_raises_on_trainings_not_list():
    with pytest.raises(TypeError, match="trainings must be list"):
        merge_paginated_library([], "not list", page=1, page_size=10)


def test_raises_on_page_zero():
    with pytest.raises(ValueError, match="page must be >= 1"):
        merge_paginated_library([], [], page=0, page_size=10)


def test_raises_on_page_negative():
    with pytest.raises(ValueError, match="page must be >= 1"):
        merge_paginated_library([], [], page=-1, page_size=10)


def test_raises_on_page_size_zero():
    with pytest.raises(ValueError, match="page_size must be >= 1"):
        merge_paginated_library([], [], page=1, page_size=0)


def test_raises_on_page_size_negative():
    with pytest.raises(ValueError, match="page_size must be >= 1"):
        merge_paginated_library([], [], page=1, page_size=-5)


def test_raises_on_page_not_int():
    with pytest.raises(TypeError, match="page must be int"):
        merge_paginated_library([], [], page="1", page_size=10)


def test_raises_on_page_size_not_int():
    with pytest.raises(TypeError, match="page_size must be int"):
        merge_paginated_library([], [], page=1, page_size=10.5)


def test_raises_on_page_bool():
    """bool 是 int 子类, 显式排除."""
    with pytest.raises(TypeError, match="page must be int"):
        merge_paginated_library([], [], page=True, page_size=10)


def test_raises_on_practice_item_not_dict():
    with pytest.raises(TypeError, match="practice item must be dict"):
        merge_paginated_library(["not dict"], [], page=1, page_size=10)


def test_raises_on_training_item_not_dict():
    with pytest.raises(TypeError, match="training item must be dict"):
        merge_paginated_library([], ["not dict"], page=1, page_size=10)


# ============================================================
# 排序合同 (P1 #5 修复 — 关键 case)
# ============================================================

def test_sort_asc_practices_not_pre_pended():
    """P1 #5 修复: sort_order=asc 时 practices 不再硬 prepend, 按 created_at asc 排."""
    practices = [_p(1, "P_NEW", "2026-04-28")]      # 新
    trainings = [_t(101, "T_OLD", "2026-04-01")]   # 老
    r = merge_paginated_library(practices, trainings, page=1, page_size=10, sort_desc=False)
    # asc: 老 T_OLD 应在前, P_NEW 在后
    assert [x["id"] for x in r["list"]] == [101, 1]


def test_sort_by_title_asc():
    """sort_key=title 按字典序升序."""
    practices = [_p(1, "Z_practice", "2026-04-28")]
    trainings = [_t(101, "A_training", "2026-04-25")]
    r = merge_paginated_library(practices, trainings, page=1, page_size=10, sort_key="title", sort_desc=False)
    # asc by title: A_training, Z_practice
    assert [x["id"] for x in r["list"]] == [101, 1]


def test_practices_drop_when_total_exceeds_page_size_and_sorted_lower():
    """P0 #1 关键 case 变体: practices 在 sort 后落到非 page 1, 也能正确拿到."""
    # 老 practice, 新 trainings
    practices = [_p(1, "OLD_P", "2026-04-01")]
    trainings = [_t(101, "T1", "2026-04-25"), _t(102, "T2", "2026-04-20"), _t(103, "T3", "2026-04-15")]
    # desc: T1, T2, T3, OLD_P
    p1 = merge_paginated_library(practices, trainings, page=1, page_size=2)
    p2 = merge_paginated_library(practices, trainings, page=2, page_size=2)
    assert [x["id"] for x in p1["list"]] == [101, 102]
    assert [x["id"] for x in p2["list"]] == [103, 1]  # OLD_P 在 page 2 末位
