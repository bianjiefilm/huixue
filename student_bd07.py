"""Hive 数据仓库基础 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
import math


def compute_partition_count(rows: int, rows_per_partition: int) -> int:
    """
    Hive 分区数 = ceil(rows / rows_per_partition)。

    Args:
        rows: 总行数, >= 0。
        rows_per_partition: 单分区目标行数, > 0。

    Returns:
        int: 分区数 (rows=0 → 0)。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_partition_pruning_helpful(query_partitions: int,
                                 total_partitions: int,
                                 threshold: float = 0.5) -> bool:
    """
    剪枝有效: query_partitions / total_partitions < threshold。

    Args:
        query_partitions: 查询涉及分区数。
        total_partitions: 总分区数, > 0。
        threshold: 阈值 ∈ (0, 1), 默认 0.5。

    Returns:
        bool。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_data_warehouse_size(raw_size_gb: float, replication: int,
                                compression_ratio: float) -> float:
    """
    数仓存储 = raw_size * replication * compression_ratio。

    Args:
        raw_size_gb: 原始数据 GB, >= 0。
        replication: 副本因子, >= 1。
        compression_ratio: 压缩率 ∈ (0, 1]。

    Returns:
        float: 占用 GB。

    Raises:
        ValueError, TypeError。
    """
    pass


def get_hive_storage_format(use_case: str) -> str:
    """
    'analytical' → 'orc'
    'compatibility' → 'parquet'
    'simple' → 'textfile'

    Args:
        use_case: 用途名 (3 个之一)。

    Returns:
        str: 格式名。

    Raises:
        ValueError, TypeError。
    """
    pass
