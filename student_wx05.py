"""格式规范化 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Tuple


def normalize_phone_digits(phone: str) -> str:
    """
    去掉非数字字符, 保留所有数字。
    "138-0000-0000" → "13800000000"
    "+86 138 0000 0000" → "8613800000000"

    Args:
        phone: 任意字符串。

    Returns:
        str: 仅含数字字符。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass


def normalize_email_lower(email: str) -> str:
    """
    邮箱归一化: strip + lower。

    Args:
        email: 邮箱字符串。

    Returns:
        str: 小写无前后空白。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass


def is_valid_email_basic(email: str) -> bool:
    """
    最简邮箱校验: 含 '@' AND 含 '.' AND 非空。

    Args:
        email: 待校验字符串。

    Returns:
        bool: True 若合法。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass


def parse_simple_date_iso(s: str) -> Tuple[int, int, int]:
    """
    解析 ISO YYYY-MM-DD 字符串为 (year, month, day) 三元组。
    简化规则: 长度 == 10, 用 '-' 切 3 段, 每段为数字。
    不校验月份/天数范围。

    Args:
        s: 长度 10 的字符串, 形如 'YYYY-MM-DD'。

    Returns:
        (year, month, day)。

    Raises:
        ValueError: 长度不是 10 / 段数不是 3 / 段不是数字。
        TypeError: 输入不是字符串。
    """
    pass
