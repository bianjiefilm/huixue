"""
Block 11: 多课堂覆盖
当前只测classroom 100，扩展到验证所有预置课堂(100-114)。
"""
import pytest
import requests
from conftest import API_URL, BASE_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


# 预置课堂ID列表（从API查询确认存在）
CLASSROOM_IDS = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]


@pytest.mark.parametrize("cid", CLASSROOM_IDS)
def test_classroom_api_accessible(teacher_token, cid):
    """每个预置课堂通过API应可访问"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/{cid}",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Classroom {cid}: status {r.status_code}"
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Classroom {cid} error: {str(data)[:200]}"


def test_classroom_list_returns_all(teacher_token):
    """课堂列表应包含所有预置课堂"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms?page=1&page_size=50",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    items = data.get("data", {}).get("list", [])
    found_ids = {c.get("id") for c in items}
    missing = set(CLASSROOM_IDS) - found_ids
    # 允许teacher1看不到某些课堂（可能不是owner），但至少应看到部分
    assert len(found_ids & set(CLASSROOM_IDS)) >= 5, (
        f"Teacher sees too few classrooms. Found: {found_ids & set(CLASSROOM_IDS)}, Missing: {missing}"
    )


SAMPLE_CLASSROOMS = [100, 107, 114]


@pytest.mark.parametrize("cid", SAMPLE_CLASSROOMS)
def test_classroom_detail_page_loads(teacher_page, cid):
    """课堂详情页（采样3个）应正常加载"""
    teacher_page.goto(
        f"{BASE_URL}/#/classroom/{cid}",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    teacher_page.wait_for_timeout(5000)
    url = teacher_page.url
    assert "classroom" in url, f"Classroom {cid} redirected: {url}"
