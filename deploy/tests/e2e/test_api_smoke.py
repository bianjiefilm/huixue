"""
Block 8: API端点批量冒烟
核心API端点可达性验证。
"""
import pytest
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)


# (method, path, extra_params, expected_status)
ENDPOINTS = [
    ("GET", "/api/v1/classrooms", {}, [200]),
    ("GET", "/api/v1/courses", {}, [200]),
    ("GET", "/api/v1/exams", {"teacher_id": "{teacher_id}"}, [200]),
    ("GET", "/api/v1/practices", {}, [200]),
    ("GET", "/api/v1/paper-library/papers", {"teacher_id": "{teacher_id}"}, [200]),
    ("GET", "/api/v1/trainings/my-trainings", {}, [200]),
    ("GET", "/api/me", {}, [200]),
]


@pytest.mark.parametrize(
    "method,path,params,expected",
    ENDPOINTS,
    ids=[e[1] for e in ENDPOINTS],
)
def test_api_endpoint_reachable(teacher_token, teacher_id, method, path, params, expected):
    """核心API端点应返回正常状态码"""
    # 替换teacher_id占位符
    resolved = {k: (str(teacher_id) if v == "{teacher_id}" else v) for k, v in params.items()}
    r = SESSION.request(
        method,
        f"{API_URL}{path}",
        params=resolved,
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=20,
    )
    assert r.status_code in expected, (
        f"{method} {path} returned {r.status_code}: {r.text[:200]}"
    )


# 需要认证的端点
UNAUTHENTICATED_ENDPOINTS = [
    ("GET", "/api/v1/classrooms"),
    ("GET", "/api/v1/courses"),
    ("GET", "/api/v1/exams"),
    ("GET", "/api/me"),
]


@pytest.mark.parametrize("method,path", UNAUTHENTICATED_ENDPOINTS, ids=[e[1] for e in UNAUTHENTICATED_ENDPOINTS])
def test_api_requires_auth(method, path):
    """受保护端点无token应返回401/403"""
    r = SESSION.request(method, f"{API_URL}{path}", timeout=20)
    assert r.status_code in [401, 403, 422], (
        f"{method} {path} accessible without auth: {r.status_code}"
    )
