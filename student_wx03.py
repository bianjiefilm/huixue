"""重复数据识别与去重 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def is_exact_duplicate(row_a: List, row_b: List) -> bool:
    """
    判断两条记录是否完全相同 (元素逐个 == 比较)。

    Args:
        row_a, row_b: 两个 list。

    Returns:
        bool: 长度相同且元素全相同 → True; 否则 False。

    Raises:
        TypeError: 输入不是 list。
    """
    pass


def count_duplicate_rows(rows: List[List]) -> int:
    """
    统计重复行数 = 总行数 - 不同行种数。
    例: [A, A, B, C, A] → 5 - 3 = 2。

    Args:
        rows: list[list]。

    Returns:
        int: 重复行数 (>= 0)。

    Raises:
        TypeError: rows 不是 list 或元素不是 list。
    """
    pass


def dedup_preserve_first(rows: List[List]) -> List[List]:
    """
    去重保留首次出现, 顺序不变。

    Args:
        rows: list[list]。

    Returns:
        list[list]: 去重后, 按原顺序保留首次出现的行。

    Raises:
        TypeError: 输入类型错误。
    """
    pass


def dedup_keep_last(rows: List[List]) -> List[List]:
    """
    去重保留末次出现, 顺序按"最后一次出现的位置"排序。
    例: [A, B, A, C, B] → [A, C, B] (A 末次在 idx 2, C 在 idx 3, B 在 idx 4)。

    Args:
        rows: list[list]。

    Returns:
        list[list]: 去重后保留每行末次出现版本, 按末次位置升序。

    Raises:
        TypeError: 输入类型错误。
    """
    pass
