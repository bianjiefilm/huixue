import math


def get_hadoop_component_role(component):
    if not isinstance(component, str):
        raise TypeError("component must be str")
    mapping = {
        "hdfs": "storage",
        "mapreduce": "compute",
        "yarn": "scheduling",
        "hive": "data_warehouse",
        "hbase": "nosql",
        "kafka": "streaming",
        "sqoop": "migration",
    }
    if component not in mapping:
        raise ValueError("unknown component")
    return mapping[component]


def compute_cluster_node_count(data_size_tb, node_capacity_tb, replication_factor=3):
    if not isinstance(data_size_tb, (int, float)) or not isinstance(node_capacity_tb, (int, float)):
        raise TypeError("sizes must be numeric")
    if data_size_tb <= 0 or node_capacity_tb <= 0 or replication_factor <= 0:
        raise ValueError("invalid capacity")
    return math.ceil(data_size_tb / node_capacity_tb * replication_factor)


def is_hadoop_safe_mode_ok(block_count, threshold=1000):
    if not isinstance(block_count, int) or not isinstance(threshold, int):
        raise TypeError("counts must be int")
    if block_count < 0 or threshold < 0:
        raise ValueError("counts must be non-negative")
    return block_count <= threshold


def get_hadoop_default_port(service):
    if not isinstance(service, str):
        raise TypeError("service must be str")
    ports = {
        "namenode": 9000,
        "datanode": 9866,
        "namenode_ui": 9870,
        "resourcemanager": 8088,
        "jobhistory": 19888,
    }
    if service not in ports:
        raise ValueError("unknown service")
    return ports[service]
