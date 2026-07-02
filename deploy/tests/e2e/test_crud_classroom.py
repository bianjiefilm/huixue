"""
Block 3: CRUD闭环 — 课堂创建→验证→删除
验证教师能完成课堂生命周期管理。
"""
import requests
import uuid
from datetime import datetime, timedelta
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_classroom_create_read_delete(teacher_token):
    """课堂CRUD闭环：创建→读取→删除"""
    headers = {"Authorization": f"Bearer {teacher_token}"}
    now = datetime.now()

    # CREATE — 包含所有必填字段
    create_resp = SESSION.post(
        f"{API_URL}/api/v1/classrooms",
        json={
            "name": f"TDD测试_{uuid.uuid4().hex[:8]}",
            "description": "自动化测试创建，测试结束后删除",
            "start_date": now.strftime("%Y-%m-%d"),
            "end_date": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    create_data = create_resp.json()
    assert create_data.get("code") == "0000", f"Create failed: {create_data}"
    classroom_id = create_data["data"].get("classroom_id") or create_data["data"].get("id")

    try:
        # READ
        read_resp = SESSION.get(
            f"{API_URL}/api/v1/classrooms/{classroom_id}",
            headers=headers,
            timeout=TIMEOUT,
        )
        read_data = read_resp.json()
        assert read_data.get("code") == "0000", f"Read failed: {read_data}"
        assert "TDD测试_" in read_data["data"]["name"]
    finally:
        # DELETE (cleanup)
        del_resp = SESSION.delete(
            f"{API_URL}/api/v1/classrooms/{classroom_id}",
            headers=headers,
            timeout=TIMEOUT,
        )
        assert del_resp.status_code < 500, f"Delete server error: {del_resp.text}"
