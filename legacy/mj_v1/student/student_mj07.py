"""无监督学习: 聚类 - 学生作答文件"""
import numpy as np
from typing import List, Tuple


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个向量的欧氏距离"""
    pass


def kmeans_init_centroids(X: np.ndarray, k: int) -> np.ndarray:
    """
    K-Means++ 初始化: 选择距离已选中心最远的样本作为新中心。

    Returns:
        np.ndarray: (k, n_features) 初始中心
    """
    pass


def assign_clusters(X: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """
    将每个样本分配给最近的中心。

    Returns:
        np.ndarray: 每个样本的簇标签 (n_samples,)
    """
    pass


def compute_inertia(X: np.ndarray, labels: np.ndarray, centroids: np.ndarray) -> float:
    """
    计算 K-Means inertia(SSE): 每个样本到其所属中心的距离平方和。

    Returns:
        float: inertia 值
    """
    pass


def silhouette_score(X: np.ndarray, labels: np.ndarray) -> float:
    """
    轮廓系数: s = (b - a) / max(a, b)

    a: 样本到同簇其他点的平均距离
    b: 样本到最近其他簇的平均距离

    Returns:
        float: 轮廓系数 (-1~1, 越接近1越好)
    """
    pass
