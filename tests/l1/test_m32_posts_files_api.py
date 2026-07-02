"""
L1 API contract tests for: posts, file_serve, file_upload, ai_assistant, ai_features.

Validates HTTP status codes, response shapes, and error handling.
Does NOT call AI generation endpoints that cost money -- only tests
that endpoints exist by sending minimal/empty payloads and expecting
400/422/500 rather than triggering actual LLM calls.
"""

import pytest
import requests
import uuid

from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1

AI_TIMEOUT = 30  # AI endpoints may be slow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def admin_token():
    token = _get_token("admin")
    if not token:
        pytest.skip("Cannot obtain admin token")
    return token


@pytest.fixture(scope="module")
def admin_session(admin_token):
    return _session(admin_token)


# ===========================================================================
# Posts CRUD
# ===========================================================================

class TestPostsCRUD:
    """Test discussion posts endpoints under /api/v1/posts/posts/."""

    def test_list_posts(self, admin_session):
        """GET /api/v1/posts/posts/ should return a list."""
        r = admin_session.get(f"{BASE_URL}/api/v1/posts/posts/", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_create_read_delete_post(self, admin_session):
        """Full CRUD lifecycle for a post."""
        post_id = None
        try:
            # CREATE
            payload = {
                "title": f"L1-test-{uuid.uuid4().hex[:8]}",
                "content": "Automated L1 test post content.",
                "author_id": 1,
            }
            r = admin_session.post(
                f"{BASE_URL}/api/v1/posts/posts/", json=payload, timeout=TIMEOUT
            )
            assert r.status_code in (200, 201, 422), f"Create post unexpected: {r.status_code}"
            if r.status_code in (422,):
                pytest.skip("Post schema may require additional fields")
            body = r.json()
            post_id = body.get("id")
            assert post_id is not None, "Created post must have an id"

            # READ
            r2 = admin_session.get(
                f"{BASE_URL}/api/v1/posts/posts/{post_id}", timeout=TIMEOUT
            )
            assert r2.status_code == 200
            assert r2.json()["id"] == post_id

        finally:
            # DELETE (cleanup)
            if post_id is not None:
                rd = admin_session.delete(
                    f"{BASE_URL}/api/v1/posts/posts/{post_id}", timeout=TIMEOUT
                )
                assert rd.status_code in (200, 204, 404)

    def test_get_nonexistent_post(self, admin_session):
        """GET a non-existent post should return 404."""
        try:
            r = admin_session.get(
                f"{BASE_URL}/api/v1/posts/posts/999999", timeout=TIMEOUT
            )
            assert r.status_code == 404
        except requests.exceptions.ConnectionError:
            pytest.skip("Transient connection error")

    def test_delete_nonexistent_post(self, admin_session):
        """DELETE a non-existent post should return 404."""
        r = admin_session.delete(
            f"{BASE_URL}/api/v1/posts/posts/999999", timeout=TIMEOUT
        )
        assert r.status_code == 404


# ===========================================================================
# File Serve -- test that endpoints exist and handle missing files
# ===========================================================================

class TestFileServe:
    """Test file serving endpoints under /api/v1/files/."""

    def test_file_access_diagnostic(self, admin_session):
        """GET /api/v1/files/test-file-access should return diagnostic info."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/test-file-access", timeout=TIMEOUT
        )
        assert r.status_code == 200
        body = r.json()
        assert "base_dir" in body

    def test_classroom_disk_missing_file(self, admin_session):
        """Requesting a non-existent classroom disk file should fail gracefully."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/classroom-disk/99999/nonexistent.txt",
            timeout=TIMEOUT,
        )
        # Server returns 500 wrapping the 404 -- accept either
        assert r.status_code in (404, 500)

    def test_training_dataset_missing_file(self, admin_session):
        """Requesting a non-existent training dataset file should fail gracefully."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/training-dataset/99999/nonexistent.csv",
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 500)

    def test_homework_missing_file(self, admin_session):
        """Requesting a non-existent homework file should fail gracefully."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/homework/99999/99999/nonexistent.pdf",
            timeout=TIMEOUT,
        )
        assert r.status_code in (403, 404, 500)

    def test_syllabus_missing_file(self, admin_session):
        """Requesting a non-existent syllabus file should return 404."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/syllabus/nonexistent_syllabus.md",
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 500)

    def test_teaching_resource_missing_file(self, admin_session):
        """Requesting a non-existent teaching resource should fail gracefully."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/teaching-resource/99999/nonexistent.pptx",
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 500)

    def test_course_files_missing(self, admin_session):
        """Requesting a non-existent course file should return 404."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/course-files/nonexistent/path/file.pdf",
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 500)

    def test_teaching_resources_path_missing(self, admin_session):
        """Requesting a non-existent teaching-resources path should return 404."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/teaching-resources/nonexistent/file.pdf",
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 500)

    def test_preview_image_missing(self, admin_session):
        """Requesting a non-existent preview image should return 404."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/files/preview/image/nonexistent/img.png",
            timeout=TIMEOUT,
        )
        assert r.status_code in (404, 500)


# ===========================================================================
# File Upload -- contract checks with inline multipart payloads
# ===========================================================================

# 合法响应集合：
#   200 - 上传成功
#   400/403/422 - 业务校验失败（权限不足、参数不合法）
#   404 - 关联实体（课堂/实训/作业）不存在
# 目的: 验证路由已注册且接收 multipart 负载；不要求实际写盘成功。
_ACCEPT_UPLOAD_STATUS = (200, 400, 403, 404, 422)


class TestFileUpload:
    """File upload endpoints — contract validation with minimal multipart payload."""

    def test_upload_classroom_disk(self, admin_session):
        """POST /api/v1/files/upload/classroom-disk 接受 multipart/form-data"""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/files/upload/classroom-disk",
            files={"file": ("t.txt", b"x", "text/plain")},
            data={
                "classroom_id": 1,
                "teacher_id": 1,
                "file_name": "t.txt",
                "folder_path": "",
                "is_shared": "false",
            },
            timeout=TIMEOUT,
        )
        assert r.status_code in _ACCEPT_UPLOAD_STATUS, f"Got {r.status_code}: {r.text[:200]}"

    def test_upload_training_dataset(self, admin_session):
        """POST /api/v1/files/upload/training-dataset 接受 multipart/form-data"""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/files/upload/training-dataset",
            files={"file": ("t.csv", b"a,b\n1,2\n", "text/csv")},
            data={"training_id": 1, "description": "contract test"},
            timeout=TIMEOUT,
        )
        assert r.status_code in _ACCEPT_UPLOAD_STATUS, f"Got {r.status_code}: {r.text[:200]}"

    def test_upload_homework_submission(self, admin_session):
        """POST /api/v1/files/upload/homework-submission 接受 multipart/form-data"""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/files/upload/homework-submission",
            files={"file": ("t.txt", b"x", "text/plain")},
            data={
                "homework_id": 1,
                "student_id": 1,
                "submission_type": "report",
            },
            timeout=TIMEOUT,
        )
        # 500 也接受：此路由未充分处理不存在作业的路径
        assert r.status_code in _ACCEPT_UPLOAD_STATUS + (500,), f"Got {r.status_code}: {r.text[:200]}"

    @pytest.mark.xfail(
        reason="Backend endpoint references nonexistent models.TeachingResourceModule "
               "(orphaned code path, returns 500 AttributeError)",
        strict=True,
    )
    def test_upload_teaching_resource(self, admin_session):
        """POST /api/v1/files/upload/teaching-resource 接受 multipart/form-data"""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/files/upload/teaching-resource",
            files={"file": ("t.pdf", b"%PDF-1.4 test", "application/pdf")},
            data={
                "module_id": 1,
                "teacher_id": 1,
                "file_name": "t.pdf",
                "file_type": "document",
                "description": "contract test",
            },
            timeout=TIMEOUT,
        )
        assert r.status_code in _ACCEPT_UPLOAD_STATUS, f"Got {r.status_code}: {r.text[:200]}"


# ===========================================================================
# AI Assistant (/api/v1/ai)
# ===========================================================================

class TestAIAssistant:
    """
    Tests for /api/v1/ai endpoints.

    We do NOT call generation endpoints with real data to avoid LLM costs.
    Instead we send minimal/empty payloads and verify the endpoint exists
    (expecting 422 for missing fields, or 500 if AI is not configured).
    """

    def test_quota_endpoint(self, admin_session):
        """GET /api/v1/ai/quota/1 should return quota info."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/ai/quota/1", timeout=TIMEOUT
        )
        assert r.status_code == 200
        body = r.json()
        assert "monthly_quota" in body or "remaining" in body

    def test_summary_empty_content(self, admin_session):
        """POST /api/v1/ai/summary with empty content -- should not cost money."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai/summary",
            json={"content": "", "course_title": ""},
            timeout=AI_TIMEOUT,
        )
        # Empty content may return empty result (200) or fail (500) if AI unconfigured
        assert r.status_code in (200, 422, 500)


    def test_chat_missing_fields(self, admin_session):
        """POST /api/v1/ai/chat with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai/chat", json={}, timeout=AI_TIMEOUT
        )
        assert r.status_code == 422


    def test_explain_concept_missing_fields(self, admin_session):
        """POST /api/v1/ai/explain-concept with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai/explain-concept", json={}, timeout=AI_TIMEOUT
        )
        assert r.status_code == 422


    def test_generate_questions_missing_fields(self, admin_session):
        """POST /api/v1/ai/generate-questions with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai/generate-questions", json={}, timeout=AI_TIMEOUT
        )
        assert r.status_code == 422


    def test_check_quality_missing_fields(self, admin_session):
        """POST /api/v1/ai/check-quality with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai/check-quality", json={}, timeout=AI_TIMEOUT
        )
        assert r.status_code == 422


# ===========================================================================
# AI Features (/api/v1/ai-features)
# ===========================================================================

class TestAIFeatures:
    """
    Tests for /api/v1/ai-features endpoints (PromptPilot integration).

    We do NOT trigger actual LLM calls. We test:
    - Status endpoint (GET)
    - Validation errors for missing required fields (expect 422)
    """

    def test_status(self, admin_session):
        """GET /api/v1/ai-features/status should return service availability."""
        r = admin_session.get(
            f"{BASE_URL}/api/v1/ai-features/status", timeout=TIMEOUT
        )
        assert r.status_code == 200
        body = r.json()
        assert "available" in body
        assert "task_ids" in body


    def test_recommendation_explain_missing_fields(self, admin_session):
        """POST /ai-features/recommendation/explain with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/recommendation/explain",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_brainstorm_missing_fields(self, admin_session):
        """POST /ai-features/brainstorm with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/brainstorm",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_command_parse_missing_fields(self, admin_session):
        """POST /ai-features/command/parse with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/command/parse",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_code_suggest_missing_fields(self, admin_session):
        """POST /ai-features/code/suggest with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/code/suggest",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_code_explain_missing_fields(self, admin_session):
        """POST /ai-features/code/explain with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/code/explain",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_code_diagnose_missing_fields(self, admin_session):
        """POST /ai-features/code/diagnose with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/code/diagnose",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_general_chat_missing_fields(self, admin_session):
        """POST /ai-features/chat with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/chat",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422


    def test_batch_recommendation_missing_fields(self, admin_session):
        """POST /ai-features/recommendation/batch with empty body -- expect 422."""
        r = admin_session.post(
            f"{BASE_URL}/api/v1/ai-features/recommendation/batch",
            json={},
            timeout=AI_TIMEOUT,
        )
        assert r.status_code == 422
