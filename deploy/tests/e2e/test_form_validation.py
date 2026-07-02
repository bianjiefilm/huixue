"""
Block 12: 表单校验/空态/分页（防御性测试）
验证API对边界输入的处理。
"""
import requests
import pytest
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_classroom_create_missing_name(teacher_token):
    """创建课堂缺少name应返回错误"""
    r = SESSION.post(
        f"{API_URL}/api/v1/classrooms",
        json={"description": "测试"},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code in [400, 422], f"Missing name accepted: {r.status_code} {r.text[:200]}"


def test_classroom_create_empty_name(teacher_token):
    """创建课堂name为空字符串应返回错误"""
    r = SESSION.post(
        f"{API_URL}/api/v1/classrooms",
        json={"name": "", "start_date": "2026-01-01", "end_date": "2026-02-01"},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    # 空name应被拒绝
    if r.status_code == 200:
        data = r.json()
        assert data.get("code") not in [200, "0000"], f"Empty name classroom created: {data}"


def test_pagination_page_zero(teacher_token):
    """page=0应被合理处理（不500）"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"page": 0, "page_size": 10},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Page 0 caused server error: {r.text[:200]}"


def test_pagination_negative_page(teacher_token):
    """page=-1应被合理处理（不500）"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"page": -1, "page_size": 10},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Negative page caused server error: {r.text[:200]}"


def test_pagination_huge_page_size(teacher_token):
    """page_size=99999应被合理处理"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"page": 1, "page_size": 99999},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Huge page_size caused server error: {r.text[:200]}"


def test_empty_list_response(teacher_token):
    """搜索不存在的关键词应返回空列表（不500）"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"keyword": "不存在的课堂名称xyz123"},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Keyword search failed: {r.status_code}"
    data = r.json()
    items = data.get("data", {}).get("list", [])
    assert isinstance(items, list), f"Expected list, got: {type(items)}"


def test_special_characters_in_search(teacher_token):
    """特殊字符搜索应被安全处理"""
    for keyword in ["<script>alert(1)</script>", "'; DROP TABLE --", "%00null"]:
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms",
            params={"keyword": keyword},
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code != 500, f"Special char '{keyword}' caused 500: {r.text[:200]}"
