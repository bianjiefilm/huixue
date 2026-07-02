"""HiveQL 查询与优化 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def compute_partition_pruning_set(filter_partitions: List[str],
                                  available_partitions: List[str]) -> List[str]:
    """
    返回 filter 与 available 的交集 (升序, 去重)。

    Args:
        filter_partitions, available_partitions: list[str]。

    Returns:
        list[str]: 实际扫描的分区。

    Raises:
        TypeError。
    """
    pass


def estimate_query_cost(rows_scanned: int, num_joins: int) -> int:
    """
    简化代价: rows * (joins + 1)。

    Args:
        rows_scanned, num_joins: >= 0。

    Returns:
        int: 代价。

    Raises:
        ValueError, TypeError。
    """
    pass


def should_use_broadcast_join(left_rows: int, right_rows: int,
                              broadcast_threshold: int = 1000000) -> str:
    """
    若 min(left, right) < threshold → 'broadcast'; 否则 → 'shuffle'。

    Args:
        left_rows, right_rows: > 0。
        broadcast_threshold: > 0, 默认 1M。

    Returns:
        str。

    Raises:
        ValueError, TypeError。
    """
    pass


def count_distinct_simple(values: List) -> int:
    """
    distinct 计数 = len(set(values))。

    Args:
        values: 任意 list。

    Returns:
        int: distinct 数。

    Raises:
        TypeError: 不是 list。
    """
    pass
