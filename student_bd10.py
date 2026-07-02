"""Sqoop 数据迁移工具 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
import math


def compute_split_size(table_size_mb: int, num_mappers: int) -> int:
    """
    每 mapper 分片大小 = ceil(table_size / num_mappers)。

    Args:
        table_size_mb, num_mappers: > 0。

    Returns:
        int MB。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_incremental_import_valid(last_value: int, current_max: int) -> bool:
    """
    增量有效: current_max > last_value。

    Args:
        last_value, current_max: >= 0。

    Returns:
        bool。

    Raises:
        ValueError, TypeError。
    """
    pass


def compute_migration_time_seconds(rows: int, rows_per_sec: int = 10000) -> float:
    """
    迁移耗时 = rows / rows_per_sec。

    Args:
        rows: >= 0。
        rows_per_sec: > 0, 默认 10000。

    Returns:
        float 秒。

    Raises:
        ValueError, TypeError。
    """
    pass


def select_split_column_strategy(num_high_cardinality_cols: int) -> str:
    """
    >= 1 → 'numeric_pk'; == 0 → 'manual'。

    Args:
        num_high_cardinality_cols: >= 0。

    Returns:
        str。

    Raises:
        ValueError, TypeError。
    """
    pass
