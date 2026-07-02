"""无监督学习: 降维 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def center_data(X: list) -> Tuple[List[List[float]], List[float]]:
    """
    对样本矩阵每列减去该列均值。

    Args:
        X: list[list[float]] 形状 (n_samples, n_features)。

    Returns:
        (centered_X, mean):
          - centered_X: 与 X 同形状, 每列均值为 0
          - mean: 长度 n_features 的列均值列表

    Raises:
        ValueError: X 空 / 行长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def compute_covariance(X: list) -> List[List[float]]:
    """
    从 (已中心化) 样本矩阵计算协方差矩阵, 分母用 N (population)。

    Args:
        X: list[list[float]] 形状 (n_samples, n_features), 应已中心化。

    Returns:
        list[list[float]] 形状 (n_features, n_features), 对称半正定。

    Raises:
        ValueError: X 空 / 行长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def pca_transform(X: list, components: list) -> List[List[float]]:
    """
    把样本矩阵投影到主成分空间。

    Args:
        X: list[list[float]] 形状 (n_samples, n_features)。
        components: list[list[float]] 形状 (k, n_features); 每行是一个主成分方向。

    Returns:
        list[list[float]] 形状 (n_samples, k); 每行是该样本的 k 维主成分坐标。

    Raises:
        ValueError: X 或 components 空 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def explained_variance_ratio(eigenvalues: list) -> List[float]:
    """
    把特征值列表归一化为解释方差比例 (sum = 1)。

    Args:
        eigenvalues: list[float], 各值非负。

    Returns:
        list[float] 与输入等长, 总和为 1.0。

    Raises:
        ValueError: 输入空 / 含负值 / 全 0 (无法归一化)。
        TypeError: 输入类型错误。
    """
    pass
