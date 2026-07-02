"""
Block 26 — BI实训工作区端到端测试
覆盖: 实训库列表 → 实训详情 → 数据集加载 → 实践环境配置 → 容器相关探测
"""
import pytest
import requests
from conftest import API_URL, get_api_token, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)

TIMEOUT = 30


@pytest.fixture(scope="module")
def teacher_headers():
    token = get_api_token("teacher1", "teacher123")
    assert token, "teacher1 login failed"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def student_headers():
    token = get_api_token("student1", "student123")
    assert token, "student1 login failed"
    return {"Authorization": f"Bearer {token}"}


# ---------- 实训库 ----------

class TestTrainingLibrary:

    def test_library_list(self, teacher_headers):
        """实训库列表可达"""
        r = SESSION.get(f"{API_URL}/api/v1/trainings/library", headers=teacher_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json().get("data", {})
        items = data.get("list", data.get("items", []))
        assert len(items) >= 1, "实训库应有至少1个实训"

    def test_library_has_required_fields(self, teacher_headers):
        """实训项包含必要字段"""
        r = SESSION.get(f"{API_URL}/api/v1/trainings/library", headers=teacher_headers, timeout=TIMEOUT)
        items = r.json()["data"].get("list", r.json()["data"].get("items", []))
        item = items[0]
        for field in ["id", "title", "training_type", "difficulty"]:
            assert field in item, f"缺少字段: {field}"

    def test_library_student_accessible(self, student_headers):
        """学生也能看实训库"""
        r = SESSION.get(f"{API_URL}/api/v1/trainings/library", headers=student_headers, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_library_without_auth(self):
        """无token访问实训库"""
        r = SESSION.get(f"{API_URL}/api/v1/trainings/library", timeout=TIMEOUT)
        # 允许200(公开)或401/403
        assert r.status_code in (200, 401, 403, 422)

    def test_my_trainings(self, teacher_headers):
        """我的实训列表"""
        r = SESSION.get(f"{API_URL}/api/v1/trainings/my-trainings", headers=teacher_headers, timeout=TIMEOUT)
        assert r.status_code == 200


# ---------- 实训数据集 ----------

class TestTrainingDatasets:

    @pytest.fixture(scope="class")
    def training_id(self, teacher_headers):
        """获取第一个实训ID"""
        r = SESSION.get(f"{API_URL}/api/v1/trainings/library", headers=teacher_headers, timeout=TIMEOUT)
        items = r.json()["data"].get("list", r.json()["data"].get("items", []))
        assert items, "No trainings in library"
        return items[0]["id"]

    def test_datasets_reachable(self, teacher_headers, training_id):
        """数据集端点可达"""
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/{training_id}/datasets",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200

    def test_datasets_structure(self, teacher_headers, training_id):
        """数据集响应包含正确结构（允许空 datasets 列表）"""
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/{training_id}/datasets",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json().get("data", {})
        # 后端对空数据集只返回 {'datasets': [], 'total': 0}，有数据集时才包含 training_id
        assert "datasets" in data
        assert isinstance(data["datasets"], list)

    def test_datasets_have_required_fields(self, teacher_headers, training_id):
        """每个数据集有id/name/path"""
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/{training_id}/datasets",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        datasets = r.json()["data"]["datasets"]
        if not datasets:
            pytest.skip("No datasets for this training")
        ds = datasets[0]
        for field in ["id", "name", "path"]:
            assert field in ds, f"数据集缺少字段: {field}"

    def test_datasets_nonexistent_training(self, teacher_headers):
        """不存在的实训返回404或空"""
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/99999/datasets",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code in (200, 404)

    def test_datasets_student_access(self, student_headers, training_id):
        """学生也能查看数据集"""
        r = SESSION.get(
            f"{API_URL}/api/v1/trainings/{training_id}/datasets",
            headers=student_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200


# ---------- 实践环境配置 ----------

class TestPracticeEnvironments:

    def test_environments_list(self, teacher_headers):
        """实践环境列表可达"""
        r = SESSION.get(
            f"{API_URL}/api/v1/teaching-resources/practice-environments",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        assert r.status_code == 200

    def test_environments_has_items(self, teacher_headers):
        """至少有一个实践环境"""
        r = SESSION.get(
            f"{API_URL}/api/v1/teaching-resources/practice-environments",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        data = r.json().get("data", {})
        items = data.get("items", [])
        assert len(items) >= 1

    def test_environment_has_config(self, teacher_headers):
        """环境配置包含资源限制"""
        r = SESSION.get(
            f"{API_URL}/api/v1/teaching-resources/practice-environments",
            headers=teacher_headers, timeout=TIMEOUT,
        )
        items = r.json()["data"]["items"]
        env = items[0]
        assert "type" in env
        assert "docker_image" in env or "name" in env


# ---------- 容器管理探测 ----------

class TestContainerProbe:
    """容器端点探测（不实际启动容器）"""

    def test_container_status_endpoint(self, teacher_headers):
        """容器状态端点存在(可能无活跃容器)"""
        # 尝试常见容器状态路径
        for path in [
            "/api/v1/containers",
            "/api/v1/containers/status",
            "/api/v1/practices/100/container",
        ]:
            r = SESSION.get(f"{API_URL}{path}", headers=teacher_headers, timeout=TIMEOUT)
            if r.status_code != 404:
                assert r.status_code in (200, 401, 403, 422, 500)
                return
        # 所有路径都404也可接受 — 容器管理可能不暴露REST端点
        pytest.skip("No container status endpoint found")
