"""
Resource sync path E2E smoke tests.

Validates that resource scanning, listing, and sync-related endpoints
respond correctly — covering the diff_engine / parser code paths
that were rewired during TDD pure function extraction.
"""
import requests
import pytest
from conftest import API_URL, get_api_token, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


@pytest.fixture(scope="module")
def teacher_token():
    token = get_api_token("teacher1", "teacher123")
    if not token:
        pytest.skip("Cannot obtain teacher token")
    return token


@pytest.fixture(scope="module")
def auth_headers(teacher_token):
    return {"Authorization": f"Bearer {teacher_token}"}


class TestResourceScanEndpoints:
    """Test resource-import scan endpoints (exercises resource_scanner + sync code)."""

    def test_scan_trainings_returns_valid_response(self, auth_headers):
        resp = SESSION.post(
            f"{API_URL}/api/v1/resource-import/scan/trainings",
            headers=auth_headers, timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") in ("0000", "2000"), f"Unexpected code: {data}"
        if data["code"] == "0000":
            assert "data" in data
            assert "total" in data["data"]

    def test_scan_practices_returns_valid_response(self, auth_headers):
        resp = SESSION.post(
            f"{API_URL}/api/v1/resource-import/scan/practices",
            headers=auth_headers, params={"course_name": "__nonexistent__"},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        # May return 0000 (empty) or 2000 (no such course), both are valid
        assert data.get("code") in ("0000", "2000"), f"Unexpected code: {data}"

    def test_scan_trainings_responds_without_auth(self):
        """Scan endpoint should respond (may or may not enforce auth)."""
        resp = SESSION.post(
            f"{API_URL}/api/v1/resource-import/scan/trainings",
            timeout=10,
        )
        # Endpoint accepts the request — verify it doesn't crash
        assert resp.status_code in (200, 401, 403)


class TestResourceListEndpoints:
    """Test that listing endpoints return correct data shapes after rewire."""

    def test_courses_list_shape(self, auth_headers):
        resp = SESSION.get(
            f"{API_URL}/api/v1/courses",
            headers=auth_headers, timeout=15,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Response should be a list or paginated dict
        payload = data.get("data", data)
        assert isinstance(payload, (list, dict))

    def test_trainings_list_shape(self, auth_headers):
        resp = SESSION.get(
            f"{API_URL}/api/v1/trainings/my-trainings",
            headers=auth_headers, timeout=15,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == "0000"
        assert "data" in data


class TestHealthEndpoint:
    """Verify backend health after all rewiring deployments."""

    def test_health_returns_ok(self):
        resp = SESSION.get(f"{API_URL}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "健康"
        assert data.get("database") == "已连接"
        assert data.get("connection_test") == "通过"
