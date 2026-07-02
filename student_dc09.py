#!/usr/bin/env python3
"""Stage DC09: 日志格式解析与采集 — 学生模板"""

import re, json
from typing import Dict, List, Optional


def parse_nginx_log_line(line: str) -> Optional[Dict]:
    """
    解析一行 Nginx combined log 格式

    Args:
        line: Nginx combined log 行，如：
              '192.168.1.1 - - [10/Oct/2026:13:55:36 +0800] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"'

    Returns:
        dict: 包含 ip, time, request, status, size, referer, ua 字段
              解析失败返回 None
    """
    # 请补充代码
    pass


def parse_json_log_line(line: str) -> Optional[Dict]:
    """
    解析一行 JSON Lines 格式日志

    Args:
        line: JSON Lines 行，如 '{"ts": 1713926400, "level": "INFO", "msg": "ok"}'

    Returns:
        dict: 解析后的字典，失败返回 None
    """
    # 请补充代码
    pass


def run_log_pipeline() -> List[Dict]:
    """
    模拟日志采集流水线：
    1. 读取模拟的 Nginx 日志数据
    2. 解析每行
    3. 统计各状态码出现次数
    4. 返回统计结果列表

    Returns:
        List[Dict]: 每条解析结果 + 统计摘要
    """
    # 请补充代码
    pass
