"""HDFS 操作与 Block 调度 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def compute_data_locality_score(local_replicas: int, total_replicas: int) -> float:
    """
    数据本地性 = local_replicas / total_replicas。

    Args:
        local_replicas: >= 0。
        total_replicas: >= 1。

    Returns:
        float ∈ [0.0, 1.0]。

    Raises:
        ValueError: 输入非法。
        TypeError: 不是 int。
    """
    pass


def is_replication_factor_valid(replicas: int, datanodes: int) -> bool:
    """
    副本因子合法性: 1 <= replicas <= datanodes。

    Args:
        replicas, datanodes: 非负整数。

    Returns:
        bool。

    Raises:
        ValueError, TypeError。
    """
    pass


def count_blocks_to_re_replicate(replicas_per_block: List[int],
                                 target: int = 3) -> int:
    """
    计数副本数 < target 的 block 数。

    Args:
        replicas_per_block: 每 block 副本数 list。
        target: 目标副本, 默认 3。

    Returns:
        int: 不足 block 数。

    Raises:
        ValueError, TypeError。
    """
    pass


def assign_replicas_round_robin(num_replicas: int, num_racks: int) -> List[int]:
    """
    round-robin 把 num_replicas 个副本分到 num_racks 个机架。

    Args:
        num_replicas: >= 0。
        num_racks: >= 1。

    Returns:
        list[int]: 长度 num_replicas, 元素 ∈ [0, num_racks-1]。

    Raises:
        ValueError, TypeError。
    """
    pass
