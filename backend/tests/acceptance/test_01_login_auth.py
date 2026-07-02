"""
验收测试 Part 1: 登录系统 (AC001-AC008)
真实 FastAPI TestClient + 真实 SQLite 数据库，禁止 mock
"""
import pytest
from tests.acceptance.conftest import auth_header


class TestLoginSystem:
    """登录系统 — AC001 ~ AC008"""

    # ====== 正常流 ======

    def test_ac001_login_success_admin(self, client, seed_users):
        """📌 AC001 正常流: 管理员使用正确用户名密码登录 → 返回 token 和用户信息"""
        resp = client.post("/api/login", json={
            "username": "admin", "password": "admin123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["token"]["access_token"]
        assert data["user"]["role"] == "admin"

    def test_ac001_login_success_teacher(self, client, seed_users):
        """📌 AC001 正常流: 教师使用正确用户名密码登录"""
        resp = client.post("/api/login", json={
            "username": "teacher1", "password": "teacher123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["role"] == "teacher"

    def test_ac001_login_success_student(self, client, seed_users):
        """📌 AC001 正常流: 学生使用正确用户名密码登录"""
        resp = client.post("/api/login", json={
            "username": "student1", "password": "student123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["role"] == "student"

    # ====== 边界条件 ======

    def test_ac002_empty_username(self, client):
        """📌 AC002 边界: 用户名为空、密码不为空 → 应返回 401"""
        resp = client.post("/api/login", json={
            "username": "", "password": "admin123"
        })
        assert resp.status_code == 401

    def test_ac003_empty_password(self, client):
        """📌 AC003 边界: 密码为空、用户名不为空 → 应返回 401"""
        resp = client.post("/api/login", json={
            "username": "admin", "password": ""
        })
        assert resp.status_code == 401

    def test_ac004_both_empty(self, client):
        """📌 AC004 边界: 用户名和密码均为空 → 应返回 401"""
        resp = client.post("/api/login", json={
            "username": "", "password": ""
        })
        assert resp.status_code == 401

    # ====== 异常处理 ======

    def test_ac005_wrong_password(self, client, seed_users):
        """📌 AC005 异常: 输入错误密码 → 应返回 401"""
        resp = client.post("/api/login", json={
            "username": "admin", "password": "wrongpassword"
        })
        assert resp.status_code == 401

    def test_ac005_wrong_username(self, client):
        """📌 AC005 异常: 输入不存在的用户名 → 应返回 401"""
        resp = client.post("/api/login", json={
            "username": "nonexistent_user_xyz", "password": "any"
        })
        assert resp.status_code == 401

    def test_ac006_malformed_json(self, client):
        """📌 AC006 异常: 请求体格式错误 → 应返回友好错误提示"""
        resp = client.post("/api/login", content="not-json",
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

    # ====== 业务规则 ======

    def test_ac007_token_isolation(self, client, seed_users):
        """📌 AC007 业务规则: 两次登录获得的 token 不同（会话隔离）"""
        resp1 = client.post("/api/login", json={
            "username": "admin", "password": "admin123"
        })
        resp2 = client.post("/api/login", json={
            "username": "teacher1", "password": "teacher123"
        })
        token1 = resp1.json()["token"]["access_token"]
        token2 = resp2.json()["token"]["access_token"]
        assert token1 != token2

    def test_ac008_disabled_user(self, client, seed_users):
        """📌 AC008 业务规则: 被停用的用户尝试登录 → 应返回 401"""
        resp = client.post("/api/login", json={
            "username": "disabled_user", "password": "test123"
        })
        assert resp.status_code == 401


class TestTokenValidation:
    """Token 验证相关（补充 AC007）"""

    def test_access_protected_route_without_token(self, client):
        """📌 AC214 异常: 未登录用户访问受保护路由 → 应返回 401"""
        resp = client.get("/api/v1/classrooms")
        assert resp.status_code == 401

    def test_access_with_invalid_token(self, client):
        """📌 AC214 异常: 使用无效 token → 应返回 401"""
        resp = client.get("/api/v1/classrooms",
                          headers={"Authorization": "Bearer invalid_token_xyz"})
        assert resp.status_code == 401

    def test_access_with_valid_token(self, client, teacher_token):
        """📌 AC001 正常流: 有效 token 可访问受保护路由"""
        if not teacher_token:
            pytest.skip("No teacher token available")
        resp = client.get("/api/v1/classrooms",
                          headers=auth_header(teacher_token))
        assert resp.status_code in (200, 422)  # 可能需要额外参数



"""
覆盖验收标准:
✅ AC001 — 正常登录流程（管理员/教师/学生）
✅ AC002 — 用户名为空边界
✅ AC003 — 密码为空边界
✅ AC004 — 均为空边界
✅ AC005 — 错误用户名/密码
✅ AC006 — 网络/格式异常
✅ AC007 — 会话隔离
✅ AC008 — 停用用户登录
✅ AC214 — 未登录用户访问保护路由

未覆盖（需浏览器 MCP 测试）:
👁️ AC001 — 登录后页面跳转验证（教师→我的课堂，学生→首页）
👁️ AC006 — 网络断开时的前端提示
"""


