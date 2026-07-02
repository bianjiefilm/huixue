"""监督学习: 分类进阶 - 学生作答文件"""
import numpy as np
import pandas as pd
from typing import Dict, List


def compute_gini(labels: np.ndarray) -> float:
    """
    计算给定标签数组的基尼系数: 1 - sum(p_i^2)

    Args:
        labels: 一组样本的标签

    Returns:
        float: 基尼系数 (0~1)
    """
    pass


def find_best_split(X: np.ndarray, y: np.ndarray, feature_indices: List[int]) -> Dict:
    """
    在指定特征范围内找最优分裂点。

    对每个特征计算最佳分裂阈值,返回基尼增益最大的分裂。

    Returns:
        dict: {feature_index, threshold, gini_gain}
    """
    pass


def random_forest_predict(X: np.ndarray, trees: List[Dict], n_classes: int) -> np.ndarray:
    """
    随机森林预测: K 棵树投票。

    Args:
        X: (n_samples, n_features)
        trees: 每棵树的 {feature_indices, thresholds, leaf_values}
        n_classes: 类别数

    Returns:
        np.ndarray: 预测标签 (n_samples,)
    """
    pass


def get_feature_importance(forest_dicts: List[Dict]) -> np.ndarray:
    """
    从随机森林中汇总特征重要性。

    Args:
        forest_dicts: 每棵树的特征使用计数列表

    Returns:
        np.ndarray: 归一化重要性数组 (n_features,)
    """
    pass
