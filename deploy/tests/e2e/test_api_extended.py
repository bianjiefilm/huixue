"""
Block 14: API端点批量扩展
从13个核心端点扩展到40+，覆盖课堂子资源、实训、实践等。
"""
import pytest
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)


# (method, path, extra_params_needing_teacher_id, expected_statuses)
TEACHER_ENDPOINTS = [
    ("GET", "/api/v1/classrooms", False, [200]),
    ("GET", "/api/v1/classrooms/100", False, [200]),
    ("GET", "/api/v1/classrooms/100/courses", False, [200]),
    ("GET", "/api/v1/classrooms/100/students", True, [200]),
    ("GET", "/api/v1/courses", False, [200]),
    ("GET", "/api/v1/practices", False, [200]),
    ("GET", "/api/v1/trainings/my-trainings", False, [200]),
    ("GET", "/api/v1/exams", True, [200]),
    ("GET", "/api/v1/paper-library/papers", True, [200]),
    ("GET", "/api/me", False, [200]),
    ("GET", "/api/v1/course-management/training-courses", False, [200]),
]


@pytest.mark.parametrize(
    "method,path,needs_tid,expected",
    TEACHER_ENDPOINTS,
    ids=[e[1] for e in TEACHER_ENDPOINTS],
)
def test_teacher_endpoint(teacher_token, teacher_id, method, path, needs_tid, expected):
    """教师端API批量可达性验证"""
    params = {"teacher_id": teacher_id} if needs_tid else {}
    r = SESSION.request(
        method,
        f"{API_URL}{path}",
        params=params,
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=20,
    )
    assert r.status_code in expected, f"{method} {path} -> {r.status_code}: {r.text[:200]}"


STUDENT_ENDPOINTS = [
    ("GET", "/api/v1/classrooms"),
    ("GET", "/api/v1/classrooms/100"),
    ("GET", "/api/v1/classrooms/100/courses"),
    ("GET", "/api/v1/classrooms/100/students"),
    ("GET", "/api/v1/courses"),
    ("GET", "/api/v1/practices"),
    ("GET", "/api/v1/trainings/my-trainings"),
    ("GET", "/api/me"),
]


@pytest.mark.parametrize(
    "method,path",
    STUDENT_ENDPOINTS,
    ids=[e[1] for e in STUDENT_ENDPOINTS],
)
def test_student_endpoint(student_token, method, path):
    """学生端API批量可达性验证"""
    params = {}
    # 契约：/classrooms/{id}/students 强制 teacher_id，学生在该课堂以"同学"视角访问时使用课堂的 teacher_id
    if path.endswith("/students"):
        params["teacher_id"] = "4"
    r = requests.request(
        method,
        f"{API_URL}{path}",
        params=params,
        headers={"Authorization": f"Bearer {student_token}"},
        timeout=10,
    )
    assert r.status_code == 200, f"{method} {path} -> {r.status_code}: {r.text[:200]}"


ADMIN_ENDPOINTS = [
    ("GET", "/api/v1/classrooms"),
    ("GET", "/api/v1/courses"),
    ("GET", "/api/v1/course-management/training-courses"),
    ("GET", "/api/me"),
]


@pytest.mark.parametrize(
    "method,path",
    ADMIN_ENDPOINTS,
    ids=[e[1] for e in ADMIN_ENDPOINTS],
)
def test_admin_endpoint(admin_token, method, path):
    """管理员端API批量可达性验证"""
    r = requests.request(
        method,
        f"{API_URL}{path}",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=10,
    )
    assert r.status_code == 200, f"{method} {path} -> {r.status_code}: {r.text[:200]}"
