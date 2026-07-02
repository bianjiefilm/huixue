"""YARN 资源管理与调度 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""


def compute_yarn_container_count(total_memory_gb: int,
                                 container_memory_gb: int) -> int:
    """
    可分配 container 数 = floor(total_memory / container_memory)。

    Args:
        total_memory_gb: 集群总内存 GB, > 0。
        container_memory_gb: 单 container 内存 GB, > 0。

    Returns:
        int: container 数。

    Raises:
        ValueError, TypeError。
    """
    pass


def is_resource_request_valid(req_mem_gb: int, req_cpu: int,
                              max_mem_gb: int = 32, max_cpu: int = 16) -> bool:
    """
    1 <= req_mem <= max_mem AND 1 <= req_cpu <= max_cpu。

    Args:
        req_mem_gb, req_cpu: 请求资源。
        max_mem_gb, max_cpu: 上限, 默认 32 / 16。

    Returns:
        bool。

    Raises:
        TypeError: 不是 int。
    """
    pass


def assign_yarn_queue(priority: int) -> str:
    """
    priority >= 8 → 'production'
    4 <= priority < 8 → 'default'
    priority < 4 → 'low'

    Args:
        priority: 整数。

    Returns:
        str: 队列名。

    Raises:
        TypeError: 不是 int。
    """
    pass


def compute_fair_share_for_job(job_weight: int, total_weights: int,
                               total_resources: int) -> int:
    """
    公平分配 = floor(total_resources * job_weight / total_weights)。

    Args:
        job_weight, total_weights: > 0。
        total_resources: >= 0。

    Returns:
        int: 该 job 份额。

    Raises:
        ValueError, TypeError。
    """
    pass
