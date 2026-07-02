"""数据探索与特征理解 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List


def compute_correlation(x: list, y: list) -> float:
    """
    给定两组等长数值列表, 返回 Pearson 相关系数。

    Returns:
        float: Pearson 相关系数, 取值 [-1.0, 1.0]。

    Raises:
        ValueError: 输入为空、两列表长度不一致, 或任一列表方差为 0。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass


def find_outliers_iqr(values: list) -> List[int]:
    """
    用 IQR 1.5 倍规则找出异常值的索引位置。

    Returns:
        List[int]: 异常值在原列表中的索引, 升序; 无异常值返回空列表。

    Raises:
        ValueError: 输入为空。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass


def summarize_distribution(values: list) -> Dict[str, float]:
    """
    返回数值列表的摘要统计。

    Returns:
        含 4 个键的 dict:
          - 'mean': 算术平均
          - 'median': 中位数
          - 'std': 总体标准差 (除以 N, 不是 N-1)
          - 'range': 极差 (max - min)

    Raises:
        ValueError: 输入为空。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass


def compute_quartiles(values: list) -> List[float]:
    """
    返回数值列表的五数概括。

    Returns:
        长度恰为 5 的 list[float]: [min, Q1, median, Q3, max]
        (Q1/Q3 用线性插值法计算)。

    Raises:
        ValueError: 输入为空。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass
