"""数据预处理与特征工程 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List, Tuple


def label_encode(values: list) -> Tuple[List[int], Dict[str, int]]:
    """
    把字符串列表做标签编码。

    Returns:
        (encoded, mapping):
          - encoded: 编码后的整数列表, 长度等于 values
          - mapping: dict {原始字符串: 整数编码}, 编号基于去重排序后顺序

    Raises:
        ValueError: 输入为空。
        TypeError: 输入不是 list / 含非字符串元素。
    """
    pass


def z_score_standardize(values: list) -> List[float]:
    """
    对数值列表做 z-score 标准化, 标准差用 N (总体) 作分母。

    Returns:
        与输入等长的 float 列表, 标准化后均值≈0、标准差≈1。

    Raises:
        ValueError: 输入为空 / 标准差为 0 (常量列)。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass


def fill_with_median(values: list) -> List[float]:
    """
    用中位数填充列表中的 None。中位数仅基于非 None 值计算。

    Returns:
        与输入等长的 float 列表, 不含 None。

    Raises:
        ValueError: 输入为空 / 全部都是 None。
        TypeError: 输入不是 list / 含既非数值又非 None 的元素。
    """
    pass


def filter_low_variance(matrix: list, threshold: float) -> Tuple[List[List[float]], List[int]]:
    """
    按列方差阈值过滤多列数据。保留方差**严格大于** threshold 的列。

    Args:
        matrix: list[list[float]], 形状 (n_samples, n_features)。
        threshold: 阈值。

    Returns:
        (filtered_matrix, kept_indices):
          - filtered_matrix: 仅含被保留列的子矩阵
          - kept_indices: 被保留列在原矩阵中的索引升序列表

    Raises:
        ValueError: 矩阵为空 / 单样本 (无法算方差) / 行长度不一致。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass
