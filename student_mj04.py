"""监督学习: 分类基础 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List


def sigmoid(z: list) -> List[float]:
    """
    对数值列表逐元素计算 sigmoid 值, 输出严格落在 (0, 1)。

    Returns:
        与输入等长的 float 列表; 输入为空列表时返回空列表。

    Raises:
        TypeError: 输入不是 list / 含非数值元素。
    """
    pass


def compute_confusion_matrix(y_true: list, y_pred: list) -> Dict[str, int]:
    """
    给定二分类真实标签与预测标签 (取值 0 或 1), 返回混淆矩阵。

    Returns:
        含 4 个键的 dict: 'tp', 'fp', 'tn', 'fn' (都是 int)。

    Raises:
        ValueError: 输入为空 / 两列表长度不一致 / 含非 0/1 取值。
        TypeError: 输入不是 list / 含非整数元素。
    """
    pass


def compute_metrics(tp: int, fp: int, tn: int, fn: int) -> Dict[str, float]:
    """
    根据混淆矩阵 4 个计数, 计算 accuracy/precision/recall/F1 四个指标。

    Returns:
        含 4 个键的 dict: 'accuracy', 'precision', 'recall', 'f1' (都是 float)。
        当除零情况发生 (precision/recall/f1 分母为 0) 时, 该指标取 0.0。

    Raises:
        ValueError: 任一参数为负 / 4 个参数全为 0 (无样本)。
        TypeError: 任一参数不是 int。
    """
    pass


def classify_by_threshold(scores: list, threshold: float) -> List[int]:
    """
    用阈值规则把概率分数转成 0/1 标签。规则: score >= threshold 判 1, 否则 0。

    Returns:
        与输入等长的 0/1 整数列表; 输入空列表返回空列表。

    Raises:
        TypeError: scores 不是 list / 含非数值; threshold 不是数值。
    """
    pass
