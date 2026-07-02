import importlib
import pytest


CASES = [
    (
        "爬取一个静态 HTML 页面，获取所有新闻标题和链接，页面数量少于 10 个",
        "requests + BeautifulSoup",
    ),
    (
        "抓取一个需要登录后才能查看的页面，该页面内容通过 JavaScript 动态渲染",
        "Selenium",
    ),
    (
        "需要并发发送 1000 个 HTTP GET 请求到不同的 API 端点获取 JSON 数据",
        "httpx",
    ),
    (
        "爬取一个有 1000+ 页面的电商网站，每个页面结构相同，需要自动去重和请求调度",
        "Scrapy",
    ),
    (
        "分析一个 React 单页应用（SPA），需要拦截其内部 API 调用来获取数据",
        "Playwright",
    ),
    (
        "调用一个天气数据公开 API，获取未来 7 天的天气预报数据",
        "requests",
    ),
    ("   ", "manual_review"),
]


def _student():
    return importlib.import_module("student_dc01")


@pytest.mark.parametrize(("scenario", "expected"), CASES)
def test_recommend_collection_tool(scenario, expected):
    assert _student().recommend_collection_tool(scenario) == expected


def test_recommend_collection_tool_rejects_non_string():
    with pytest.raises(TypeError):
        _student().recommend_collection_tool({"source": "api"})
