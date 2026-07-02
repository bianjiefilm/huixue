"""数据挖掘概述与流程 - 学生作答文件"""
from typing import Dict, List, Tuple
from sklearn.base import BaseEstimator, ClassifierMixin
import numpy as np


def get_crisp_dm_phases() -> List[str]:
    """
    返回 CRISP-DM 标准流程的 6 个阶段名称列表。

    Returns:
        List[str]: 按顺序的6个阶段名称
    """
    pass


def classify_problem_type(X, y) -> str:
    """
    根据数据特征判断问题类型。

    Args:
        X: 特征矩阵 (n_samples, n_features)
        y: 标签向量 (n_samples,)

    Returns:
        str: 'supervised', 'unsupervised', 或 'semi-supervised'
    """
    pass


def evaluate_classifier(y_true, y_pred) -> Dict[str, float]:
    """
    计算分类器评估指标: 准确率、精确率、召回率、F1。

    Args:
        y_true: 真实标签
        y_pred: 预测标签

    Returns:
        dict: {accuracy, precision, recall, f1}，值保留4位小数
    """
    pass


def detect_overfitting(training_score: float, test_score: float) -> Dict[str, any]:
    """
    判断模型是否过拟合。

    Args:
        training_score: 训练集得分 (0~1)
        test_score: 测试集得分 (0~1)

    Returns:
        dict: {is_overfitting: bool, gap: float, suggestion: str}
    """
    pass
