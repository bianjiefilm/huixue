"""数据清洗概述与流程 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def classify_value_status(value, valid_min: float, valid_max: float,
                          missing_marker=None) -> str:
    """
    分类单个值的状态:
      - 等于 missing_marker / None / 空字符串 → 'missing'
      - 数值且在 [valid_min, valid_max] 范围内 → 'valid'
      - 数值但超出范围 → 'out_of_range'

    Args:
        value: 待分类值。
        valid_min, valid_max: 有效数值范围 (闭区间)。
        missing_marker: 缺失值标记 (默认 None)。

    Returns:
        str: 'missing' / 'valid' / 'out_of_range' 三选一。

    Raises:
        TypeError: valid_min/valid_max 不是数值。
    """
    pass


def compute_quality_ratio(num_valid: int, num_total: int) -> float:
    """
    数据质量比率 = num_valid / num_total。

    Args:
        num_valid: 有效记录数 (>= 0)。
        num_total: 总记录数 (>= 1)。

    Returns:
        float: ∈ [0.0, 1.0]。

    Raises:
        ValueError: num_total <= 0 或 num_valid > num_total 或 num_valid < 0。
        TypeError: 输入不是 int。
    """
    pass


def get_cleaning_priority(step_name: str) -> int:
    """
    按标准清洗流水线返回步骤优先级 (1-5):
      missing      → 1
      duplicate    → 2
      outlier      → 3
      format       → 4
      consistency  → 5

    Args:
        step_name: 上述 5 个之一。

    Returns:
        int: 优先级序号 1-5。

    Raises:
        ValueError: 未知 step。
        TypeError: 输入不是字符串。
    """
    pass


def decide_drop_or_fill(num_missing: int, num_total: int,
                        threshold: float = 0.5) -> str:
    """
    给定 missing 数量与总数, 决定 drop 还是 fill:
      missing_ratio > threshold → 'drop'
      否则                       → 'fill'

    Args:
        num_missing, num_total: 非负整数, num_total >= 1。
        threshold: 阈值 ∈ (0, 1)。

    Returns:
        str: 'drop' 或 'fill'。

    Raises:
        ValueError: num_total <= 0 / num_missing > num_total / threshold 越界。
        TypeError: 输入类型错误。
    """
    pass
