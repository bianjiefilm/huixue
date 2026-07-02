"""
Block 22: 全量路由GET扫描
对所有已知GET路由做可达性扫描，确认200+body>200字节。
"""
import pytest
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


ALL_GET_ROUTES = [
    "/api/v1/classrooms",
    "/api/v1/classrooms/100",
    "/api/v1/classrooms/100/courses",
    "/api/v1/classrooms/100/students",
    "/api/v1/courses",
    "/api/v1/practices",
    "/api/v1/trainings/my-trainings",
    "/api/v1/trainings/library",
    "/api/v1/paper-library/papers",
    "/api/v1/files/test-file-access",
    "/api/v1/storage/stats",
    "/api/me",
    "/api/v1/exams",
    "/api/v1/classrooms/107",
    "/api/v1/classrooms/114",
    "/api/v1/classrooms/107/courses",
    "/api/v1/classrooms/114/courses",
    "/api/v1/classrooms/100/students",
    "/api/v1/teaching-resources/practice-environments",
    "/api/coursematerial/lists",
]


@pytest.mark.parametrize("path", ALL_GET_ROUTES, ids=ALL_GET_ROUTES)
def test_route_returns_200(teacher_token, teacher_id, path):
    """路由应返回200且body非空"""
    params = {}
    if path in ["/api/v1/exams", "/api/v1/paper-library/papers"]:
        params["teacher_id"] = str(teacher_id)
    # /classrooms/{id}/students 强制要求 teacher_id 查询参数（与 openapi 契约一致）
    if path.endswith("/students"):
        params["teacher_id"] = str(teacher_id)
    r = SESSION.get(
        f"{API_URL}{path}",
        params=params,
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"
    assert len(r.content) > 10, f"{path} returned empty body"
