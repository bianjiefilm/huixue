"""
Block 16: CRUD闭环 — 实践课程
验证教师能查看实践课程列表和详情。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_teacher_can_list_practices(teacher_token):
    """教师能看到实践课程列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/practices",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"
    items = data.get("data", {}).get("list", [])
    assert len(items) > 0, "No practices found"


def test_teacher_can_view_practice_detail(teacher_token):
    """教师能看到实践课程详情(id=100)"""
    r = SESSION.get(
        f"{API_URL}/api/v1/practices/100",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"


def test_practice_has_tasks(teacher_token):
    """实践课程应包含关卡任务"""
    r = SESSION.get(
        f"{API_URL}/api/v1/practices/100",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    practice = data.get("data", {})
    task_count = practice.get("task_count", 0)
    assert task_count > 0, f"Practice 100 has no tasks: {str(practice)[:200]}"


def test_student_can_view_practices(student_token):
    """学生也能看到实践课程列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/practices",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"
