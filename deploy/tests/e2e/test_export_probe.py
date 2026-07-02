"""
Block 23: 导出端点探测
验证导出/下载类端点可达性或合理降级。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


EXPORT_ENDPOINTS = [
    "/api/v1/exams/export",
    "/api/v1/grades/export",
    "/api/v1/classrooms/export",
    "/api/v1/classrooms/100/export",
    "/api/v1/reports/export",
]


def test_export_endpoints_not_500(teacher_token, teacher_id):
    """导出端点应返回非500（404=未实现也可接受）"""
    for path in EXPORT_ENDPOINTS:
        params = {}
        if "exams" in path or "grades" in path:
            params["teacher_id"] = str(teacher_id)
        r = SESSION.get(
            f"{API_URL}{path}",
            params=params,
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code != 500, f"{path} returned 500: {r.text[:200]}"


def test_export_requires_auth():
    """导出端点无token应被拒绝或返回404"""
    for path in EXPORT_ENDPOINTS:
        r = SESSION.get(f"{API_URL}{path}", timeout=TIMEOUT)
        assert r.status_code in [401, 403, 404, 405, 422], (
            f"{path} accessible without auth: {r.status_code}"
        )


def test_download_nonexistent_file(teacher_token):
    """下载不存在的文件应404"""
    r = SESSION.get(
        f"{API_URL}/api/v1/storage/nonexistent/file.txt",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code in [404, 403], f"Expected 404, got {r.status_code}"
