import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC04_MODULE", "student_dc04"))


def _assert_valid_plan(plan, username, password, login_url):
    assert plan["login_url"] == login_url
    assert plan["credentials"] == {"username": username, "password": password}
    assert plan["browser"]["engine"] == "chromium"
    assert "--headless=new" in plan["browser"]["arguments"]
    assert "--disable-gpu" in plan["browser"]["arguments"]
    assert "--no-sandbox" in plan["browser"]["arguments"]
    assert plan["wait_strategy"]["type"] == "explicit"
    assert plan["wait_strategy"]["timeout_seconds"] >= 5
    assert 0 < plan["wait_strategy"]["poll_seconds"] <= 1
    locator_names = {item["name"] for item in plan["locators"]}
    locator_methods = {item["by"] for item in plan["locators"]}
    assert {"username", "password", "submit"} <= locator_names
    assert {"css", "xpath"} <= locator_methods
    assert "driver.quit" in plan["cleanup"]


@pytest.mark.parametrize(
    ("username", "password", "login_url"),
    [
        ("test_user", "test_pass", "https://httpbin.org/html"),
        ("alice", "S3cret!", "https://example.com/login"),
        ("中文用户", "复杂密码123", "http://demo.local/auth"),
        ("space_user", "pass with space", "https://site.example/sign-in?from=course"),
        ("api_reader", "token-like-password", "https://portal.example.cn/login"),
        ("user-01", "pw_01", "https://www.example.org/accounts/login"),
        ("robot", "p@ssw0rd", "http://127.0.0.1:8080/login"),
        ("qa_user", "qa_pass", "https://test.example.com/auth/login"),
        ("student", "student123", "https://tempo.example/classroom/login"),
    ],
)
def test_plan_dynamic_page_collection(username, password, login_url):
    _assert_valid_plan(_student().plan_dynamic_page_collection(username, password, login_url), username, password, login_url)


def test_rejects_blank_username():
    with pytest.raises(ValueError):
        _student().plan_dynamic_page_collection("", "test_pass", "https://httpbin.org/html")


def test_rejects_blank_password():
    with pytest.raises(ValueError):
        _student().plan_dynamic_page_collection("test_user", "   ", "https://httpbin.org/html")


def test_rejects_non_http_url():
    with pytest.raises(ValueError):
        _student().plan_dynamic_page_collection("test_user", "test_pass", "ftp://example.com/login")


def test_rejects_non_string_username():
    with pytest.raises(TypeError):
        _student().plan_dynamic_page_collection(None, "test_pass", "https://httpbin.org/html")


def test_rejects_non_string_url():
    with pytest.raises(TypeError):
        _student().plan_dynamic_page_collection("test_user", "test_pass", ["https://httpbin.org/html"])
