"""HBase NoSQL 数据库 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict
import math


def design_row_key_with_salt(prefix: str, timestamp: int, salt_count: int) -> str:
    """
    带盐 row key: "{salt}-{prefix}-{timestamp}", salt = timestamp % salt_count。

    Args:
        prefix: 业务前缀, 非空。
        timestamp: 整数, >= 0。
        salt_count: 盐桶数, > 0。

    Returns:
        str。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_region_count(table_size_gb: float, region_size_gb: float = 10.0) -> int:
    """
    Region 数 = ceil(table_size / region_size)。

    Args:
        table_size_gb: > 0。
        region_size_gb: > 0, 默认 10。

    Returns:
        int (>= 1)。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_hot_row_key(prefix_counts: Dict[str, int], total: int,
                   threshold: float = 0.5) -> bool:
    """
    若任一 prefix count > total * threshold → True。

    Args:
        prefix_counts: dict[prefix, count]。
        total: > 0。
        threshold: ∈ (0, 1), 默认 0.5。

    Returns:
        bool。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_block_cache_hit_rate(total_reads: int, cache_hits: int) -> float:
    """
    命中率 = cache_hits / total_reads。

    Args:
        total_reads: > 0。
        cache_hits: 0 <= cache_hits <= total_reads。

    Returns:
        float ∈ [0.0, 1.0]。

    Raises:
        ValueError, TypeError。
    """
    pass
