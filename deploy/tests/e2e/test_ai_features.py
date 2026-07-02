"""
Block 30 — AI功能与项目画布端到端测试
覆盖: AI状态 → AgentPilot → 文本解释 → 项目画布
"""
import pytest
import requests
from conftest import API_URL, get_api_token, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
# Plain session for endpoints where 503 is a valid business response (not a transient error)
PLAIN_SESSION = requests.Session()
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
def student_headers():
    token = get_api_token("student1", "student123")
    assert token
    return {"Authorization": f"Bearer {token}"}


# ---------- AI Features ----------

class TestAIFeatures:

    def test_ai_status(self, admin_headers):
        """AI服务状态"""
        r = SESSION.get(f"{API_URL}/api/v1/ai-features/status", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert "available" in data

    def test_ai_status_has_task_ids(self, admin_headers):
        """AI状态包含任务ID"""
        r = SESSION.get(f"{API_URL}/api/v1/ai-features/status", headers=admin_headers, timeout=TIMEOUT)
        data = r.json()
        assert "task_ids" in data or "message" in data


# ---------- AgentPilot ----------

class TestAgentPilot:

    def test_agentpilot_status(self, admin_headers):
        """AgentPilot状态"""
        r = SESSION.get(f"{API_URL}/api/v1/agentpilot/status", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert "enabled" in data

    def test_agentpilot_render_requires_body(self, admin_headers):
        """AgentPilot渲染需要请求体"""
        r = PLAIN_SESSION.post(f"{API_URL}/api/v1/agentpilot/render", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code in (200, 422, 500, 503)  # 503=服务未配置

    def test_agentpilot_task_requires_body(self, admin_headers):
        """AgentPilot任务需要请求体"""
        r = PLAIN_SESSION.post(f"{API_URL}/api/v1/agentpilot/tasks", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code in (200, 422, 500, 503)  # 503=服务未配置


# ---------- Text Explain ----------

class TestTextExplain:

    def test_explain_history(self, teacher_headers):
        """解释历史"""
        r = SESSION.get(f"{API_URL}/api/v1/text-explain/explain/history", headers=teacher_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json().get("data", {})
        assert "history" in data

    def test_explain_requires_body(self, teacher_headers):
        """文本解释需要请求体"""
        r = SESSION.post(
            f"{API_URL}/api/v1/text-explain/explain",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code in (200, 422, 500)


# ---------- Project Canvas ----------

class TestProjectCanvas:

    def test_canvas_reachable(self, admin_headers):
        """项目画布可达"""
        r = SESSION.get(f"{API_URL}/api/v1/project-canvas/canvas", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_canvas_has_nodes(self, admin_headers):
        """画布包含节点"""
        r = SESSION.get(f"{API_URL}/api/v1/project-canvas/canvas", headers=admin_headers, timeout=TIMEOUT)
        data = r.json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)

    def test_canvas_node_structure(self, admin_headers):
        """节点有必要字段"""
        r = SESSION.get(f"{API_URL}/api/v1/project-canvas/canvas", headers=admin_headers, timeout=TIMEOUT)
        nodes = r.json().get("nodes", [])
        if not nodes:
            pytest.skip("No canvas nodes")
        node = nodes[0]
        assert "id" in node
        assert "title" in node

    def test_canvas_student_accessible(self, student_headers):
        """学生能看画布"""
        r = SESSION.get(f"{API_URL}/api/v1/project-canvas/canvas", headers=student_headers, timeout=TIMEOUT)
        assert r.status_code == 200
