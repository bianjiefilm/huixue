"""
Block 13: 学生完整学习链路
验证学生能完成：课堂列表→课堂详情→课程查看→实践查看→实训查看
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_student_can_view_classroom_detail(student_token):
    """学生能查看课堂详情"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/100",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"


def test_student_can_view_classroom_courses(student_token):
    """学生能看到课堂内的课程列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/100/courses",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"
    courses = data.get("data", {}).get("courses", [])
    assert len(courses) > 0, "Classroom 100 has no courses"


def test_student_can_view_classroom_students(student_token):
    """学生能看到课堂同学列表"""
    # 契约：/classrooms/{id}/students 需要 teacher_id 查询参数。
    # 学生以"同班同学"视角访问时，使用该课堂的 teacher_id（课堂 100 由 teacher1 id=4 持有）。
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/100/students",
        params={"teacher_id": 4},
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"


def test_student_can_view_practices(student_token):
    """学生能查看实践课程列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/practices",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"
    items = data.get("data", {}).get("list", [])
    assert len(items) > 0, "No practices available"


def test_student_can_view_trainings(student_token):
    """学生能查看实训列表"""
    r = SESSION.get(
        f"{API_URL}/api/v1/trainings/my-trainings",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Failed: {str(data)[:200]}"


def test_student_cannot_create_classroom(student_token):
    """学生不能创建课堂"""
    r = SESSION.post(
        f"{API_URL}/api/v1/classrooms",
        json={"name": "学生非法创建", "start_date": "2026-01-01", "end_date": "2026-02-01"},
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=30,
    )
    if r.status_code == 200:
        data = r.json()
        # 即使返回200，code不应该是成功
        assert data.get("code") not in ["0000"], (
            f"Student created classroom! {str(data)[:200]}"
        )
    # 否则401/403/422都可接受


def test_student_cannot_delete_classroom(student_token):
    """学生不能删除课堂"""
    r = SESSION.delete(
        f"{API_URL}/api/v1/classrooms/100",
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=30,
    )
    if r.status_code == 200:
        data = r.json()
        assert data.get("code") not in ["0000"], f"Student deleted classroom! {str(data)[:200]}"
