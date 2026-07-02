"""监督学习: 分类进阶 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List


def majority_vote(predictions: list, tie_break: str = "smaller") -> List[int]:
    """
    对多个基础模型对同一批样本的预测做多数表决。

    Args:
        predictions: list[list[int]], 形状 (n_samples, n_estimators);
                     每行是一个样本的 K 个估计器预测标签。
        tie_break: 平票规则; 本关只支持 'smaller' (返回数值最小的类)。

    Returns:
        list[int], 长度 n_samples, 每个样本的多数表决结果。

    Raises:
        ValueError: 输入空 / 含空内层 / 包含非整数标签。
        TypeError: 输入不是 list / 内层不是 list。
    """
    pass


def compute_feature_importance(usage_counts: list) -> List[float]:
    """
    将每个特征的使用计数归一化为重要性比例 (sum = 1)。

    Returns:
        与输入等长的 float 列表; 各值非负, 总和为 1.0。

    Raises:
        ValueError: 输入空 / 全 0 (无法归一化) / 含负数。
        TypeError: 输入不是 list / 含非整数元素。
    """
    pass


def gini_impurity(labels: list) -> float:
    """
    计算给定标签列表的 Gini 不纯度。

    Returns:
        float: 1 - sum(p_c^2)。

    Raises:
        ValueError: 输入空。
        TypeError: 输入不是 list / 含非整数元素。
    """
    pass


def compute_boosting_residual(y_true: list, y_pred: list) -> List[float]:
    """
    Boosting 第 t 轮的残差: y_true[i] - y_pred[i]。

    Returns:
        与输入等长的 float 列表。

    Raises:
        ValueError: 输入空 / 两列表长度不一致。
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass
