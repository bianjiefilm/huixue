"""监督学习: 回归 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def compute_mse(y_true: list, y_pred: list) -> float:
    """
    计算均方误差。

    Returns:
        float: 平均平方误差。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 非 list / 含非数值。
    """
    pass


def compute_r2(y_true: list, y_pred: list) -> float:
    """
    计算决定系数 R²。允许返回负值 (模型不如均值基线)。

    Returns:
        float: R² 值, 不强制 ≥ 0。

    Raises:
        ValueError: 输入空 / 长度不一致 / y_true 全相同 (SS_tot = 0)。
        TypeError: 非 list / 含非数值。
    """
    pass


def linear_predict(X: list, weights: list, bias: float) -> List[float]:
    """
    给定特征矩阵、权重、偏置, 输出每个样本的预测值。

    Args:
        X: list[list[float]], 形状 (n_samples, n_features)。
        weights: 长度 n_features 的浮点列表。
        bias: 标量。

    Returns:
        长度 n_samples 的浮点列表。

    Raises:
        ValueError: X 空 / 行长度不一致 / weights 与特征数不匹配。
        TypeError: 输入类型错误。
    """
    pass


def normal_equation(X: list, y: list) -> List[float]:
    """
    用正规方程对 (X, y) 求 OLS 最优权重。不自动加截距列。

    Args:
        X: list[list[float]] 形状 (n_samples, n_features)。
        y: 长度 n_samples 的浮点列表。

    Returns:
        长度 n_features 的浮点权重列表。

    Raises:
        ValueError: X 空 / 形状不匹配 / X^T X 奇异 (无法求逆)。
        TypeError: 输入类型错误。
    """
    pass
