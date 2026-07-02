"""
Block 17: CRUD闭环 — 实训管理
验证实训列表、详情、手册等API。
实训ID范围: 109-113+ (从course-management API获取)
"""
import pytest
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def _get_training_ids(token):
    """获取可用的实训ID列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/course-management/training-courses",
        params={"page": 1, "page_size": 20},
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT,
    )
    if r.status_code == 200:
        items = r.json().get("items", [])
        return [t["id"] for t in items]
    return []


def test_training_courses_list(admin_token):
    """���程管理中的实训列表应有数据"""
    r = SESSION.get(
        f"{API_URL}/api/v1/course-management/training-courses",
        params={"page": 1, "page_size": 20},
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    items = r.json().get("items", [])
    assert len(items) >= 5, f"Too few trainings: {len(items)}"


def test_training_library_detail(teacher_token):
    """实训库详情(library)应可访问"""
    ids = _get_training_ids(teacher_token)
    assert len(ids) > 0, "No training IDs found"
    tid = ids[0]
    r = SESSION.get(
        f"{API_URL}/api/v1/trainings/library/{tid}",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"
    assert data.get("data", {}).get("title"), f"No title: {str(data)[:200]}"


def test_training_handbook(teacher_token):
    """实训手册端点应可达；在前几个实训中至少有一个有内容（否则 skip）"""
    ids = _get_training_ids(teacher_token)
    assert len(ids) > 0, "No training IDs found"
    headers = {"Authorization": f"Bearer {teacher_token}"}
    last_len = 0
    for tid in ids[:5]:
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/{tid}/handbook",
            headers=headers,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"
        content = data.get("data", {}).get("content", "") or ""
        last_len = len(content)
        if last_len > 50:
            return
    pytest.skip(f"No training in top-5 has non-empty handbook (last len: {last_len})")


def test_all_trainings_accessible(teacher_token):
    """所有实训库详情都应可访问"""
    ids = _get_training_ids(teacher_token)
    assert len(ids) >= 5, f"Too few trainings: {len(ids)}"
    for tid in ids:
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/library/{tid}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, f"Training {tid} returned {r.status_code}"
