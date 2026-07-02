"""缺失值检测与补全 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Optional, Set


DEFAULT_MISSING_MARKERS = {None, "", "NA", "null", "NaN"}


def is_missing(value, markers: Optional[Set] = None) -> bool:
    """
    判断单个值是否为缺失值。
    若 markers 为 None, 用默认 {None, "", "NA", "null", "NaN"}。

    Args:
        value: 待判断值。
        markers: 缺失 marker 集合 (None 用默认)。

    Returns:
        bool: True 若是 missing。
    """
    pass


def count_missing(values: List, markers: Optional[Set] = None) -> int:
    """
    统计列表中 missing 的数量。

    Args:
        values: 列表。
        markers: 缺失 marker 集合 (None 用默认)。

    Returns:
        int: missing 数量 (>= 0)。

    Raises:
        TypeError: values 不是 list。
    """
    pass


def fill_missing_with_mean(values: List, markers: Optional[Set] = None) -> List[float]:
    """
    用非 missing 值的均值补全所有 missing 位置。
    若全 missing, 抛 ValueError。

    Args:
        values: 数值列表 (含 missing)。
        markers: 缺失 marker 集合 (None 用默认)。

    Returns:
        list[float]: 与输入同长度, missing 位置已替换为均值。

    Raises:
        ValueError: 全 missing / 输入空。
        TypeError: 输入不是 list。
    """
    pass


def fill_missing_with_constant(values: List, constant: float,
                              markers: Optional[Set] = None) -> List:
    """
    用常量补全所有 missing 位置。

    Args:
        values: 列表。
        constant: 填充常量。
        markers: 缺失 marker 集合 (None 用默认)。

    Returns:
        list: 与输入同长度, missing 位置已替换为 constant。

    Raises:
        TypeError: values 不是 list。
    """
    pass
