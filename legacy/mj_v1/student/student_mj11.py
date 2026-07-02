"""集成学习与模型融合 - 学生作答文件"""
import numpy as np
from typing import List


def bagging_predict(X: np.ndarray, base_predictions: np.ndarray) -> np.ndarray:
    """
    Bagging 投票: base_predictions (n_estimators, n_samples) 每行是基础模型的预测标签,
    返回多数投票结果。

    Returns:
        np.ndarray: 投票后的预测标签 (n_samples,)
    """
    pass


def weighted_bagging_predict(X: np.ndarray, base_predictions: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    加权 Bagging: 按 weights 权重对各模型预测结果加权后取 argmax。

    Args:
        base_predictions: (n_estimators, n_samples)
        weights: (n_estimators,)

    Returns:
        np.ndarray: 加权投票结果 (n_samples,)
    """
    pass


def stacking_predict(meta_features: np.ndarray, meta_model) -> np.ndarray:
    """
    Stacking 预测: 用元模型对基础模型输出矩阵 meta_features 做预测。

    Args:
        meta_features: (n_samples, n_estimators) 基础模型预测概率/标签
        meta_model: 有 predict 方法的模型

    Returns:
        np.ndarray: 元模型预测结果
    """
    pass


def adaboost_weights_update(weights: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray, alpha: float) -> np.ndarray:
    """
    AdaBoost 样本权重更新: w_new = w * exp(-alpha * y_true * y_pred)

    Args:
        weights: (n_samples,)
        y_true: (n_samples,) 真实标签(+1/-1)
        y_pred: (n_samples,) 预测标签(+1/-1)
        alpha: 分类器权重

    Returns:
        np.ndarray: 更新后的权重 (n_samples,)
    """
    pass
