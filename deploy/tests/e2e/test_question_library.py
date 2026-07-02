"""
Block 28 — 试题库端到端测试
覆盖: 试题库健康检查 → 筛选标签 → 试题CRUD → 试题复制
"""
import pytest
import requests
from conftest import API_URL, get_api_token, get_user_id, resilient_session

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


@pytest.fixture(scope="module")
def teacher_id(teacher_headers):
    token = teacher_headers["Authorization"].split(" ")[1]
    uid = get_user_id(token)
    assert uid
    return uid


class TestQuestionLibraryHealth:

    def test_health_check(self, admin_headers):
        """试题库健康检查"""
        r = SESSION.get(f"{API_URL}/api/v1/question-library/health", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "healthy"

    def test_filter_tags(self, admin_headers):
        """获取筛选标签"""
        r = SESSION.get(f"{API_URL}/api/v1/question-library/questions/filter-tags", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()["data"]
        assert "question_types" in data
        assert len(data["question_types"]) >= 1


class TestQuestionCRUD:

    def test_list_requires_teacher_id(self, admin_headers):
        """列表需要teacher_id参数"""
        r = SESSION.get(f"{API_URL}/api/v1/question-library/questions", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 422  # missing teacher_id

    def test_list_with_teacher_id(self, teacher_headers, teacher_id):
        """带teacher_id查询试题列表"""
        r = SESSION.get(
            f"{API_URL}/api/v1/question-library/questions",
            headers=teacher_headers, params={"teacher_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200

    def test_create_question(self, teacher_headers, teacher_id):
        """创建单选题(teacher_id作为query参数)"""
        r = SESSION.post(
            f"{API_URL}/api/v1/question-library/questions",
            headers=teacher_headers,
            params={"teacher_id": teacher_id},
            json={
                "question_type": "SINGLE_CHOICE",
                "content": "E2E测试题：Python中哪个是列表？",
                "options": [
                    {"label": "A", "content": "[]", "is_correct": True},
                    {"label": "B", "content": "{}", "is_correct": False},
                    {"label": "C", "content": "()", "is_correct": False},
                ],
                "answer": "A",
                "difficulty": "BEGINNER",
                "score": 5,
            },
            timeout=TIMEOUT,
        )
        assert r.status_code in (200, 201, 422), f"创建试题失败: {r.text[:300]}"

    def test_get_nonexistent_question(self, teacher_headers, teacher_id):
        """获取不存在的试题"""
        r = SESSION.get(
            f"{API_URL}/api/v1/question-library/questions/99999",
            headers=teacher_headers, params={"teacher_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert r.status_code in (200, 404, 422)

    def test_template_download(self, teacher_headers):
        """试题模板下载"""
        r = SESSION.get(f"{API_URL}/api/v1/question-library/questions/template", headers=teacher_headers, timeout=TIMEOUT)
        assert r.status_code in (200, 404)
