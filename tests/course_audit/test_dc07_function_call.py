import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC07_MODULE", "student_dc07"))


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Firefox/121.0",
]


def _expected(url, delay, index):
    return {
        "url": url,
        "headers": {
            "User-Agent": USER_AGENTS[index % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": url.rsplit("/", 1)[0] + "/",
            "Connection": "keep-alive",
        },
        "rate_limit": {"strategy": "fixed_delay", "delay_seconds": float(delay)},
        "session": {"enabled": True, "cookie_policy": "persist_between_requests"},
    }


@pytest.mark.parametrize(
    ("url", "delay", "index"),
    [
        ("https://example.com/news/article-1", 1.0, 0),
        ("https://example.com/news/article-2", 2.0, 1),
        ("https://example.com/news/article-3", 0.5, 2),
        ("https://example.com/news/article-4", 3.5, 3),
        ("https://example.com/news/article-5", 10, 4),
        ("http://localhost:8000/articles/1", 1.25, 5),
        ("https://portal.example.cn/data/page", 4, 6),
        ("https://site.example/search?q=python", 0.75, 7),
        ("https://news.example.org/section/item", 6, 8),
    ],
)
def test_build_anticrawl_request(url, delay, index):
    assert _student().build_anticrawl_request(url, delay, index) == _expected(url, delay, index)


def test_rejects_non_string_url():
    with pytest.raises(TypeError):
        _student().build_anticrawl_request(None, 1.0, 0)


def test_rejects_bad_url_scheme():
    with pytest.raises(ValueError):
        _student().build_anticrawl_request("ftp://example.com/data", 1.0, 0)


def test_rejects_too_fast_delay():
    with pytest.raises(ValueError):
        _student().build_anticrawl_request("https://example.com/news", 0.1, 0)


def test_rejects_too_slow_delay():
    with pytest.raises(ValueError):
        _student().build_anticrawl_request("https://example.com/news", 11, 0)


def test_rejects_non_numeric_delay():
    with pytest.raises(TypeError):
        _student().build_anticrawl_request("https://example.com/news", "1", 0)


def test_rejects_non_integer_user_agent_index():
    with pytest.raises(TypeError):
        _student().build_anticrawl_request("https://example.com/news", 1.0, 1.5)
