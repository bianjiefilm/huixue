import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC05_MODULE", "student_dc05"))


def _assert_request(request, api_url, bearer_token, page, page_size):
    assert request["method"] == "GET"
    assert request["url"] == api_url
    assert request["headers"] == {
        "Authorization": bearer_token,
        "Accept": "application/json",
    }
    assert request["params"] == {"page": page, "page_size": page_size}
    assert request["timeout_seconds"] == 10
    assert request["retry"] == {"max_attempts": 3, "backoff_seconds": 1}


@pytest.mark.parametrize(
    ("api_url", "bearer_token", "page", "page_size"),
    [
        ("https://api.example.com/data", "Bearer sk_test_123456", 1, 100),
        ("https://api.example.com/users", "Bearer sk_test_789012", 2, 50),
        ("https://api.example.com/posts", "Bearer sk_live_abc123", 5, 20),
        ("https://api.example.com/orders", "Bearer sk_live_xyz789", 1, 10),
        ("https://api.example.com/products", "Bearer sk_prod_def456", 3, 200),
        ("https://api.example.com/comments", "Bearer sk_prod_ghi789", 4, 25),
        ("http://localhost:8000/api/items", "Bearer local_token", 1, 1),
        ("https://portal.example.cn/openapi/v1/events", "Bearer cn_token_001", 9, 500),
        ("https://demo.example/search?q=python", "Bearer token-with-query", 7, 75),
    ],
)
def test_build_api_collection_request(api_url, bearer_token, page, page_size):
    _assert_request(_student().build_api_collection_request(api_url, bearer_token, page, page_size), api_url, bearer_token, page, page_size)


def test_rejects_non_string_url():
    with pytest.raises(TypeError):
        _student().build_api_collection_request(None, "Bearer sk_test_123456")


def test_rejects_non_bearer_token():
    with pytest.raises(ValueError):
        _student().build_api_collection_request("https://api.example.com/data", "sk_test_123456")


def test_rejects_bad_url_scheme():
    with pytest.raises(ValueError):
        _student().build_api_collection_request("ftp://api.example.com/data", "Bearer sk_test_123456")


def test_rejects_zero_page():
    with pytest.raises(ValueError):
        _student().build_api_collection_request("https://api.example.com/data", "Bearer sk_test_123456", 0, 100)


def test_rejects_oversized_page_size():
    with pytest.raises(ValueError):
        _student().build_api_collection_request("https://api.example.com/data", "Bearer sk_test_123456", 1, 501)


def test_rejects_non_integer_page_size():
    with pytest.raises(TypeError):
        _student().build_api_collection_request("https://api.example.com/data", "Bearer sk_test_123456", 1, "100")
