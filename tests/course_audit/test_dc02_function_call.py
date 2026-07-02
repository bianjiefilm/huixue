import importlib
import os

import pytest


CASES = [
    ("http://httpbin.org/status/200", 200),
    ("http://httpbin.org/get", 200),
    ("http://httpbin.org/status/404", 404),
    ("http://httpbin.org/html", 200),
    ("http://httpbin.org/json", 200),
    ("http://httpbin.org/status/500", 500),
    ("http://httpbin.org/status/301", 301),
    ("http://httpbin.org/status/302", 302),
    ("http://httpbin.org/status/204", 204),
    ("http://httpbin.org/status/418", 418),
    ("http://httpbin.org/status/451", 451),
    ("http://httpbin.org/status/503", 503),
    ("http://httpbin.org/status/206", 206),
    ("http://httpbin.org/status/422", 422),
]


def _student():
    return importlib.import_module(os.environ.get("DC02_MODULE", "student_dc02"))


@pytest.mark.parametrize(("url", "expected"), CASES)
def test_parse_httpbin_status(url, expected):
    assert _student().parse_httpbin_status(url) == expected


def test_parse_httpbin_status_rejects_non_string():
    with pytest.raises(TypeError):
        _student().parse_httpbin_status(None)


def test_parse_httpbin_status_rejects_unknown_path():
    with pytest.raises(ValueError):
        _student().parse_httpbin_status("http://httpbin.org/anything")


def test_parse_httpbin_status_rejects_non_numeric_status():
    with pytest.raises(ValueError):
        _student().parse_httpbin_status("http://httpbin.org/status/not-found")
