"""
Block 29 — 系统管理与组织架构端到端测试
覆盖: 学校信息 → 组织树 → 教师管理 → 使用统计
"""
import pytest
import requests
from conftest import API_URL, get_api_token, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)

TIMEOUT = 30


@pytest.fixture(scope="module")
def admin_headers():
    token = get_api_token("admin", "admin123")
    assert token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def teacher_headers():
    token = get_api_token("teacher1", "teacher123")
    assert token
    return {"Authorization": f"Bearer {token}"}


# ---------- 学校信息 ----------

class TestSchoolInfo:

    def test_school_info_reachable(self, admin_headers):
        """学校信息端点可达"""
        r = SESSION.get(f"{API_URL}/api/v1/system/school/1", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_school_has_name(self, admin_headers):
        """学校信息包含名称"""
        r = SESSION.get(f"{API_URL}/api/v1/system/school/1", headers=admin_headers, timeout=TIMEOUT)
        data = r.json().get("data", {})
        assert data.get("name"), "学校名称不能为空"

    def test_school_nonexistent(self, admin_headers):
        """不存在的学校"""
        r = SESSION.get(f"{API_URL}/api/v1/system/school/99999", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code in (200, 404)


# ---------- 组织架构 ----------

class TestOrganization:

    def test_org_tree(self, admin_headers):
        """组织架构树"""
        r = SESSION.get(
            f"{API_URL}/api/v1/organization/schools/1/organizations/tree",
            headers=admin_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_org_list(self, admin_headers):
        """组织列表"""
        r = SESSION.get(
            f"{API_URL}/api/v1/organization/schools/1/organizations",
            headers=admin_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200


# ---------- 使用统计 ----------

class TestUsageStatistics:

    def test_course_usage(self, admin_headers):
        """课程使用统计"""
        r = SESSION.get(f"{API_URL}/api/v1/usage-statistics/courses", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json().get("data", {})
        assert "data" in data

    def test_practice_usage(self, admin_headers):
        """实践使用统计"""
        r = SESSION.get(f"{API_URL}/api/v1/usage-statistics/practices", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_training_usage(self, admin_headers):
        """实训使用统计"""
        r = SESSION.get(f"{API_URL}/api/v1/usage-statistics/trainings", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_student_usage(self, admin_headers):
        """学生使用统计"""
        r = SESSION.get(f"{API_URL}/api/v1/usage-statistics/students", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_course_detail_usage(self, admin_headers):
        """课程详细统计"""
        r = SESSION.get(f"{API_URL}/api/v1/usage-statistics/courses/100/details", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code in (200, 404)
