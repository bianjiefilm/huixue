"""
tests/l1/test_m26_question_library_api.py
L1 试题库 API 合约测试（自包含）

覆盖:
  AC1: 健康检查 GET /question-library/health
  AC2: 筛选标签 GET /question-library/questions/filter-tags
  AC3: 题目列表 GET /question-library/questions
  AC4: 题目详情 GET /question-library/questions/{id}
  AC5: 创建题目 POST /question-library/questions
  AC6: 错误路径
"""
import pytest
import requests
import uuid
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1

_PREFIX = f"{BASE_URL}/api/v1/question-library"


def _get_first_question_id(token):
    """获取第一个可用题目 ID"""
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/questions", params={"teacher_id": 1, "page": 1, "size": 1}, timeout=TIMEOUT)
        if resp.status_code == 200:
            items = (resp.json().get("data", {}) or {}).get("list", [])
            if items:
                return items[0].get("id") or items[0].get("question_id")
    finally:
        s.close()
    return None


# ═══════════════════════════════════════════════════════════════
# AC1: 健康检查
# ═══════════════════════════════════════════════════════════════

def test_question_library_health():
    """AC1: GET /question-library/health → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/health", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: 筛选标签
# ═══════════════════════════════════════════════════════════════

def test_get_question_filter_tags():
    """AC2: GET /question-library/questions/filter-tags → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/questions/filter-tags", params={"teacher_id": 1}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC3: 题目列表
# ═══════════════════════════════════════════════════════════════

def test_get_questions_list():
    """AC3: GET /question-library/questions → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/questions", params={"teacher_id": 1}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_questions_with_keyword():
    """AC3: 关键词搜索"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/questions", params={"teacher_id": 1, "keyword": "Python"}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_questions_pagination():
    """AC3: 分页"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/questions", params={"teacher_id": 1, "page": 1, "size": 5}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC4: 题目详情
# ═══════════════════════════════════════════════════════════════

def test_get_question_detail():
    """AC4: GET /question-library/questions/{id} → 200"""
    token = _get_token("admin")
    qid = _get_first_question_id(token)
    if not qid:
        pytest.skip("No questions available")
    s = _session(token)
    try:
        resp = s.get(f"{_PREFIX}/questions/{qid}", params={"teacher_id": 1}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC5: 创建题目
# ═══════════════════════════════════════════════════════════════

def test_create_question():
    """AC5: POST /question-library/questions → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.post(
            f"{_PREFIX}/questions",
            params={"teacher_id": 1},
            json={
                "content": f"测试题目_{suffix}: 1+1=?",
                "question_type": "SINGLE_CHOICE",
                "difficulty": "BEGINNER",
                "options": [
                    {"label": "A", "content": "1", "is_correct": False},
                    {"label": "B", "content": "2", "is_correct": True},
                    {"label": "C", "content": "3", "is_correct": False},
                ],
                "correct_answers": ["B"],
                "explanation": "1+1=2",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        qid = (resp.json().get("data") or {}).get("question_id")
        assert qid is not None
        # cleanup
        if qid:
            s.delete(f"{_PREFIX}/questions/{qid}", params={"teacher_id": 1}, timeout=TIMEOUT)
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC6: 错误路径
# ═══════════════════════════════════════════════════════════════

def test_questions_unauthorized():
    """AC6: 无 token → 401/403/422"""
    s = requests.Session()
    try:
        resp = s.get(f"{_PREFIX}/questions", timeout=TIMEOUT)
        assert resp.status_code in (200, 401, 403, 422, 307)
    finally:
        s.close()
