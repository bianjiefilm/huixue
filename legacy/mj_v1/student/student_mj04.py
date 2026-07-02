"""监督学习: 分类基础 - 学生作答文件"""
import numpy as np
from typing import Dict, Tuple


def sigmoid(z: np.ndarray) -> np.ndarray:
    """
    sigmoid 函数: 1 / (1 + exp(-z))
    对输入数组逐元素计算。
    """
    pass


def logistic_regression_predict(X: np.ndarray, weights: np.ndarray, bias: float) -> np.ndarray:
    """
    逻辑回归预测: 先计算线性组合,再用 sigmoid 转为概率。

    Args:
        X: (n_samples, n_features)
        weights: (n_features,)
        bias: float

    Returns:
        np.ndarray: 各类别概率 (n_samples,)
    """
    pass


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    计算混淆矩阵导出指标: TP/FP/TN/FN → accuracy/precision/recall/f1。

    Returns:
        dict: {accuracy, precision, recall, f1} 保留4位小数
    """
    pass


def find_best_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> Tuple[float, float]:
    """
    在 [0,1] 范围内遍历阈值,找到使 F1 最大的阈值及其 F1 值。

    Returns:
        (best_threshold, best_f1)
    """
    pass
