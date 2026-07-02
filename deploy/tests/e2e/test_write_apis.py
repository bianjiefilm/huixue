"""
Block 19: 写入API端点探测
验证POST/PUT/DELETE端点可达性，不实际写入数据，仅检查非404/500。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


WRITE_ENDPOINTS = [
    # (method, path, body)
    ("POST", "/api/v1/classrooms", {"name": "__probe__", "description": "probe"}),
    ("POST", "/api/v1/courses", {"name": "__probe__"}),
    ("POST", "/api/v1/exams", {"name": "__probe__"}),
    ("POST", "/api/v1/practices", {"name": "__probe__"}),
    ("POST", "/api/v1/files/upload/classroom-disk", None),
    ("POST", "/api/v1/files/upload/homework-submission", None),
    ("POST", "/api/v1/files/upload/teaching-resource", None),
]


def test_write_endpoints_reachable(teacher_token):
    """写入端点应可达（非404），允许400/422/403"""
    for method, path, body in WRITE_ENDPOINTS:
        kwargs = {"timeout": 10, "headers": {"Authorization": f"Bearer {teacher_token}"}}
        if body:
            kwargs["json"] = body
        r = SESSION.request(method, f"{API_URL}{path}", **kwargs)
        assert r.status_code != 404, f"{method} {path} returned 404"
        assert r.status_code != 500, f"{method} {path} returned 500: {r.text[:200]}"


def test_write_without_auth_blocked():
    """写入端点无token应被拒绝"""
    endpoints = [
        ("POST", "/api/v1/classrooms", {"name": "x"}),
        ("POST", "/api/v1/courses", {"name": "x"}),
        ("POST", "/api/v1/exams", {"name": "x"}),
    ]
    for method, path, body in endpoints:
        r = SESSION.request(method, f"{API_URL}{path}", json=body, timeout=TIMEOUT)
        assert r.status_code in [401, 403, 405, 422], (
            f"{method} {path} accessible without auth: {r.status_code}"
        )


def test_delete_nonexistent_returns_not_500(teacher_token):
    """DELETE不存在的资源应返回404或合理错误，不应500"""
    paths = [
        "/api/v1/classrooms/999999",
        "/api/v1/courses/999999",
        "/api/v1/exams/999999",
    ]
    for path in paths:
        r = SESSION.delete(
            f"{API_URL}{path}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code != 500, f"DELETE {path} returned 500: {r.text[:200]}"


def test_put_nonexistent_returns_not_500(teacher_token):
    """PUT不存在的资源应返回404或合理错误，不应500"""
    paths = [
        ("/api/v1/classrooms/999999", {"name": "updated"}),
        ("/api/v1/courses/999999", {"name": "updated"}),
    ]
    for path, body in paths:
        r = SESSION.put(
            f"{API_URL}{path}",
            json=body,
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code != 500, f"PUT {path} returned 500: {r.text[:200]}"
