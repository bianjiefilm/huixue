"""
Block 10: 文件上传端到端
验证文件上传API可达性和基本错误处理。
注意：不上传真实文件到生产环境，仅验证端点存在且拒绝无效请求。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


UPLOAD_ENDPOINTS = [
    "/api/v1/files/upload/classroom-disk",
    "/api/v1/files/upload/training-dataset",
    "/api/v1/files/upload/homework-submission",
    "/api/v1/files/upload/teaching-resource",
]


def test_upload_endpoints_reject_empty(teacher_token):
    """上传端点应拒绝空请求（无文件）"""
    for path in UPLOAD_ENDPOINTS:
        r = SESSION.post(
            f"{API_URL}{path}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        # 应返回422（缺少文件）或400，不应500
        assert r.status_code != 500, f"{path} server error: {r.text[:200]}"
        assert r.status_code in [400, 422], f"{path} unexpected status {r.status_code}: {r.text[:200]}"


def test_upload_requires_auth():
    """上传端点无token应被拒绝"""
    for path in UPLOAD_ENDPOINTS:
        r = SESSION.post(f"{API_URL}{path}", timeout=TIMEOUT)
        assert r.status_code in [401, 403, 422], (
            f"{path} accessible without auth: {r.status_code}"
        )


def test_file_serve_test_endpoint(teacher_token):
    """文件服务测试端点应可达"""
    r = SESSION.get(
        f"{API_URL}/api/v1/files/test-file-access",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert "base_dir" in data, f"Unexpected response: {data}"


def test_file_upload_with_wrong_content_type(teacher_token):
    """上传时content-type不正确应被合理处理"""
    r = SESSION.post(
        f"{API_URL}/api/v1/files/upload/classroom-disk",
        headers={
            "Authorization": f"Bearer {teacher_token}",
            "Content-Type": "application/json",
        },
        json={"fake": "data"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Wrong content-type caused 500: {r.text[:200]}"
    assert r.status_code in [400, 422], f"Unexpected: {r.status_code}"


def test_storage_upload_rejects_empty(teacher_token):
    """对象存储上传端点应拒绝空请求"""
    r = SESSION.post(
        f"{API_URL}/api/v1/storage/upload",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 404, f"Storage route still broken (404): double prefix bug"
    assert r.status_code in [400, 422], f"Unexpected: {r.status_code} {r.text[:200]}"


def test_storage_stats(admin_token):
    """对象存储统计端点应可达"""
    r = SESSION.get(
        f"{API_URL}/api/v1/storage/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 404, f"Storage route still broken (404): double prefix bug"
    assert r.status_code == 200, f"Storage stats failed: {r.status_code} {r.text[:200]}"
