"""清洗质量评估 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Optional, Set, Dict


DEFAULT_MISSING_MARKERS = {None, "", "NA", "null", "NaN"}


def compute_completeness(values: List, markers: Optional[Set] = None) -> float:
    """
    完整性比率 = 非 missing 数 / 总数。

    Args:
        values: 任意 list。
        markers: 缺失 marker 集合 (None 用默认)。

    Returns:
        float ∈ [0.0, 1.0]。

    Raises:
        ValueError: 输入空。
        TypeError: 输入不是 list。
    """
    pass


def compute_uniqueness(values: List) -> float:
    """
    唯一性比率 = distinct 数 / 总数。

    Args:
        values: 任意 list。

    Returns:
        float ∈ (0.0, 1.0]。

    Raises:
        ValueError: 输入空。
        TypeError: 输入不是 list。
    """
    pass


def compute_validity_in_range(values: List[float], lower: float, upper: float) -> float:
    """
    有效性比率 = 在 [lower, upper] 内的元素数 / 总数。

    Args:
        values: 数值列表。
        lower, upper: 范围, lower <= upper。

    Returns:
        float ∈ [0.0, 1.0]。

    Raises:
        ValueError: 输入空 / lower > upper。
        TypeError: 输入类型错误。
    """
    pass


def quality_summary_dict(completeness: float, uniqueness: float,
                         validity: float) -> Dict[str, float]:
    """
    把 3 个比率组装成 dict:
      {'completeness': c, 'uniqueness': u, 'validity': v, 'overall': (c+u+v)/3}

    Args:
        completeness, uniqueness, validity: 都 ∈ [0, 1]。

    Returns:
        dict: 4 key, 含 'overall' 简单平均。

    Raises:
        ValueError: 任一参数越界 [0, 1]。
        TypeError: 输入不是数值。
    """
    pass
