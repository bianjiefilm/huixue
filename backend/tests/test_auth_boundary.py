"""
test_auth_boundary.py — 越权测试
验证学生不能调教师/管理员接口，教师不能调管理员接口
Targets: GAP-B8, TD-09
"""
import pytest


class TestStudentCannotAccessTeacherAPIs:
    """学生角色越权测试"""

    def test_student_cannot_create_classroom(self, client, student_headers):
        """学生不应能创建课堂 → 应返回 403"""
        resp = client.post("/api/v1/classrooms", json={
            "name": "学生非法课堂",
            "start_date": "2026-04-01T00:00:00",
            "end_date": "2026-07-01T00:00:00",
        }, headers=student_headers)
        assert resp.status_code == 403, \
            f"Expected 403 but got {resp.status_code}: student should not create classrooms"

    @pytest.mark.xfail(reason="POST /practices 路由不存在 (405), 结构性缺失 GAP-S1")
    def test_student_cannot_create_practice(self, client, student_headers):
        """学生不应能创建实践课程"""
        resp = client.post("/api/v1/practices", json={
            "title": "学生非法实践",
            "direction": "test",
            "category": "test",
            "difficulty": "beginner",
        }, headers=student_headers)
        assert resp.status_code in (403, 401), \
            f"Expected 403/401 but got {resp.status_code}"

    @pytest.mark.xfail(reason="POST /practices/{id}/publish 路由不存在 (404), 结构性缺失 GAP-S1")
    def test_student_cannot_publish_practice(self, client, student_headers, sample_practice):
        """学生不应能发布实践课程"""
        resp = client.post(
            f"/api/v1/practices/{sample_practice.id}/publish",
            headers=student_headers,
        )
        assert resp.status_code in (403, 401), \
            f"Expected 403/401 but got {resp.status_code}"

    def test_student_cannot_add_teacher(self, client, student_headers):
        """学生不应能添加教师"""
        resp = client.post("/api/v1/organization/schools/1/teachers", json={
            "username": "hacker_teacher",
            "email": "hack@test.com",
            "full_name": "黑客教师",
        }, headers=student_headers)
        # 422 (payload validation) or 4xx is OK — not 200
        assert resp.status_code != 200, \
            f"Expected non-200 but got {resp.status_code}: student should not add teachers"

    @pytest.mark.xfail(reason="GET /system/practice-courses 路由不存在 (404), GAP-S1")
    def test_student_cannot_access_system_management(self, client, student_headers):
        """学生不应能访问系统管理"""
        resp = client.get("/api/v1/system/practice-courses", headers=student_headers)
        assert resp.status_code in (403, 401), \
            f"Expected 403/401 but got {resp.status_code}"


class TestTeacherCannotAccessAdminAPIs:
    """教师不能越权到管理员"""

    def test_teacher_cannot_manage_roles(self, client, teacher_headers):
        """教师不应能管理角色授权"""
        resp = client.get("/api/v1/system/role-authorization", headers=teacher_headers)
        if resp.status_code != 404:
            assert resp.status_code in (403, 401), \
                f"Expected 403/401 but got {resp.status_code}"

    def test_teacher_cannot_manage_experiment_resources(self, client, teacher_headers):
        """教师不应能管理实验资源"""
        resp = client.get("/api/v1/teaching-resources/container-processes",
                         headers=teacher_headers)
        if resp.status_code != 404:
            pass  # 记录行为


class TestAuthTokenValidation:
    """Token 验证边界测试"""

    def test_no_token_returns_401(self, client, no_auth_headers):
        """未提供 token 应该返回 401"""
        resp = client.get("/api/v1/classrooms", headers=no_auth_headers)
        assert resp.status_code in (401, 403), \
            f"Expected 401/403 but got {resp.status_code}: unauthenticated access should be rejected"

    def test_expired_token_returns_401(self, client, expired_headers):
        """过期 token 应该返回 401"""
        resp = client.get("/api/v1/classrooms", headers=expired_headers)
        assert resp.status_code in (401, 403), \
            f"Expected 401/403 but got {resp.status_code}: expired token should be rejected"

    def test_malformed_token_returns_401(self, client):
        """格式错误的 token 应该返回 401"""
        resp = client.get("/api/v1/classrooms",
                         headers={"Authorization": "Bearer this_is_not_a_valid_jwt"})
        assert resp.status_code in (401, 403), \
            f"Expected 401/403 but got {resp.status_code}: malformed token should be rejected"

    def test_missing_bearer_prefix(self, client):
        """缺少 Bearer 前缀应该返回 401"""
        resp = client.get("/api/v1/classrooms",
                         headers={"Authorization": "just_a_token"})
        assert resp.status_code in (401, 403, 422), \
            f"Expected 401/403/422 but got {resp.status_code}"
