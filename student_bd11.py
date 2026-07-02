"""Kafka 流数据平台 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Dict


def assign_consumer_partitions(consumers: List[str],
                               partitions: List[int]) -> Dict[str, List[int]]:
    """
    Round-robin 分配: partition[i] → consumers[i % len(consumers)]。
    每个 consumer 都有 entry, 无 partition 时空 list。

    Args:
        consumers: 非空 consumer ID 列表。
        partitions: partition ID 列表。

    Returns:
        dict[str, list[int]]。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_minimum_replication(fault_tolerance: int, num_brokers: int) -> int:
    """
    最小副本因子 = max(1, min(ft + 1, num_brokers))。
    若 ft + 1 > num_brokers → ValueError。

    Args:
        fault_tolerance: >= 0。
        num_brokers: >= 1。

    Returns:
        int (>= 1)。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_message_lag_critical(consumer_offset: int, log_end_offset: int,
                            threshold: int = 1000) -> bool:
    """
    lag = log_end - consumer_offset; lag > threshold → True。

    Args:
        consumer_offset, log_end_offset: >= 0, log_end >= consumer。
        threshold: > 0, 默认 1000。

    Returns:
        bool。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_throughput_bytes_per_sec(messages_per_sec: int,
                                     message_size_bytes: int) -> int:
    """
    吞吐 = messages_per_sec * message_size_bytes。

    Args:
        messages_per_sec, message_size_bytes: > 0。

    Returns:
        int 字节/秒。

    Raises:
        ValueError, TypeError。
    """
    pass
