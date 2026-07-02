"""HDFS 分布式文件系统 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
import math


def compute_hdfs_block_count(file_size_bytes: int,
                             block_size_bytes: int = 134217728) -> int:
    """
    HDFS block 数 = ceil(file_size / block_size)。
    默认 block_size = 128 MB。

    Args:
        file_size_bytes: 文件字节, >= 0。
        block_size_bytes: block 字节, > 0。

    Returns:
        int: block 数 (file=0 → 0)。

    Raises:
        ValueError: 输入非法。
        TypeError: 不是 int。
    """
    pass


def compute_storage_with_replication(file_size_bytes: int,
                                     replication: int = 3) -> int:
    """
    实际存储 = file_size * replication。

    Args:
        file_size_bytes: >= 0。
        replication: 默认 3, >= 1。

    Returns:
        int: 占用字节。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_block_size_valid(block_size_bytes: int) -> bool:
    """
    block_size 合法性: ∈ [1 MB, 1 GB] 且为 2 的幂。

    Args:
        block_size_bytes: 待校验字节数。

    Returns:
        bool。

    Raises:
        TypeError: 不是 int。
    """
    pass


def compute_namenode_metadata_size(num_files: int,
                                   bytes_per_file: int = 150) -> int:
    """
    NameNode 元数据内存 = num_files * bytes_per_file。

    Args:
        num_files: >= 0。
        bytes_per_file: > 0, 默认 150。

    Returns:
        int: 总字节。

    Raises:
        ValueError, TypeError。
    """
    pass
