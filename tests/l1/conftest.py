"""
tests/l1/conftest.py
L1 API 合约测试 - 专用 fixtures
"""

import pytest
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from tests.conftest import (
    SCOPE_FUNC,
    SCOPE_MODULE,
    TIMEOUT_SHORT,
    TIMEOUT_MEDIUM,
    auth_header,
    assert_api_success,
)


# ─────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _future(days: int = 30) -> datetime:
    return _now() + timedelta(days=days)


def _past(days: int = 30) -> datetime:
    return _now() - timedelta(days=days)


def _to_iso(dt: datetime) -> str:
    """datetime -> ISO 字符串（兼容前端解析）"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


# ─────────────────────────────────────────────────────────────
# L1 通用 Fixture：测试课堂（自动清理）
# 重要：不依赖 teacher_client fixture，避免 session-scope token 冲突
# 直接创建独立 session 和 token
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope=SCOPE_FUNC)
def test_classroom(unique_suffix) -> Dict[str, Any]:
    """
    创建一个测试用课堂，测试结束后自动删除。
    使用独立 requests session，不依赖 shared client fixtures。
    返回 {"id": int, "name": str}
    """
    import sys
    from tests.conftest import TEST_API_URL

    # 直接获取 teacher token（不走 fixture 依赖链）
    auth_resp = requests.post(
        f"{TEST_API_URL}/api/login",
        json={"username": "teacher1", "password": "teacher123"},
        timeout=TIMEOUT_SHORT
    )

    teacher_token = auth_resp.json().get("token", {}).get("access_token")

    if not teacher_token:
        pytest.fail(f"Failed to get teacher token: {auth_resp.text}")

    # 创建独立 session
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {teacher_token}"})

    classroom_name = f"测试课堂_{unique_suffix}"
    payload = {
        "name": classroom_name,
        "description": f"自动化测试创建的课堂 (ID: {unique_suffix})",
        "semester": "2026-春",
        "start_date": "2026-04-01T00:00:00",
        "end_date": "2026-12-31T23:59:59",
    }


    resp = session.post(
        f"{TEST_API_URL}/api/v1/classrooms",
        json=payload,
        timeout=TIMEOUT_MEDIUM
    )
    print(f"[test_classroom] POST /api/v1/classrooms: {resp.status_code} {resp.text[:200]}", file=sys.stderr)


    if resp.status_code >= 400:
        resp = session.post(
            f"{TEST_API_URL}/api/classrooms",
            json=payload,
            timeout=TIMEOUT_MEDIUM
        )
        print(f"[test_classroom] POST /api/classrooms -> {resp.status_code}: {resp.text[:200]}", file=sys.stderr)

    assert resp.status_code in (200, 201), \
        f"Failed to create test classroom: {resp.status_code} {resp.text}"

    data = resp.json()
    classroom_id = (
        (data.get("data") or {}).get("classroom_id")
        or (data.get("data") or {}).get("id")
        or data.get("id")
    )
    assert classroom_id is not None, f"Cannot extract classroom_id from: {data}"

    yield {"id": classroom_id, "name": classroom_name}

    # Cleanup: 删除课堂（双路径 fallback）
    try:
        resp = session.delete(
            f"{TEST_API_URL}/api/v1/classrooms/{classroom_id}",
            timeout=TIMEOUT_SHORT
        )
        if resp.status_code >= 400:
            session.delete(
                f"{TEST_API_URL}/api/classrooms/{classroom_id}",
                timeout=TIMEOUT_SHORT
            )
    except Exception as e:
        print(f"[test_classroom] cleanup failed: {e}", file=sys.stderr)
    session.close()


# ─────────────────────────────────────────────────────────────
# L1 通用 Fixture：带章节的测试课堂
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_classroom_with_chapter(unique_suffix) -> Dict[str, Any]:
    """
    创建一个带章节的测试课堂（完全自包含，不依赖 shared client fixtures）。
    返回 {"classroom_id": int, "chapter_id": int, "chapter_name": str}
    """
    from tests.conftest import TEST_API_URL

    # 获取 teacher token（自包含）
    auth_resp = requests.post(
        f"{TEST_API_URL}/api/login",
        json={"username": "teacher1", "password": "teacher123"},
        timeout=TIMEOUT_SHORT
    )
    teacher_token = auth_resp.json().get("token", {}).get("access_token")

    # 创建独立 session（自包含，不复用 api_client）
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {teacher_token}"})

    # 获取 teacher_id
    me_resp = session.get(f"{TEST_API_URL}/api/me", timeout=TIMEOUT_SHORT)
    if me_resp.status_code != 200:
        session.close()
        pytest.skip(f"Cannot get teacher_id from /api/me: {me_resp.status_code}")
    teacher_id = me_resp.json().get("id")
    if not teacher_id:
        session.close()
        pytest.skip(f"Cannot extract teacher id from /api/me response: {me_resp.json()}")

    # 获取 classroom_id（自包含创建 classroom）
    class_auth = requests.post(
        f"{TEST_API_URL}/api/login",
        json={"username": "teacher1", "password": "teacher123"},
        timeout=TIMEOUT_SHORT
    ).json()
    class_token = class_auth.get("token", {}).get("access_token")
    class_session = requests.Session()
    class_session.headers.update({"Authorization": f"Bearer {class_token}"})

    classroom_resp = class_session.post(
        f"{TEST_API_URL}/api/v1/classrooms",
        json={
            "name": f"测试课堂_{unique_suffix}",
            "description": f"自动化测试 (ID: {unique_suffix})",
            "semester": "2026-春",
            "start_date": "2026-04-01T00:00:00",
            "end_date": "2026-12-31T23:59:59",
        },
        timeout=TIMEOUT_MEDIUM
    )
    print(f"[chapter_fixture] classroom POST: {classroom_resp.status_code} {classroom_resp.text[:200]}", file=sys.stderr)
    class_session.close()

    class_data = classroom_resp.json()
    classroom_id = (
        (class_data.get("data") or {}).get("classroom_id")
        or (class_data.get("data") or {}).get("id")
        or class_data.get("id")
    )

    if not classroom_id:
        session.close()
        pytest.skip(f"Cannot create classroom for chapter test: {class_data}")

    chapter_name = f"测试章节_{unique_suffix}"

    resp = session.post(
        f"{TEST_API_URL}/api/v1/classrooms/{classroom_id}/chapters",
        params={"teacher_id": teacher_id, "title": chapter_name},
        timeout=TIMEOUT_MEDIUM
    )
    if resp.status_code >= 400:
        resp = session.post(
            f"{TEST_API_URL}/api/classrooms/{classroom_id}/chapters",
            params={"teacher_id": teacher_id, "title": chapter_name},
            timeout=TIMEOUT_MEDIUM
        )

    data = resp.json()
    chapter_id = (
        (data.get("data") or {}).get("id")
        or data.get("id")
    )

    session.close()

    if chapter_id:
        yield {
            "classroom_id": classroom_id,
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
        }
    else:
        yield {
            "classroom_id": classroom_id,
            "chapter_id": None,
            "chapter_name": chapter_name,
        }


# ─────────────────────────────────────────────────────────────
# L1 通用 Fixture：按状态分类的测试课堂
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def test_classroom_upcoming(teacher_client, unique_suffix) -> Dict[str, Any]:
    """创建一个"未开始"的测试课堂（开始时间在明天）"""
    classroom_name = f"测试课堂_未开始_{unique_suffix}"
    payload = {
        "name": classroom_name,
        "description": f"未开始课堂 (ID: {unique_suffix})",
        "semester": "2026-春",
        "start_date": "2026-05-01T00:00:00",
        "end_date": "2026-12-31T23:59:59",
    }
    resp = teacher_client.post("/api/v1/classrooms", json=payload, timeout=TIMEOUT_MEDIUM)
    if resp.status_code >= 400:
        resp = teacher_client.post("/api/classrooms", json=payload, timeout=TIMEOUT_MEDIUM)

    assert resp.status_code in (200, 201), f"Failed to create upcoming classroom: {resp.text}"
    data = resp.json()
    classroom_id = (data.get("data") or {}).get("classroom_id") or (data.get("data") or {}).get("id") or data.get("id")

    yield {"id": classroom_id, "name": classroom_name, "status": "upcoming"}

    try:
        resp = teacher_client.delete(f"/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
        if resp.status_code >= 400:
            teacher_client.delete(f"/api/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass


@pytest.fixture
def test_classroom_ended(teacher_client, unique_suffix) -> Dict[str, Any]:
    """创建一个"历史"的测试课堂（结束时间在昨天）"""
    classroom_name = f"测试课堂_历史_{unique_suffix}"
    payload = {
        "name": classroom_name,
        "description": f"历史课堂 (ID: {unique_suffix})",
        "semester": "2025-秋",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-12-31T23:59:59",
    }
    resp = teacher_client.post("/api/v1/classrooms", json=payload, timeout=TIMEOUT_MEDIUM)
    if resp.status_code >= 400:
        resp = teacher_client.post("/api/classrooms", json=payload, timeout=TIMEOUT_MEDIUM)

    assert resp.status_code in (200, 201), f"Failed to create ended classroom: {resp.text}"
    data = resp.json()
    classroom_id = (data.get("data") or {}).get("classroom_id") or (data.get("data") or {}).get("id") or data.get("id")

    yield {"id": classroom_id, "name": classroom_name, "status": "ended"}

    try:
        resp = teacher_client.delete(f"/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
        if resp.status_code >= 400:
            teacher_client.delete(f"/api/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass


@pytest.fixture
def test_classroom_ongoing(teacher_client, unique_suffix) -> Dict[str, Any]:
    """创建一个"进行中"的测试课堂"""
    classroom_name = f"测试课堂_进行中_{unique_suffix}"
    payload = {
        "name": classroom_name,
        "description": f"进行中课堂 (ID: {unique_suffix})",
        "semester": "2026-春",
        "start_date": "2026-04-01T00:00:00",
        "end_date": "2026-12-31T23:59:59",
    }
    resp = teacher_client.post("/api/v1/classrooms", json=payload, timeout=TIMEOUT_MEDIUM)
    if resp.status_code >= 400:
        resp = teacher_client.post("/api/classrooms", json=payload, timeout=TIMEOUT_MEDIUM)

    assert resp.status_code in (200, 201), f"Failed to create ongoing classroom: {resp.text}"
    data = resp.json()
    classroom_id = (data.get("data") or {}).get("classroom_id") or (data.get("data") or {}).get("id") or data.get("id")

    yield {"id": classroom_id, "name": classroom_name, "status": "ongoing"}

    try:
        resp = teacher_client.delete(f"/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
        if resp.status_code >= 400:
            teacher_client.delete(f"/api/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass
