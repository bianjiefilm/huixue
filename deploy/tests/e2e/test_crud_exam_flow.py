"""
Block 5: CRUD闭环 — 考试/成绩生命周期
验证考试查看和成绩查询API。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_teacher_can_list_exams(teacher_token, teacher_id):
    """教师能查看考试列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/exams",
        params={"teacher_id": teacher_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Unexpected response: {data}"


def test_teacher_can_view_paper_library(teacher_token, teacher_id):
    """教师能查看试卷库"""
    r = SESSION.get(
        f"{API_URL}/api/v1/paper-library/papers",
        params={"teacher_id": teacher_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Unexpected response: {data}"


def test_teacher_can_view_classroom_grades(teacher_token, teacher_id):
    """教师能查看课堂成绩（即使课堂不存在也应返回合理响应）"""
    r = SESSION.get(
        f"{API_URL}/api/v1/grades/classrooms/100/courses/100/grades",
        params={"teacher_id": teacher_id},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    # 200 with data, or 404 if classroom/course doesn't exist — both acceptable
    assert r.status_code in [200, 404], f"Server error: {r.status_code} {r.text[:200]}"


def test_student_can_view_classrooms(student_token):
    """学生能查看自己的课堂列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Unexpected response: {data}"


def test_teacher_can_list_trainings(teacher_token):
    """教师能查看实训列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/trainings/my-trainings",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Unexpected response: {data}"
