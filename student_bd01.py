"""Hadoop 概述与集群搭建 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
import math


def get_hadoop_component_role(component: str) -> str:
    """
    Hadoop 生态组件的角色映射:
      'hdfs'→'storage', 'mapreduce'→'compute', 'yarn'→'scheduling',
      'hive'→'data_warehouse', 'hbase'→'nosql', 'kafka'→'streaming',
      'sqoop'→'migration'

    Args:
        component: 组件名 (上述 7 个之一)。

    Returns:
        str: 角色名。

    Raises:
        ValueError: 未知组件。
        TypeError: 输入不是字符串。
    """
    pass


def compute_cluster_node_count(data_size_tb: float, per_node_tb: float,
                               replication: int = 3) -> int:
    """
    所需集群节点数 = ceil(data_size_tb * replication / per_node_tb)。

    Args:
        data_size_tb: 业务数据规模 (TB), > 0。
        per_node_tb: 单节点容量 (TB), > 0。
        replication: 副本因子, 默认 3, >= 1。

    Returns:
        int: 节点数 (>= 1)。

    Raises:
        ValueError: 输入非正。
        TypeError: 输入类型错误。
    """
    pass


def is_hadoop_safe_mode_ok(under_replicated_blocks: int,
                           threshold: int = 1000) -> bool:
    """
    判定是否可退出安全模式: under_replicated_blocks <= threshold → True。

    Args:
        under_replicated_blocks: 副本不足 block 数 (>= 0)。
        threshold: 阈值, 默认 1000, >= 0。

    Returns:
        bool: True 若可退出。

    Raises:
        ValueError: 输入负数。
        TypeError: 输入不是 int。
    """
    pass


def get_hadoop_default_port(service: str) -> int:
    """
    Hadoop 服务默认端口:
      'namenode'→9000, 'datanode'→9866, 'namenode_ui'→9870,
      'resourcemanager'→8088, 'jobhistory'→19888

    Args:
        service: 服务名 (上述 5 个之一)。

    Returns:
        int: 端口号。

    Raises:
        ValueError: 未知服务。
        TypeError: 输入不是字符串。
    """
    pass
