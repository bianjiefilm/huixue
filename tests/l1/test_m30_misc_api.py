"""
tests/l1/test_m30_misc_api.py
L1 API contract tests for remaining endpoint modules.

Covers:
  AC1: Health check          GET /health, GET /
  AC2: Usage statistics      GET /api/v1/usage-statistics/{courses,practices,trainings,teachers,students}
  AC3: Usage stats detail    GET /api/v1/usage-statistics/courses/{id}/details
  AC4: Project canvas        GET /api/v1/project-canvas/canvas
  AC5: Project canvas node   GET /api/v1/project-canvas/canvas/node/{id}
  AC6: Common endpoints      GET /api/v1/statistics, GET /api/v1/organization-tree
  AC7: Compatibility routes  GET /api/v1/organizations/tree, /classes/departlists, /organizations, /students
  AC8: Stages - list         GET /api/v1/practices/{id}/stages
  AC9: Stages - templates    GET /api/v1/stage-templates
  AC10: Stages - detail      GET /api/v1/stages/{id}
  AC11: Error paths
"""
import pytest
import requests
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _get_first_practice_id(token):
    """Return the first practice id visible to the admin user, or None."""
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices",
            params={"page": 1, "size": 1, "creator_id": 1},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            items = data.get("list", []) if isinstance(data, dict) else []
            if items:
                return items[0].get("id")
    finally:
        s.close()
    return None


def _get_first_stage_id(token, practice_id=None):
    """Return a stage_id or None.
    If practice_id is None, scan practices across known creator_ids to find accessible stages."""
    s = _session(token)
    try:
        candidate_creators = [1, 29]  # admin 与典型 teacher
        if practice_id is not None:
            practice_ids = [practice_id]
        else:
            practice_ids = []
            for cid in candidate_creators:
                resp = s.get(
                    f"{BASE_URL}/api/v1/practices",
                    params={"page": 1, "size": 20, "creator_id": cid},
                    timeout=TIMEOUT,
                )
                if resp.status_code == 200:
                    practice_ids += [p.get("id") for p in (resp.json().get("data", {}).get("list", []))]
            # 去重保持顺序
            seen = set()
            practice_ids = [p for p in practice_ids if not (p in seen or seen.add(p))]

        for pid in practice_ids:
            for cid in candidate_creators:
                resp2 = s.get(
                    f"{BASE_URL}/api/v1/practices/{pid}/stages",
                    params={"creator_id": cid, "page": 1, "page_size": 1},
                    timeout=TIMEOUT,
                )
                if resp2.status_code == 200 and resp2.json() is not None:
                    body = resp2.json()
                    if body.get("code") == "0000":
                        items = (body.get("data") or {}).get("list", [])
                        if items:
                            return items[0].get("id") or items[0].get("stage_id")
    finally:
        s.close()
    return None


def _get_first_training_id(token):
    """Return the first training id, or None."""
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/trainings/",
            params={"page": 1, "page_size": 1},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json() is not None:
            data = (resp.json().get("data") or {})
            items = data.get("list", []) if isinstance(data, dict) else []
            if items:
                return items[0].get("id") or items[0].get("training_id")
    finally:
        s.close()
    return None


# ═══════════════════════════════════════════════════════════════
# AC1: Health check
# ═══════════════════════════════════════════════════════════════

def test_health_check():
    """AC1: GET /health -> 200 with status field"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        body = resp.json()
        assert "status" in body, "Health response should contain 'status' key"
    finally:
        s.close()


def test_root_endpoint():
    """AC1: GET / -> 200 welcome message"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        body = resp.json()
        assert "status" in body or "message" in body
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: Usage statistics - list endpoints
# ═══════════════════════════════════════════════════════════════

def test_usage_statistics_courses():
    """AC2: GET /api/v1/usage-statistics/courses -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/courses",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "5000"), f"Unexpected code: {body.get('code')}"
    finally:
        s.close()


def test_usage_statistics_practices():
    """AC2: GET /api/v1/usage-statistics/practices -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/practices",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "5000")
    finally:
        s.close()


def test_usage_statistics_trainings():
    """AC2: GET /api/v1/usage-statistics/trainings -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/trainings",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "5000")
    finally:
        s.close()


def test_usage_statistics_teachers():
    """AC2: GET /api/v1/usage-statistics/teachers -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/teachers",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "5000")
    finally:
        s.close()


def test_usage_statistics_students():
    """AC2: GET /api/v1/usage-statistics/students -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/students",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "5000")
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC3: Usage stats - course detail drill-down
# ═══════════════════════════════════════════════════════════════

def test_usage_statistics_course_details():
    """AC3: GET /api/v1/usage-statistics/courses/{id}/details -> 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if pid is None:
        pytest.skip("No practices available for course detail stats")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/courses/{pid}/details",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "4004", "5000")
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC4: Project canvas
# ═══════════════════════════════════════════════════════════════

def test_project_canvas():
    """AC4: GET /api/v1/project-canvas/canvas -> 200 with nodes"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/project-canvas/canvas", timeout=TIMEOUT)
        assert resp.status_code == 200
        body = resp.json()
        assert "success" in body, "Canvas response should contain 'success' field"
        assert "nodes" in body, "Canvas response should contain 'nodes' field"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC5: Project canvas node detail
# ═══════════════════════════════════════════════════════════════

def test_project_canvas_node_detail():
    """AC5: GET /api/v1/project-canvas/canvas/node/{id} -> 200 or 404"""
    token = _get_token("admin")
    tid = _get_first_training_id(token)
    if tid is None:
        pytest.skip("No trainings available for canvas node detail")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/project-canvas/canvas/node/{tid}",
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 404), f"Expected 200/404, got {resp.status_code}"
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("success") is True
    finally:
        s.close()


def test_project_canvas_node_not_found():
    """AC5: GET /api/v1/project-canvas/canvas/node/999999 -> 404"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/project-canvas/canvas/node/999999",
            timeout=TIMEOUT,
        )
        assert resp.status_code in (404, 500), f"Expected 404/500, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC6: Common endpoints
