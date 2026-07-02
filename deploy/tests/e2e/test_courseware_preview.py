"""
Block 27 — 课件预览/下载端到端测试
覆盖: 课程资料详情 → 章节结构 → 资源文件访问 → 文件存储探测 → 课件下载
"""
import pytest
import requests
from conftest import API_URL, BASE_URL, get_api_token, resilient_session

TIMEOUT = 30
SESSION = resilient_session(retries=2, backoff=2.0)

COURSE_MATERIAL_ID = 100  # A股上市公司销售额分析


@pytest.fixture(scope="module")
def teacher_headers():
    token = get_api_token("teacher1", "teacher123")
    assert token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def student_headers():
    token = get_api_token("student1", "student123")
    assert token
    return {"Authorization": f"Bearer {token}"}


# ---------- 课程资料详情 ----------

class TestCourseMaterialDetail:

    def test_detail_reachable(self, teacher_headers):
        """课程资料详情端点可达"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/{COURSE_MATERIAL_ID}",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200

    def test_detail_has_required_fields(self, teacher_headers):
        """详情包含核心字段"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/{COURSE_MATERIAL_ID}",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json().get("data", {})
        for field in ["id", "title", "description"]:
            assert field in data, f"缺少字段: {field}"

    def test_detail_has_chapters(self, teacher_headers):
        """详情包含章节列表"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/{COURSE_MATERIAL_ID}",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json().get("data", {})
        chapters = data.get("chapters", data.get("chapter_list", []))
        assert isinstance(chapters, list)
        assert len(chapters) >= 1, "应至少有1个章节"

    def test_chapter_structure(self, teacher_headers):
        """章节包含id/title"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/{COURSE_MATERIAL_ID}",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        chapters = r.json()["data"].get("chapters", [])
        ch = chapters[0]
        assert "id" in ch
        assert "title" in ch or "name" in ch

    def test_detail_student_accessible(self, student_headers):
        """学生能看课程资料"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/{COURSE_MATERIAL_ID}",
            headers=student_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200

    def test_nonexistent_course_material(self, teacher_headers):
        """不存在的课程资料"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/99999",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            # 有些API返回200但data为空
            data = r.json().get("data")
            assert data is None or data == {} or data.get("id") is None


# ---------- 课程资料列表 ----------

class TestCourseMaterialList:

    def test_list_reachable(self, teacher_headers):
        """课程资料列表可达"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/lists",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200

    def test_list_response_structure(self, teacher_headers):
        """列表响应包含分页"""
        r = SESSION.get(
            f"{API_URL}/api/coursematerial/lists",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json().get("data", {})
        assert "total" in data or "list" in data


# ---------- 静态资源/文件预览 ----------

class TestFilePreview:

    def test_cover_image_accessible(self):
        """课程封面图可访问（若该 fixture 文件未部署则跳过）"""
        cover_path = "/static/resources/课程资源/A股上市公司销售额分析/cover.png"
        r = SESSION.get(f"{API_URL}{cover_path}", timeout=TIMEOUT)
        # 可能通过nginx或后端serve
        if r.status_code == 404:
            # 尝试前端地址
            r = SESSION.get(f"{BASE_URL}{cover_path}", timeout=TIMEOUT)
        if r.status_code == 404:
            pytest.skip(f"Cover fixture not deployed at {cover_path}")
        assert r.status_code in (200, 301, 302, 304), f"Cover image not accessible: {r.status_code}"

    def test_file_access_probe(self, teacher_headers):
        """文件访问探测端点"""
        r = SESSION.get(
            f"{API_URL}/api/v1/files/test-file-access",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert "base_dir" in data

    def test_download_nonexistent_file(self, teacher_headers):
        """下载不存在的文件返回404"""
        r = SESSION.get(
            f"{API_URL}/api/v1/files/download",
            headers=teacher_headers,
            params={"path": "/nonexistent/file.pdf"},
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 422, 400)

    def test_storage_stats(self, teacher_headers):
        """存储统计端点可达"""
        r = SESSION.get(
            f"{API_URL}/api/v1/storage/stats",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        # 已知bug: user_role未定义导致返回2000错误码
        assert r.status_code == 200


# ---------- 课件完整性校验 ----------

class TestCoursewareIntegrity:

    def test_multiple_courses_have_material(self, teacher_headers):
        """多门课程都有对应资料"""
        r = SESSION.get(
            f"{API_URL}/api/v1/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json().get("data", r.json())
        items = data.get("list", data.get("items", data if isinstance(data, list) else []))
        assert len(items) >= 1, "应有至少1门课程"

    def test_course_has_title_and_id(self, teacher_headers):
        """课程包含id和标题"""
        r = SESSION.get(
            f"{API_URL}/api/v1/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json().get("data", r.json())
        items = data.get("list", data.get("items", data if isinstance(data, list) else []))
        if not items:
            pytest.skip("No courses")
        course = items[0]
        assert "id" in course
        assert "title" in course or "name" in course or "course_name" in course

    def test_course_detail_from_classroom(self, teacher_headers):
        """班级内课程有完整详情"""
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms/100/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        courses = r.json().get("data", {}).get("courses", [])
        assert len(courses) >= 1
        c = courses[0]
        assert c.get("course_name") or c.get("name")
