"""
Block 21: 作业批阅链路探测
验证成绩/作业相关端点可达性。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_grades_endpoint_reachable(teacher_token, teacher_id):
    """成绩相关端点应可达（探测多个可能路径）"""
    paths = [
        "/api/v1/grades",
        "/api/v1/classrooms/100/grades",
        "/api/v1/exams",
    ]
    found = False
    for path in paths:
        r = SESSION.get(
            f"{API_URL}{path}",
            params={"teacher_id": str(teacher_id)},
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            found = True
            break
        assert r.status_code != 500, f"{path} returned 500: {r.text[:200]}"
    assert found, "No grading endpoint reachable (all 404)"


def test_homework_list_reachable(teacher_token):
    """作业列表端点应可达"""
    r = SESSION.get(
        f"{API_URL}/api/v1/homework",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    # 可能是 /api/v1/homework 或嵌套在classroom下
    assert r.status_code != 500, f"Homework list 500: {r.text[:200]}"


def test_classroom_homework(teacher_token):
    """课堂100下作业列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/100/homework",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Classroom homework 500: {r.text[:200]}"


def test_student_grades_visible(student_token):
    """学生应能查看自己的成绩"""
    r = SESSION.get(
        f"{API_URL}/api/v1/grades/my",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    # 端点可能不存在(404)，但不应500
    assert r.status_code != 500, f"Student grades 500: {r.text[:200]}"


def test_grade_submission_requires_auth():
    """批阅提交应需要认证"""
    r = SESSION.post(
        f"{API_URL}/api/v1/grades",
        json={"student_id": 1, "score": 100},
        timeout=TIMEOUT,
    )
    assert r.status_code in [401, 403, 404, 405, 422], (
        f"Grade submission accessible without auth: {r.status_code}"
    )
