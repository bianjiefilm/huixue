"""大数据综合项目实战 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Dict


def validate_pipeline_input_schema(stages: List[Dict]) -> bool:
    """
    每 stage 必须含 'name' (str), 'tool' (str), 'output_size_gb' (>=0)。
    允许额外字段。

    Args:
        stages: list[dict]。

    Returns:
        bool: 全部满足 → True; 否则 False。空 list → True。

    Raises:
        TypeError: 输入不是 list / 元素不是 dict。
    """
    pass


def get_tool_for_purpose(purpose: str) -> str:
    """
    Purpose → 工具:
      'storage'→'hdfs', 'compute'→'mapreduce', 'scheduling'→'yarn',
      'sql'→'hive', 'nosql'→'hbase', 'streaming'→'kafka', 'migration'→'sqoop'

    Args:
        purpose: 7 个之一。

    Returns:
        str。

    Raises:
        ValueError: 未知。
        TypeError: 不是字符串。
    """
    pass


def compute_pipeline_total_size(stages: List[Dict]) -> float:
    """
    累加 output_size_gb。

    Args:
        stages: list[dict]。

    Returns:
        float。

    Raises:
        ValueError, TypeError。
    """
    pass


def combine_bd_pipeline_report(stages_done: int, stages_total: int,
                               errors: Dict[str, int]) -> Dict:
    """
    报告 dict (6 key):
      stages_done, stages_total, progress_ratio, errors, total_errors, is_success

    is_success = (progress_ratio == 1.0 AND total_errors == 0)。

    Args:
        stages_done, stages_total: 0 <= done <= total, total > 0。
        errors: dict[str, int] (>= 0)。

    Returns:
        dict。

    Raises:
        ValueError, TypeError。
    """
    pass
