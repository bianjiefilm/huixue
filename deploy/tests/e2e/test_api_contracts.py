"""
API contract tests — validate response schemas for core endpoints.

These tests verify field names/types don't silently change after refactoring.
Not testing business logic, only response shape stability.
"""
import pytest
import requests
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
def teacher_headers(teacher_token):
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture(scope="module")
def student_token():
    token = get_api_token("student1", "student123")
    if not token:
        pytest.skip("Cannot obtain student token")
    return token


@pytest.fixture(scope="module")
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


# ==================== /api/me ====================

class TestMeContract:

    def test_me_has_required_fields(self, teacher_headers):
        r = SESSION.get(f"{API_URL}/api/me", headers=teacher_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("id"), int)
        assert isinstance(data.get("username"), str)

    def test_student_me(self, student_headers):
        r = SESSION.get(f"{API_URL}/api/me", headers=student_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("id"), int)


# ==================== /api/v1/classrooms ====================

class TestClassroomsContract:

    def test_list_returns_array(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        payload = data.get("data", data)
        # Should be list or paginated
        if isinstance(payload, dict):
            items = payload.get("list", payload.get("items", []))
        else:
            items = payload
        assert isinstance(items, list)

    def test_classroom_item_shape(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json()
        payload = data.get("data", data)
        items = payload.get("list", payload.get("items", payload)) if isinstance(payload, dict) else payload
        if not items:
            pytest.skip("No classrooms")
        item = items[0]
        assert "id" in item
        assert "name" in item


# ==================== /api/v1/courses ====================

class TestCoursesContract:

    def test_list_shape(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("code") == "0000"
        items = data.get("data", {}).get("list", [])
        assert isinstance(items, list)

    def test_course_item_has_id_title(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        items = r.json().get("data", {}).get("list", [])
        if not items:
            pytest.skip("No courses")
        c = items[0]
        assert isinstance(c.get("id"), int)
        assert isinstance(c.get("title"), str)
        assert len(c["title"]) > 0

    def test_course_item_has_type(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        items = r.json().get("data", {}).get("list", [])
        if not items:
            pytest.skip("No courses")
        c = items[0]
        assert "course_type" in c or "type" in c


# ==================== /api/v1/trainings ====================

class TestTrainingsContract:

    def test_list_shape(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/my-trainings",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("code") == "0000"


# ==================== /api/v1/classrooms/{id}/courses ====================

class TestClassroomCoursesContract:

    def test_classroom_courses_shape(self, teacher_headers):
        # Get first classroom
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        payload = r.json().get("data", r.json())
        items = payload.get("list", payload.get("items", payload)) if isinstance(payload, dict) else payload
        if not items:
            pytest.skip("No classrooms")
        cid = items[0]["id"]

        r2 = SESSION.get(
            f"{API_URL}/api/v1/classrooms/{cid}/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r2.status_code == 200
        data = r2.json()
        courses = data.get("data", {}).get("courses", [])
        assert isinstance(courses, list)

    def test_classroom_course_item_shape(self, teacher_headers):
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        payload = r.json().get("data", r.json())
        items = payload.get("list", payload.get("items", payload)) if isinstance(payload, dict) else payload
        if not items:
            pytest.skip("No classrooms")
        cid = items[0]["id"]

        r2 = SESSION.get(
            f"{API_URL}/api/v1/classrooms/{cid}/courses",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        courses = r2.json().get("data", {}).get("courses", [])
        if not courses:
            pytest.skip("No courses in classroom")
        c = courses[0]
        assert "course_name" in c or "name" in c or "title" in c


# ==================== /health ====================

class TestHealthContract:

    def test_health_shape(self):
        r = SESSION.get(f"{API_URL}/health", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "database" in data
