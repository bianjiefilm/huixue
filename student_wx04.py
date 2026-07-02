"""异常值检测与处理 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def is_outlier_iqr(value: float, q1: float, q3: float,
                   multiplier: float = 1.5) -> bool:
    """
    IQR 法判断单值是否异常: value < q1 - mult*(q3-q1) 或 value > q3 + mult*(q3-q1)。

    Args:
        value: 待判断值。
        q1, q3: 25%/75% 分位数, 满足 q1 <= q3。
        multiplier: 容差倍数, 默认 1.5。

    Returns:
        bool: True 若是 outlier。

    Raises:
        ValueError: q1 > q3 / multiplier <= 0。
        TypeError: 输入不是数值。
    """
    pass


def compute_iqr_bounds(q1: float, q3: float,
                       multiplier: float = 1.5) -> Tuple[float, float]:
    """
    计算 IQR 上下界: (lower, upper) = (q1 - mult*IQR, q3 + mult*IQR)。

    Args:
        q1, q3: 分位数, 满足 q1 <= q3。
        multiplier: 倍数, 默认 1.5。

    Returns:
        (lower, upper)。

    Raises:
        ValueError: q1 > q3 / multiplier <= 0。
        TypeError: 输入不是数值。
    """
    pass


def clip_value_to_range(value: float, lower: float, upper: float) -> float:
    """
    截断值到 [lower, upper] 区间内: max(min(value, upper), lower)。

    Args:
        value: 待截断值。
        lower, upper: 上下界, 满足 lower <= upper。

    Returns:
        float: 截断结果。

    Raises:
        ValueError: lower > upper。
        TypeError: 输入不是数值。
    """
    pass


def count_outliers(values: List[float], lower: float, upper: float) -> int:
    """
    统计列表中超出 [lower, upper] 的元素个数。

    Args:
        values: 数值列表。
        lower, upper: 上下界, 满足 lower <= upper。

    Returns:
        int: 超出范围的个数 (>= 0)。

    Raises:
        ValueError: lower > upper。
        TypeError: 输入不是 list。
    """
    pass
