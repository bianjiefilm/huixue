"""无监督学习: 降维 - 学生作答文件"""
import numpy as np
from typing import Tuple


def pca_fit(X: np.ndarray, n_components: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    PCA 拟合: 对 X 做标准化后,计算协方差矩阵并返回前 n_components 个主成分。

    Returns:
        (components, explained_variance) — (n_components, n_features), (n_components,)
    """
    pass


def pca_transform(X: np.ndarray, components: np.ndarray) -> np.ndarray:
    """
    用已 fit 的主成分对 X 投影降维。

    Returns:
        np.ndarray: 降维后的数据 (n_samples, n_components)
    """
    pass


def explained_variance_ratio(variance: np.ndarray) -> np.ndarray:
    """
    将方差向量转为解释方差比例(各方差/总方差)。

    Returns:
        np.ndarray: 各主成分解释方差比例
    """
    pass


def reconstruct_from_pca(X_pca: np.ndarray, components: np.ndarray, mean: np.ndarray) -> np.ndarray:
    """
    从 PCA 降维结果重建回原始维度(近似)。

    Returns:
        np.ndarray: 重建数据 (n_samples, n_features)
    """
    pass