# ═══════════════════════════════════════════════════════════════

def test_common_statistics():
    """AC6: GET /api/v1/statistics -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/statistics", timeout=TIMEOUT)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == "0000"
    finally:
        s.close()


def test_common_organization_tree():
    """AC6: GET /api/v1/organization-tree -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/organization-tree", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_common_filter_tags_practices():
    """AC6: GET /api/v1/filter-tags/practices -> 200 (may 404 if not deployed)"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/filter-tags/practices", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC7: Compatibility routes
# ═══════════════════════════════════════════════════════════════

def test_compat_organization_tree():
    """AC7: GET /api/v1/organizations/tree -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/organizations/tree", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_compat_department_lists():
    """AC7: GET /api/v1/classes/departlists -> 200 returns list"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classes/departlists", timeout=TIMEOUT)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), "departlists should return a JSON array"
    finally:
        s.close()


def test_compat_organizations_list():
    """AC7: GET /api/v1/organizations -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/organizations",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "list" in body or "meta" in body, "organizations response should have list or meta"
    finally:
        s.close()


def test_compat_students_list():
    """AC7: GET /api/v1/students -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/students",
            params={"page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        data = body.get("data", body)
        assert "list" in data or "meta" in data
    finally:
        s.close()


def test_compat_class_students():
    """AC7: GET /api/v1/classes/classtulists?class_id=class-default -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classes/classtulists",
            params={"class_id": "class-default"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), "classtulists should return a JSON array"
    finally:
        s.close()


def test_compat_project_datasets():
    """AC7: GET /api/v1/projects/{id}/datasets -> 200"""
    token = _get_token("admin")
    tid = _get_first_training_id(token)
    if tid is None:
        pytest.skip("No trainings available")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/projects/{tid}/datasets",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == "0000"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC8: Stages - list stages for a practice
# ═══════════════════════════════════════════════════════════════

def test_stages_list():
    """AC8: GET /api/v1/practices/{id}/stages -> 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if pid is None:
        pytest.skip("No practices available")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices/{pid}/stages",
            params={"creator_id": 1, "page": 1, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


def test_stages_management():
    """AC8: GET /api/v1/practices/{id}/stages/management -> 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if pid is None:
        pytest.skip("No practices available")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices/{pid}/stages/management",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


def test_stages_repository_files():
    """AC8: GET /api/v1/practices/{id}/repository/files -> 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if pid is None:
        pytest.skip("No practices available")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices/{pid}/repository/files",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC9: Stage templates
# ═══════════════════════════════════════════════════════════════

def test_stage_templates():
    """AC9: GET /api/v1/stage-templates -> 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/stage-templates", timeout=TIMEOUT)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "2000")
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC10: Stage detail and question data
# ═══════════════════════════════════════════════════════════════

def test_stage_detail():
    """AC10: GET /api/v1/stages/{id} -> 200"""
    token = _get_token("admin")
    stage_id = _get_first_stage_id(token)
    if stage_id is None:
        pytest.skip("No accessible stages found")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/stages/{stage_id}",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


def test_stage_question_data():
    """AC10: GET /api/v1/stages/{id}/question-data -> 200"""
    token = _get_token("admin")
    stage_id = _get_first_stage_id(token)
    if stage_id is None:
        pytest.skip("No accessible stages found")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/stages/{stage_id}/question-data",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


def test_stage_delete_validation():
    """AC10: GET /api/v1/stages/{id}/delete-validation -> 200"""
    token = _get_token("admin")
    stage_id = _get_first_stage_id(token)
    if stage_id is None:
        pytest.skip("No accessible stages found")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/stages/{stage_id}/delete-validation",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


def test_stage_student_view():
    """AC10: GET /api/v1/stages/{id}/student-view -> 200
    Accept 404 when the endpoint has not been deployed to the test server yet."""
    token = _get_token("admin")
    stage_id = _get_first_stage_id(token)
    if stage_id is None:
        pytest.skip("No accessible stages found")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/stages/{stage_id}/student-view",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") in ("0000", "1002", "2000")
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC11: Error paths
# ═══════════════════════════════════════════════════════════════

def test_stages_missing_creator_id():
    """AC11: GET /api/v1/practices/1/stages without creator_id -> 422"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices/1/stages",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 422, f"Expected 422 (missing required query param), got {resp.status_code}"
    finally:
        s.close()


def test_stage_detail_nonexistent():
    """AC11: GET /api/v1/stages/999999 -> 200 with code 1002 (not found)"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/stages/999999",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("code") == "1002", f"Expected code 1002, got {body.get('code')}"
    finally:
        s.close()


def test_canvas_no_auth():
    """AC11: GET /api/v1/project-canvas/canvas without token -> 401/403"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/v1/project-canvas/canvas", timeout=TIMEOUT)
        assert resp.status_code in (401, 403, 307), f"Expected 401/403/307, got {resp.status_code}"
    finally:
        s.close()


def test_usage_statistics_invalid_page():
    """AC11: GET /api/v1/usage-statistics/courses?page=0 -> 422 (page >= 1)"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/usage-statistics/courses",
            params={"page": 0, "page_size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
    finally:
        s.close()
