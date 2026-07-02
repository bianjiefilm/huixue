import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC11_MODULE", "content_orchestrator.stages_config.data_collection.student_dc11"))


NGINX_200 = '192.168.1.10 - - [01/May/2026:10:15:01 +0800] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"'
NGINX_404 = '10.0.0.8 - - [01/May/2026:10:16:02 +0800] "POST /api/login HTTP/1.1" 404 - "-" "curl/8"'
APACHE = '172.16.0.2 - - [01/May/2026:10:17:03 +0800] "GET /report HTTP/1.1" 500 2048 "-" "Mozilla/5.0"'
JSON_INFO = '{"ts":1,"level":"INFO","message":"started"}'
JSON_WARN = '{"ts":2,"level":"WARN","message":"slow request"}'
JSON_ERROR = '{"ts":3,"level":"ERROR","message":"failed"}'
SYSLOG = "<13>May  1 10:18:04 host-1 app[123]: service started"


PARSE_CASES = [
    (NGINX_200, {"type": "access", "ip": "192.168.1.10", "time": "01/May/2026:10:15:01 +0800", "method": "GET", "path": "/index.html", "status": 200, "size": 1024}),
    (NGINX_404, {"type": "access", "ip": "10.0.0.8", "time": "01/May/2026:10:16:02 +0800", "method": "POST", "path": "/api/login", "status": 404, "size": 0}),
    (APACHE, {"type": "access", "ip": "172.16.0.2", "time": "01/May/2026:10:17:03 +0800", "method": "GET", "path": "/report", "status": 500, "size": 2048}),
    (JSON_INFO, {"type": "json", "timestamp": 1, "level": "INFO", "message": "started"}),
    (SYSLOG, {"type": "syslog", "priority": 13, "timestamp": "May  1 10:18:04", "host": "host-1", "message": "app[123]: service started"}),
    ("not valid log", {"error": "invalid_log"}),
    ("", {"error": "invalid_log"}),
]


SUMMARY_CASES = [
    ([NGINX_200, NGINX_404, APACHE], {"status_counts": {"200": 1, "404": 1, "500": 1}, "level_counts": {}, "invalid": 0}),
    ([JSON_INFO, JSON_WARN, JSON_ERROR, "bad"], {"status_counts": {}, "level_counts": {"INFO": 1, "WARN": 1, "ERROR": 1}, "invalid": 1}),
    ([NGINX_200, JSON_INFO, "bad", NGINX_200], {"status_counts": {"200": 2}, "level_counts": {"INFO": 1}, "invalid": 1}),
]


@pytest.mark.parametrize(("line", "expected"), PARSE_CASES)
def test_parse_log_entry(line, expected):
    assert _student().parse_log_entry(line) == expected


@pytest.mark.parametrize(("lines", "expected"), SUMMARY_CASES)
def test_summarize_log_entries(lines, expected):
    assert _student().summarize_log_entries(lines) == expected


def test_parse_rejects_non_string_line():
    with pytest.raises(TypeError):
        _student().parse_log_entry(None)


def test_summary_rejects_non_list_lines():
    with pytest.raises(TypeError):
        _student().summarize_log_entries("not a list")
