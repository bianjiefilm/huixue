"""数据合并与去重 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Dict


def merge_inner_by_key(left: List[Dict], right: List[Dict], key: str) -> List[Dict]:
    """
    Inner join: 只保留两边都有 key 的记录。同 key 时, 字段合并 ({**l, **r}, 右覆盖左)。

    Args:
        left, right: list[dict]。
        key: 字段名。

    Returns:
        list[dict]: 合并结果, 顺序按左表外层 + 右表内层。

    Raises:
        ValueError: key 在左/右某条记录中不存在。
        TypeError: 输入类型错误。
    """
    pass


def merge_left_by_key(left: List[Dict], right: List[Dict], key: str) -> List[Dict]:
    """
    Left join: 保留所有左记录; 有匹配右记录则合并 ({**l, **r}); 无匹配则只保留左记录。

    Args:
        left, right: list[dict]。
        key: 字段名。

    Returns:
        list[dict]: 合并结果, 至少 len(left) 条。

    Raises:
        ValueError: key 在左/右某条记录中不存在。
        TypeError: 输入类型错误。
    """
    pass


def dedup_dicts_by_key(rows: List[Dict], key: str) -> List[Dict]:
    """
    按 key 字段去重, 保留首次出现的记录。

    Args:
        rows: list[dict]。
        key: 字段名。

    Returns:
        list[dict]: 去重后, 顺序保留首次出现。

    Raises:
        ValueError: key 在某条记录中不存在。
        TypeError: 输入类型错误。
    """
    pass


def compute_merge_size(left_n: int, right_n: int, common_n: int, mode: str) -> int:
    """
    简化模型预测合并结果大小:
      'inner' → common_n
      'left'  → left_n
      'right' → right_n
      'outer' → left_n + right_n - common_n

    Args:
        left_n, right_n: 两表大小 (>= 0)。
        common_n: 共同 key 数 (>= 0, <= min(left_n, right_n))。
        mode: 4 个之一。

    Returns:
        int: 预测结果大小。

    Raises:
        ValueError: 参数非法 / 未知 mode。
        TypeError: 输入不是 int / mode 不是 str。
    """
    pass
