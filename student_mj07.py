"""无监督学习: 聚类 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def euclidean_distance(p1: list, p2: list) -> float:
    """
    计算两个等长向量的欧氏距离。

    Returns:
        float: 距离值, 非负。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入不是 list / 含非数值。
    """
    pass


def assign_clusters(X: list, centroids: list) -> List[int]:
    """
    把每个样本分配给距离它最近的中心。距离相同时返回较小的中心索引。

    Args:
        X: list[list[float]] 形状 (n_samples, n_features)。
        centroids: list[list[float]] 形状 (k, n_features)。

    Returns:
        list[int] 长度 n_samples; 每个值是该样本所属簇的索引 (0..k-1)。

    Raises:
        ValueError: X 或 centroids 空 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def update_centroids(X: list, labels: list, k: int) -> List[List[float]]:
    """
    根据当前 labels 重新计算每个簇的中心 (簇内均值)。

    Args:
        X: list[list[float]] 形状 (n_samples, n_features)。
        labels: list[int] 长度 n_samples, 每个值在 [0, k) 范围内。
        k: 簇数 (>0)。

    Returns:
        list[list[float]] 形状 (k, n_features); 第 i 行是簇 i 的中心。
        若某簇为空, 该行用全 0 占位。

    Raises:
        ValueError: 输入空 / X 与 labels 长度不一致 / k 非正。
        TypeError: 输入类型错误。
    """
    pass


def compute_inertia(X: list, labels: list, centroids: list) -> float:
    """
    计算簇内平方和 (inertia): 所有样本到自己簇中心的距离平方之和。

    Returns:
        float: inertia 值, 非负。

    Raises:
        ValueError: 输入空 / 长度/形状不匹配 / labels 含越界值。
        TypeError: 输入类型错误。
    """
    pass
