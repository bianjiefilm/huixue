"""MapReduce 分布式计算原理 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List
import math


def compute_map_task_count(file_sizes_bytes: List[int],
                           split_size_bytes: int = 134217728) -> int:
    """
    map 任务总数 = sum(ceil(file_i / split_size))。
    默认 split_size = 128 MB。

    Args:
        file_sizes_bytes: 文件大小列表 (字节), 元素 >= 0。
        split_size_bytes: 切片大小, > 0, 默认 128 MB。

    Returns:
        int: map 任务数。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_reduce_task_count(data_size_mb: int,
                              target_per_reduce_mb: int = 1024) -> int:
    """
    reduce 任务数 = max(1, ceil(data_size / target_per_reduce))。

    Args:
        data_size_mb: 数据规模 MB, >= 1。
        target_per_reduce_mb: 单 reducer 目标处理量 MB, > 0, 默认 1024。

    Returns:
        int: reduce 任务数 (>= 1)。

    Raises:
        ValueError, TypeError。
    """
    pass


def partition_by_hash(key: str, num_reducers: int) -> int:
    """
    确定性 hash 分区: sum(ord(c) for c in key) % num_reducers。

    Args:
        key: 字符串 (非空)。
        num_reducers: > 0。

    Returns:
        int: partition 索引 ∈ [0, num_reducers-1]。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_combinable_operation(op: str) -> bool:
    """
    判断聚合操作是否可用 combiner:
      'sum', 'max', 'min', 'count' → True
      'avg', 'median', 'distinct'  → False

    Args:
        op: 操作名。

    Returns:
        bool。

    Raises:
        ValueError: 未知操作。
        TypeError: 输入不是字符串。
    """
    pass
