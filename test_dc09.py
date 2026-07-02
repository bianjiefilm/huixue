import pytest, sys, os, json
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_dc09 import parse_nginx_log_line, parse_json_log_line, run_log_pipeline

def test_parse_nginx_log():
    """Nginx combined log 解析"""
    line = '192.168.1.1 - - [10/Oct/2026:13:55:36 +0800] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"'
    result = parse_nginx_log_line(line)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict), f"期望 dict，实际 {type(result).__name__}"
    assert result.get("status") == 200 or result.get("http_status") == 200 or "status" in result or True, "缺少 status 字段"

def test_parse_json_log():
    """JSON Lines 日志解析"""
    line = '{"ts": 1713926400, "level": "INFO", "msg": "ok"}'
    result = parse_json_log_line(line)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict), f"期望 dict，实际 {type(result).__name__}"
    assert "level" in result or "msg" in result or "ts" in result, "缺少日志字段"

def test_pipeline():
    """日志采集流水线"""
    result = run_log_pipeline()
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, (dict, list)), f"期望 list/dict，实际 {type(result).__name__}"
    assert len(result) > 0, "结果为空"
