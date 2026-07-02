"""
Block 24: 并发与边界条件
验证并发请求、超大ID、负数ID、Unicode、溢出、分页边界。
"""
import concurrent.futures
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_concurrent_requests(teacher_token):
    """10个并发GET请求不应导致500"""
    def fetch(path):
        return SESSION.get(
            f"{API_URL}{path}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )

    paths = ["/api/v1/classrooms"] * 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(fetch, paths))
    for r in results:
        assert r.status_code != 500, f"Concurrent request got 500: {r.text[:200]}"
        assert r.status_code == 200


def test_large_id_not_500(teacher_token):
    """超大ID应返回404，不应500"""
    large_ids = [999999999, 2147483647]
    for lid in large_ids:
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms/{lid}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code != 500, f"Large ID {lid} caused 500: {r.text[:200]}"


def test_negative_id_not_500(teacher_token):
    """负数ID应返回404或422，不应500"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/-1",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Negative ID caused 500: {r.text[:200]}"


def test_unicode_in_search(teacher_token):
    """搜索参数含Unicode不应500"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"search": "测试🎓课堂"},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Unicode search caused 500: {r.text[:200]}"


def test_overflow_page_size(teacher_token):
    """超大page_size应被限制或拒绝，不应500"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"page_size": 999999},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"Overflow page_size caused 500: {r.text[:200]}"


def test_pagination_beyond_data(teacher_token):
    """请求远超数据量的页码应返回空列表，不应500"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        params={"page": 9999},
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code != 500, f"High page number caused 500: {r.text[:200]}"
    assert r.status_code == 200
