"""反向传播与梯度下降 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def sigmoid_derivative(z: list) -> List[float]:
    """
    对数值列表逐元素计算 sigmoid 导数 σ'(z) = σ(z)·(1-σ(z))。

    Returns:
        与输入等长的 float 列表。

    Raises:
        TypeError: 输入不是 list / 含非数值。
    """
    pass


def compute_mse_gradient(y_true: list, y_pred: list) -> List[float]:
    """
    MSE 损失对 y_pred 的梯度: 2(y_pred - y_true) / N (逐元素)。

    Args:
        y_true: 真值列表。
        y_pred: 预测值列表, 与 y_true 等长。

    Returns:
        与输入等长的 float 列表。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def linear_backward_single(dz: float, x: list, w: list) -> Tuple[List[float], List[float], float]:
    """
    单神经元单样本反向传播。前向: z = w·x + b, 给定 dz = ∂L/∂z, 求 (dw, dx, db)。

    Args:
        dz: 上游梯度 (标量)。
        x: 该样本输入特征。
        w: 当前权重。

    Returns:
        (dw, dx, db):
          - dw: list[float] 长度 d, dw[i] = dz·x[i]
          - dx: list[float] 长度 d, dx[i] = dz·w[i]
          - db: float, = dz

    Raises:
        ValueError: x 与 w 长度不一致 / 空。
        TypeError: 输入类型错误。
    """
    pass


def gradient_descent_step(params: list, gradients: list, lr: float) -> List[float]:
    """
    梯度下降单步更新: params_new[i] = params[i] - lr·gradients[i]。

    Args:
        params: 当前参数。
        gradients: 各参数梯度, 长度同 params。
        lr: 学习率。

    Returns:
        更新后的参数 list。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入类型错误。
    """
    pass
