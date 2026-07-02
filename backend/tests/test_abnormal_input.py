"""
test_abnormal_input.py — 异常输入边界测试
验证空字符串、超长输入、XSS、SQL注入、非法日期等
Targets: TD-01, TD-05
"""
import pytest


class TestClassroomInputValidation:
    """课堂创建输入校验"""

    def test_empty_classroom_name(self, client, teacher_headers):
        """课堂名称为空字符串应被拒绝"""
        resp = client.post("/api/v1/classrooms", json={
            "name": "",
            "start_date": "2026-04-01T00:00:00",
            "end_date": "2026-07-01T00:00:00",
        }, headers=teacher_headers)
        assert resp.status_code in (400, 422), \
            f"Expected 422 but got {resp.status_code}: empty name should be rejected"

    def test_classroom_name_extremely_long(self, client, teacher_headers):
        """超长课堂名称应被拒绝或截断"""
        long_name = "A" * 500  # 远超 200 char Column limit
        resp = client.post("/api/v1/classrooms", json={
            "name": long_name,
            "start_date": "2026-04-01T00:00:00",
            "end_date": "2026-07-01T00:00:00",
        }, headers=teacher_headers)
        # 应被 Pydantic 或 DB 拦截，不应 500
        assert resp.status_code != 500, \
            f"500 on oversized name means no input validation: {resp.text[:200]}"

    def test_xss_in_classroom_name(self, client, teacher_headers):
        """XSS payload 在课堂名称中不应被原样存储"""
        xss_payload = '<script>alert("XSS")</script>大数据课堂'
        resp = client.post("/api/v1/classrooms", json={
            "name": xss_payload,
            "start_date": "2026-04-01T00:00:00",
            "end_date": "2026-07-01T00:00:00",
        }, headers=teacher_headers)
        if resp.status_code in (200, 201):
            data = resp.json()
            # 检查返回的名称是否被净化
            returned_name = data.get("data", {}).get("name", "")
            if "<script>" in returned_name:
                pytest.fail(
                    f"XSS payload stored as-is in classroom name. "
                    f"This is a potential XSS vulnerability."
                )


class TestDateInputValidation:
    """日期输入校验"""

    def test_invalid_date_format(self, client, teacher_headers):
        """非法日期格式应被拒绝"""
        resp = client.post("/api/v1/classrooms", json={
            "name": "测试课堂",
            "start_date": "not-a-date",
            "end_date": "也不是日期",
        }, headers=teacher_headers)
        assert resp.status_code == 422, \
            f"Expected 422 but got {resp.status_code}: invalid date should trigger validation error"

    def test_end_date_before_start_date(self, client, teacher_headers):
        """结束日期早于开始日期应被拒绝"""
        resp = client.post("/api/v1/classrooms", json={
            "name": "结束日期倒置的课堂",
            "start_date": "2026-07-01T00:00:00",
            "end_date": "2026-04-01T00:00:00",  # 结束 < 开始
        }, headers=teacher_headers)
        if resp.status_code in (200, 201):
            pytest.fail(
                "Classroom created with end_date before start_date. "
                "This violates logical constraints."
            )


class TestSearchInputSafety:
    """搜索输入安全性"""

    def test_sql_injection_in_search(self, client, teacher_headers):
        """SQL 注入 payload 不应导致服务器错误"""
        resp = client.get(
            "/api/v1/classrooms",
            params={"keyword": "'; DROP TABLE classrooms; --"},
            headers=teacher_headers,
        )
        assert resp.status_code != 500, \
            f"SQL injection payload caused 500 error — possible SQL injection vulnerability"

    def test_sql_injection_in_course_search(self, client, teacher_headers):
        """课程搜索中的 SQL 注入"""
        resp = client.get(
            "/api/v1/courses",
            params={"keyword": "' OR '1'='1"},
            headers=teacher_headers,
        )
        assert resp.status_code != 500, \
            f"SQL injection in course search caused 500"


class TestPayloadSizeAndBounds:
    """负载大小与数值边界"""

    def test_oversized_code_submission(self, client, student_headers):
        """提交超大代码内容不应导致服务器崩溃"""
        huge_code = "x = 1\n" * 100000  # ~600KB 代码
        resp = client.post(
            "/api/v1/tasks/300/evaluate",
            json={"code": huge_code},
            headers=student_headers,
        )
        assert resp.status_code != 500, \
            f"Oversized code submission caused 500: {resp.text[:200]}"

    def test_negative_page_number(self, client, teacher_headers):
        """负数页码不应导致错误"""
        resp = client.get(
            "/api/v1/classrooms",
            params={"page": -1, "page_size": 10},
            headers=teacher_headers,
        )
        assert resp.status_code != 500, \
            f"Negative page number caused 500 — should default to 1 or return 422"

    def test_zero_page_size(self, client, teacher_headers):
        """页大小为 0 不应导致除零错误"""
        resp = client.get(
            "/api/v1/courses",
            params={"page": 1, "page_size": 0},
            headers=teacher_headers,
        )
        assert resp.status_code != 500, \
            f"Zero page_size caused 500 — possible division by zero"

    def test_unicode_emoji_in_title(self, client, teacher_headers):
        """Unicode emoji 在标题中应被正确处理"""
        resp = client.post("/api/v1/classrooms", json={
            "name": "🎓 数据分析课堂 🏫",
            "start_date": "2026-04-01T00:00:00",
            "end_date": "2026-07-01T00:00:00",
        }, headers=teacher_headers)
        # Unicode emoji 应该能被存储和返回
        assert resp.status_code != 500, \
            f"Emoji in title caused 500 — Unicode handling issue"
