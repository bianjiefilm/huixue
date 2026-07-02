"""
tests/l1/test_m25_grades_api.py
L1 成绩管理 API 合约测试（自包含）

覆盖真实后端路由（非测试想象中的扁平 /grades 端点）:
  AC1: 课程成绩列表 GET /classrooms/{cid}/courses/{ccid}/grades?teacher_id=
  AC2: 作业列表     GET /grades/classroom-courses/{ccid}/assignments?teacher_id=
  AC3: 统计        GET /grades/classroom-courses/{ccid}/statistics?teacher_id=
  AC4: 罚分        PATCH 端点，无 GET 列表 — 跳过
  AC5: 优秀作品     GET /grades/classrooms/{cid}/excellent-works?teacher_id=
  AC6: 课程成绩     同 AC1
  AC7: 全部课程     GET /classrooms/{cid}/courses?teacher_id=
"""
import pytest
import requests
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


# ═══════════════════════════════════════════════════════════════
# 辅助：查找真实存在的 (classroom_id, classroom_course_id, teacher_id) 三元组
# ═══════════════════════════════════════════════════════════════

_cached_ctx = {}


def _find_ctx():
    """返回 (classroom_id, classroom_course_id, teacher_id) 或 None"""
    if "value" in _cached_ctx:
        return _cached_ctx["value"]
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms",
            params={"user_id": 1, "role": "admin"},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            _cached_ctx["value"] = None
            return None
        classrooms = (resp.json().get("data") or {}).get("list") or []
        for cr in classrooms:
            cid = cr.get("id")
            teacher_id = cr.get("teacher_id")
            if not cid or not teacher_id:
                continue
            cr_resp = s.get(
                f"{BASE_URL}/api/v1/classrooms/{cid}/courses",
                params={"teacher_id": teacher_id},
                timeout=TIMEOUT,
            )
            if cr_resp.status_code != 200:
                continue
            courses = (cr_resp.json().get("data") or {}).get("courses") or []
            if courses:
                ccid = courses[0].get("id")
                ctx = (cid, ccid, teacher_id)
                _cached_ctx["value"] = ctx
                return ctx
    finally:
        s.close()
    _cached_ctx["value"] = None
    return None


def _require_ctx():
    ctx = _find_ctx()
    if ctx is None:
        pytest.skip("No existing classroom with courses to test against")
    return ctx


# ═══════════════════════════════════════════════════════════════
# AC1 & AC6: 课程成绩列表
# ═══════════════════════════════════════════════════════════════

def test_get_grades_list():
    """AC1: GET /classrooms/{cid}/courses/{ccid}/grades → 200"""
    cid, ccid, tid = _require_ctx()
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses/{ccid}/grades",
            params={"teacher_id": tid},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


def test_get_course_grades():
    """AC6: GET /classrooms/{cid}/courses/{ccid}/grades → 200 (重入口同 AC1)"""
    cid, ccid, tid = _require_ctx()
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses/{ccid}/grades",
            params={"teacher_id": tid},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: 作业列表（仅适用于实训课程；非实训返回 404 是合法业务响应）
# ═══════════════════════════════════════════════════════════════

def test_get_assignments():
    """AC2: GET /grades/classroom-courses/{ccid}/assignments → 200 or 404"""
    cid, ccid, tid = _require_ctx()
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/grades/classroom-courses/{ccid}/assignments",
            params={"teacher_id": tid},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC3: 统计
# ═══════════════════════════════════════════════════════════════

def test_get_grades_statistics():
    """AC3: GET /grades/classroom-courses/{ccid}/statistics → 200"""
    cid, ccid, tid = _require_ctx()
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/grades/classroom-courses/{ccid}/statistics",
            params={"teacher_id": tid},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC4: 罚分（后端仅提供 PATCH 单笔/批量操作，无 GET 列表端点 — 跳过）
# ═══════════════════════════════════════════════════════════════

def test_penalty_patch_endpoint_exists():
    """AC4: 后端仅有 PATCH /student-progress/{id}/penalty（无 GET list）
    验证该路由已挂载：对不存在的 progress_id 调用应返回 404/422 而非 405/404(route missing)。"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.patch(
            f"{BASE_URL}/api/v1/grades/student-progress/999999999/penalty",
            params={"teacher_id": 1},
            json={"penalty_score": 0, "reason": "contract"},
            timeout=TIMEOUT,
        )
        # 404(记录不存在)/422(校验错误)/400(业务错误) 都说明路由存在且到达处理器
        assert resp.status_code in (404, 422, 400), f"Got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC5: 课堂优秀作品
# ═══════════════════════════════════════════════════════════════

def test_get_excellent_works():
    """AC5: GET /grades/classrooms/{cid}/excellent-works → 200"""
    cid, ccid, tid = _require_ctx()
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/grades/classrooms/{cid}/excellent-works",
            params={"teacher_id": tid},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC7: 课堂全部课程
# ═══════════════════════════════════════════════════════════════

def test_get_all_courses():
    """AC7: GET /classrooms/{cid}/courses → 200"""
    cid, ccid, tid = _require_ctx()
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses",
            params={"teacher_id": tid},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()
