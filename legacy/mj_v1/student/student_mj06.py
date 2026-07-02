"""监督学习: 回归 - 学生作答文件"""
import numpy as np
from typing import Dict


def mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MSE: mean((y_true - y_pred)^2)"""
    pass


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAE: mean(abs(y_true - y_pred))"""
    pass


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """R²: 1 - SS_res / SS_tot"""
    pass


def ridge_loss(X: np.ndarray, y: np.ndarray, weights: np.ndarray, alpha: float) -> float:
    """
    Ridge 回归损失: MSE + alpha * sum(weights^2)

    Returns:
        float: 总损失值
    """
    pass


def normal_equation(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    正规方程闭式解: w = (X^T X)^(-1) X^T y

    Returns:
        np.ndarray: 权重向量
    """
    pass
