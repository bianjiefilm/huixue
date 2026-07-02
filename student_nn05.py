"""浅层神经网络实战 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def forward_propagate(X: list, W1: list, b1: list, W2: list, b2: list) -> Tuple:
    """
    1 隐层 MLP 单次前向: Linear → ReLU → Linear → Sigmoid。

    Args:
        X: list[list[float]] 形状 (N, d)。
        W1: list[list[float]] 形状 (d, h)。
        b1: list[float] 长度 h。
        W2: list[list[float]] 形状 (h, 1)。
        b2: list[float] 长度 1。

    Returns:
        4-tuple (z1, a1, z2, a2):
          z1, a1 形状 (N, h)
          z2, a2 形状 (N, 1)

    Raises:
        ValueError: 输入空 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def backward_propagate(X: list, y: list, z1: list, a1: list, a2: list,
                      W2: list) -> Tuple:
    """
    BCE+Sigmoid 组合下 1 隐层 MLP 单步反向传播。

    Args:
        X: list[list[float]] (N, d)。
        y: list[int] 长度 N, 取值 0/1。
        z1, a1: 形状 (N, h)。
        a2: 形状 (N, 1)。
        W2: 形状 (h, 1)。

    Returns:
        4-tuple (dW1, db1, dW2, db2):
          dW1 (d, h), db1 (h,), dW2 (h, 1), db2 (1,)。
        BCE 取 mean → 各梯度除以 N。

    Raises:
        ValueError: 输入空 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def predict_labels(a2: list, threshold: float = 0.5) -> List[int]:
    """
    把 (N, 1) 形状的 sigmoid 输出转成 0/1 标签列表。

    规则: a2[i][0] >= threshold → 1, 否则 0。

    Args:
        a2: list[list[float]] 形状 (N, 1)。
        threshold: 阈值, 默认 0.5。

    Returns:
        list[int] 长度 N。

    Raises:
        ValueError: 形状错 (不是 N×1)。
        TypeError: 输入类型错误。
    """
    pass


def compute_accuracy_binary(y_pred: list, y_true: list) -> float:
    """
    计算二分类准确率: 预测正确占总数的比例。

    Args:
        y_pred: list[int 0/1]。
        y_true: list[int 0/1] 与 y_pred 等长。

    Returns:
        float ∈ [0, 1]。

    Raises:
        ValueError: 输入空 / 长度不一致 / 含非 0/1。
        TypeError: 输入类型错误。
    """
    pass
