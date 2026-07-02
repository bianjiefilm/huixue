"""编码与字符清洗 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""


def count_non_ascii(text: str) -> int:
    """
    统计 ord > 127 的字符数。

    Args:
        text: 任意字符串。

    Returns:
        int: 非 ASCII 字符数 (>= 0)。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass


def remove_control_chars(text: str) -> str:
    """
    删除所有 ord < 32 的控制字符, 但保留 TAB (9) 和 LF (10)。

    Args:
        text: 任意字符串。

    Returns:
        str: 清洗后的字符串。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass


def is_pure_ascii(text: str) -> bool:
    """
    是否全是 ASCII 字符 (ord <= 127, 含控制字符)。
    空字符串 → True (vacuously)。

    Args:
        text: 任意字符串。

    Returns:
        bool: True 若所有字符 ord 都 <= 127。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass


def has_utf8_bom(text: str) -> bool:
    """
    是否以 UTF-8 BOM (\\ufeff) 开头。
    空字符串 → False。

    Args:
        text: 任意字符串。

    Returns:
        bool: 第一个字符等于 \\ufeff → True。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass
