"""
tests/l2/test_bi_workflow.py
L2 BI 分析工作流集成测试

端到端工作流:
  1. Login as admin
  2. Create classroom
  3. Create BI training (training_type="BI")
  4. Publish training
  5. Save BI canvas with sample components
  6. Get preview URL -- verify URL contains /preview/bi/
  7. Save canvas again -- verify scene_id is same (update not create)
  8. Get BI data for training
  9. Cleanup

Note: BI detail (GET /bi/{id}/detail) and snapshot (POST /bi/{id}/snapshot)
      endpoints return 404 (removed from deployment) -- those steps are skipped.
"""
import pytest
import uuid

from tests.l1._auth_helper import (
    get_token as _get_token,
    make_session as _session,
    BASE_URL,
    TIMEOUT,
)

pytestmark = pytest.mark.l2


# ─── Helper functions ────────────────────────────────────────


def _create_classroom(token, suffix):
    """Create a classroom, return classroom_id or None."""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            params={"teacher_id": 1},
            json={
                "name": f"BI工作流测试_{suffix}",
                "description": f"L2 BI workflow test {suffix}",
                "semester": "2026-春",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            data = resp.json().get("data") or {}
            return data.get("classroom_id") or data.get("id")
    finally:
        s.close()
    return None


def _delete_classroom(token, classroom_id):
    if not classroom_id:
        return
    s = _session(token)
    try:
        s.delete(f"{BASE_URL}/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT)
    finally:
        s.close()


def _create_bi_training(token, suffix):
    """Create a BI training, return training id or None."""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/",
            json={
                "title": f"BI工作流实训_{suffix}",
                "training_type": "BI",
                "description": f"L2 BI workflow test {suffix}",
                "course_hours": 1,
                "assignment_nodes": [],
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            return (resp.json().get("data") or {}).get("id")
    finally:
        s.close()
    return None


def _delete_training(token, tid):
    if not tid:
        return
    s = _session(token)
    try:
        s.delete(f"{BASE_URL}/api/v1/trainings/detail/{tid}", timeout=TIMEOUT)
    finally:
        s.close()


def _publish_training(token, tid):
    """Publish a training, return response status code."""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/detail/{tid}/publish",
            timeout=TIMEOUT,
        )
        return resp.status_code
    finally:
        s.close()


def _bi_save(token, training_id, classroom_id, user_id, canvas_data):
    """Save BI canvas, return (status_code, scene_id, response_json)."""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/bi/{training_id}/save",
            json={
                "training_id": training_id,
                "classroom_id": classroom_id,
                "user_id": user_id,
                "canvas_data": canvas_data,
            },
            timeout=TIMEOUT,
        )
        data = resp.json() if resp.status_code == 200 else {}
        scene_id = (data.get("data") or {}).get("scene_id") or (data.get("data") or {}).get("draft_id")
        return resp.status_code, scene_id, data
    finally:
        s.close()


def _bi_preview_url(token, training_id, classroom_id, user_id):
    """Get BI preview URL, return (status_code, url, response_json)."""
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/bi/{training_id}/preview-url",
            params={
                "training_id": training_id,
                "classroom_id": classroom_id,
                "user_id": user_id,
            },
            timeout=TIMEOUT,
        )
        data = resp.json() if resp.status_code == 200 else {}
        url = (data.get("data") or {}).get("url")
        return resp.status_code, url, data
    finally:
        s.close()


def _bi_data(token, training_id):
    """Get BI data for training, return (status_code, response_json)."""
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/trainings/{training_id}/bi-data",
            timeout=TIMEOUT,
        )
        try:
            data = resp.json()
        except ValueError:
            data = {}
        return resp.status_code, data
    finally:
        s.close()


# ─── Main workflow test ──────────────────────────────────────


class TestBIWorkflow:
    """L2 integration: full BI analysis workflow end-to-end."""

    def test_bi_full_workflow(self):
        """
        Complete BI workflow:
        login -> create classroom -> create BI training -> publish ->
        save canvas -> get preview URL -> save again (idempotent) ->
        get BI data -> cleanup
        """
        suffix = uuid.uuid4().hex[:8]
        token = _get_token("admin")
        assert token, "Admin login failed -- cannot proceed"

        classroom_id = None
        training_id = None

        try:
            # ── Step 1: Create classroom ─────────────────────
            classroom_id = _create_classroom(token, suffix)
            assert classroom_id is not None, (
                "Failed to create classroom -- API returned no classroom_id"
            )

            # ── Step 2: Create BI training ───────────────────
            training_id = _create_bi_training(token, suffix)
            assert training_id is not None, (
                "Failed to create BI training -- API returned no training id"
            )

            # ── Step 3: Publish training ─────────────────────
            pub_status = _publish_training(token, training_id)
            assert pub_status == 200, (
                f"Publish training failed: expected 200, got {pub_status}"
            )

            # ── Step 4: Save BI canvas (first save) ──────────
            canvas_v1 = {
                "components": [
                    {"id": "comp-1", "type": "bar_chart", "title": "Sales Overview"},
                    {"id": "comp-2", "type": "pie_chart", "title": "Category Split"},
                ],
            }
            save1_status, scene_id_1, save1_resp = _bi_save(
                token, training_id, classroom_id, 1, canvas_v1,
            )
            assert save1_status == 200, (
                f"First BI save failed: expected 200, got {save1_status}. "
                f"Response: {save1_resp}"
            )
            assert scene_id_1 is not None, (
                f"First BI save returned no scene_id: {save1_resp}"
            )

            # ── Step 5: Get preview URL ──────────────────────
            preview_status, preview_url, preview_resp = _bi_preview_url(
                token, training_id, classroom_id, 1,
            )
            assert preview_status == 200, (
                f"Preview URL request failed: expected 200, got {preview_status}. "
                f"Response: {preview_resp}"
            )
            assert preview_url is not None, (
                f"No preview URL in response: {preview_resp}"
            )
            assert "/preview/bi/" in preview_url, (
                f"Preview URL does not contain /preview/bi/: {preview_url}"
            )

            # ── Step 6: Save canvas again (idempotent update) ─
            canvas_v2 = {
                "components": [
                    {"id": "comp-1", "type": "bar_chart", "title": "Sales Overview v2"},
                    {"id": "comp-2", "type": "pie_chart", "title": "Category Split v2"},
                    {"id": "comp-3", "type": "line_chart", "title": "Trend"},
                ],
            }
            save2_status, scene_id_2, save2_resp = _bi_save(
                token, training_id, classroom_id, 1, canvas_v2,
            )
            assert save2_status == 200, (
                f"Second BI save failed: expected 200, got {save2_status}. "
                f"Response: {save2_resp}"
            )
            assert scene_id_2 is not None, (
                f"Second BI save returned no scene_id: {save2_resp}"
            )
            assert scene_id_1 == scene_id_2, (
                f"Scene ID changed between saves: first={scene_id_1}, "
                f"second={scene_id_2}. Expected update-in-place, not new creation."
            )

            # ── Step 7: Get BI data ──────────────────────────
            bi_data_status, bi_data_resp = _bi_data(token, training_id)
            assert bi_data_status in (200, 404), (
                f"BI data request failed: expected 200 or 404, got {bi_data_status}. "
                f"Response: {bi_data_resp}"
            )
            # 200 means datasets exist; 404 means no datasets configured yet
            # (both are acceptable for a freshly created training)

        finally:
            # ── Cleanup ──────────────────────────────────────
            _delete_training(token, training_id)
            _delete_classroom(token, classroom_id)
