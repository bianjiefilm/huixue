"""前向传播与损失函数 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def linear_forward(x: list, w: list, b: float) -> float:
    """
    单神经元线性前向: z = w·x + b。

    Args:
        x: 输入特征列表, 长度 d。
        w: 权重列表, 长度 d。
        b: 偏置标量。

    Returns:
        float: 标量输出 z。

    Raises:
        ValueError: 输入空 / x 与 w 长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def linear_forward_batch(X: list, W: list, b: list) -> List[List[float]]:
    """
    批量线性前向: Z = X @ W + b (按样本广播加偏置)。

    Args:
        X: list[list[float]] 形状 (N, d)。
        W: list[list[float]] 形状 (d, h); W[i][j] = 第 i 输入到第 j 输出的权重。
        b: list[float] 形状 (h,)。

    Returns:
        list[list[float]] 形状 (N, h)。

    Raises:
        ValueError: 输入空 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def binary_cross_entropy(y_true: list, y_prob: list, eps: float = 1e-12) -> float:
    """
    二元交叉熵: -mean(y log p + (1-y) log(1-p))。
    实现时用 eps 把 p clip 到 [eps, 1-eps] 防 log(0)。

    Args:
        y_true: list[int 0 或 1]。
        y_prob: list[float ∈ [0, 1]]。
        eps: 数值稳定常数。

    Returns:
        float: 平均损失。

    Raises:
        ValueError: 输入空 / 长度不一致 / y_true 含非 0/1 / y_prob 越界。
        TypeError: 输入类型错误。
    """
    pass


def categorical_cross_entropy(y_true: list, y_probs: list, eps: float = 1e-12) -> float:
    """
    多元交叉熵 (类别索引版): -mean(log p[i, y_true[i]])。

    Args:
        y_true: list[int] 类别索引, 范围 [0, C-1]。
        y_probs: list[list[float]] 形状 (N, C); 每行是该样本的类别概率分布。
        eps: 数值稳定常数。

    Returns:
        float: 平均损失。

    Raises:
        ValueError: 输入空 / 长度不一致 / y_true 越界 / y_probs 行长度不一致。
        TypeError: 输入类型错误。
    """
    pass
