"""BD01 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_bd01 import (
    get_hadoop_component_role,
    compute_cluster_node_count,
    is_hadoop_safe_mode_ok,
    get_hadoop_default_port,
)


# F1: get_hadoop_component_role
def test_role_hdfs():
    assert get_hadoop_component_role("hdfs") == "storage"

def test_role_mapreduce():
    assert get_hadoop_component_role("mapreduce") == "compute"

def test_role_yarn():
    assert get_hadoop_component_role("yarn") == "scheduling"

def test_role_hive():
    assert get_hadoop_component_role("hive") == "data_warehouse"

def test_role_hbase():
    assert get_hadoop_component_role("hbase") == "nosql"

def test_role_kafka():
    assert get_hadoop_component_role("kafka") == "streaming"

def test_role_sqoop():
    assert get_hadoop_component_role("sqoop") == "migration"

def test_role_raises_on_unknown():
    with pytest.raises(ValueError):
        get_hadoop_component_role("unknown")

def test_role_raises_on_empty():
    with pytest.raises(ValueError):
        get_hadoop_component_role("")

def test_role_raises_on_non_string():
    with pytest.raises(TypeError):
        get_hadoop_component_role(123)


# F2: compute_cluster_node_count
def test_node_typical():
    """100TB, 10TB/node, R=3 → ceil(300/10) = 30"""
    assert compute_cluster_node_count(100.0, 10.0, 3) == 30

def test_node_partial_ceil():
    """95TB, 10TB/node, R=3 → ceil(285/10) = 29 (向上)"""
    assert compute_cluster_node_count(95.0, 10.0, 3) == 29

def test_node_default_replication():
    """default R=3"""
    assert compute_cluster_node_count(100.0, 10.0) == 30

def test_node_replication_1():
    """R=1: 100TB → 10 节点"""
    assert compute_cluster_node_count(100.0, 10.0, 1) == 10

def test_node_replication_2():
    """R=2: 100TB → 20 节点"""
    assert compute_cluster_node_count(100.0, 10.0, 2) == 20

def test_node_small_data():
    """1TB, 10TB/node, R=3 → ceil(3/10) = 1"""
    assert compute_cluster_node_count(1.0, 10.0, 3) == 1

def test_node_raises_on_zero_data():
    with pytest.raises(ValueError):
        compute_cluster_node_count(0, 10, 3)

def test_node_raises_on_zero_capacity():
    with pytest.raises(ValueError):
        compute_cluster_node_count(100, 0, 3)

def test_node_raises_on_non_numeric():
    with pytest.raises(TypeError):
        compute_cluster_node_count("100", 10, 3)


# F3: is_hadoop_safe_mode_ok
def test_safe_at_threshold():
    """1000 == 1000 → True (<=)"""
    assert is_hadoop_safe_mode_ok(1000) is True

def test_safe_above_threshold():
    """1500 > 1000 → False"""
    assert is_hadoop_safe_mode_ok(1500) is False

def test_safe_zero():
    """0 → True (boundary)"""
    assert is_hadoop_safe_mode_ok(0) is True

def test_safe_custom_threshold():
    """100, threshold=50 → False"""
    assert is_hadoop_safe_mode_ok(100, 50) is False

def test_safe_raises_on_negative():
    with pytest.raises(ValueError):
        is_hadoop_safe_mode_ok(-1)

def test_safe_raises_on_non_int():
    with pytest.raises(TypeError):
        is_hadoop_safe_mode_ok(500.0)


# F4: get_hadoop_default_port
def test_port_namenode():
    assert get_hadoop_default_port("namenode") == 9000

def test_port_datanode():
    assert get_hadoop_default_port("datanode") == 9866

def test_port_namenode_ui():
    assert get_hadoop_default_port("namenode_ui") == 9870

def test_port_resourcemanager():
    assert get_hadoop_default_port("resourcemanager") == 8088

def test_port_jobhistory():
    assert get_hadoop_default_port("jobhistory") == 19888

def test_port_raises_on_unknown():
    with pytest.raises(ValueError):
        get_hadoop_default_port("unknown_svc")

def test_port_raises_on_non_string():
    with pytest.raises(TypeError):
        get_hadoop_default_port(9000)
