"""BD02 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd02 import (
    compute_hdfs_block_count,
    compute_storage_with_replication,
    is_block_size_valid,
    compute_namenode_metadata_size,
)


# F1: compute_hdfs_block_count (ceil(file/block))
def test_block_300mb():
    """300 MB / 128 MB → ceil(300/128) = 3"""
    assert compute_hdfs_block_count(300 * 1024 * 1024, 128 * 1024 * 1024) == 3

def test_block_just_over():
    """129 MB / 128 MB → 2"""
    assert compute_hdfs_block_count(129 * 1024 * 1024, 128 * 1024 * 1024) == 2

def test_block_default_blocksize():
    """default 128 MB"""
    assert compute_hdfs_block_count(300 * 1024 * 1024) == 3

def test_block_custom_64mb():
    """300 MB / 64 MB → 5"""
    assert compute_hdfs_block_count(300 * 1024 * 1024, 64 * 1024 * 1024) == 5

def test_block_zero_file():
    """0 文件 → 0 block (boundary)"""
    assert compute_hdfs_block_count(0) == 0

def test_block_raises_on_zero_blocksize():
    with pytest.raises(ValueError):
        compute_hdfs_block_count(100, 0)

def test_block_raises_on_negative_filesize():
    with pytest.raises(ValueError):
        compute_hdfs_block_count(-1)

def test_block_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_hdfs_block_count(100.0)


# F2: compute_storage_with_replication
def test_storage_default():
    """100 MB × 3 = 300 MB"""
    assert compute_storage_with_replication(100 * 1024 * 1024) == 300 * 1024 * 1024

def test_storage_replication_1():
    """100 × 1 = 100"""
    assert compute_storage_with_replication(100, 1) == 100

def test_storage_replication_5():
    """100 × 5 = 500"""
    assert compute_storage_with_replication(100, 5) == 500

def test_storage_large_file():
    """1 GB × 3 = 3 GB"""
    assert compute_storage_with_replication(1024 * 1024 * 1024) == 3 * 1024 * 1024 * 1024

def test_storage_raises_on_negative_replication():
    with pytest.raises(ValueError):
        compute_storage_with_replication(100, 0)

def test_storage_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_storage_with_replication(100.0)


# F3: is_block_size_valid (1 MB - 1 GB, power of 2)
def test_block_size_64mb_valid():
    """1 个 True 测试 (默认推荐值)"""
    assert is_block_size_valid(64 * 1024 * 1024) is True

def test_block_size_too_small():
    """< 1 MB"""
    assert is_block_size_valid(512 * 1024) is False

def test_block_size_too_big():
    """> 1 GB"""
    assert is_block_size_valid(2 * 1024 * 1024 * 1024) is False

def test_block_size_not_power_of_2():
    """100 MB 不是 2 的幂"""
    assert is_block_size_valid(100 * 1024 * 1024) is False

def test_block_size_raises_on_non_int():
    with pytest.raises(TypeError):
        is_block_size_valid(128.0)


# F4: compute_namenode_metadata_size
def test_meta_one_million():
    """100 万 × 150 = 1.5 亿字节"""
    assert compute_namenode_metadata_size(1000000) == 150000000

def test_meta_100_files():
    """100 × 150 = 15000"""
    assert compute_namenode_metadata_size(100) == 15000

def test_meta_custom_bytes():
    """100 × 200 = 20000"""
    assert compute_namenode_metadata_size(100, 200) == 20000

def test_meta_zero_files():
    """0 → 0 (boundary)"""
    assert compute_namenode_metadata_size(0) == 0

def test_meta_default_bytes():
    """default 150"""
    assert compute_namenode_metadata_size(50) == 7500

def test_meta_raises_on_negative_files():
    with pytest.raises(ValueError):
        compute_namenode_metadata_size(-1)

def test_meta_raises_on_zero_bytes():
    with pytest.raises(ValueError):
        compute_namenode_metadata_size(100, 0)

def test_meta_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_namenode_metadata_size(100.0)
