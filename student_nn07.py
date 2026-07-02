"""优化算法 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def sgd_update(W: list, dW: list, lr: float) -> List[float]:
    """
    SGD 单步更新: W_new[i] = W[i] - lr * dW[i]。

    Args:
        W: 当前权重 list[float] (扁平化)。
        dW: 对应梯度 list[float] 长度同 W。
        lr: 学习率。

    Returns:
        list[float] 更新后的权重。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def momentum_update(W: list, dW: list, v_prev: list, lr: float, momentum: float) -> Tuple[List[float], List[float]]:
    """
    Momentum 单步更新: v = momentum*v_prev + dW; W_new = W - lr*v。

    Args:
        W, dW, v_prev: 等长 list[float]。
        lr: 学习率。
        momentum: 动量系数 (一般 0.9)。

    Returns:
        (W_new, v_new): 两个等长 list。

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def adam_update(W: list, dW: list, m_prev: list, v_prev: list,
                lr: float, beta1: float, beta2: float, t: int,
                eps: float = 1e-8) -> Tuple[List[float], List[float], List[float]]:
    """
    Adam 单步更新 (含偏差校正)。

    Args:
        W, dW, m_prev, v_prev: 等长 list[float]。
        lr, beta1, beta2: 超参 (常用 lr=0.001, beta1=0.9, beta2=0.999)。
        t: 当前步数 (1-indexed, 用于偏差校正)。
        eps: 数值稳定常数。

    Returns:
        (W_new, m_new, v_new): 三个等长 list。

    Raises:
        ValueError: 输入空 / 长度不一致 / t 非正。
        TypeError: 输入类型错误。
    """
    pass


def apply_lr_decay(initial_lr: float, epoch: int, decay_rate: float, decay_type: str) -> float:
    """
    根据 decay_type 计算 epoch 时的学习率。

    支持:
      - 'step': initial_lr * decay_rate**epoch
      - 'exp': initial_lr * exp(-decay_rate * epoch)
      - 'inverse': initial_lr / (1 + decay_rate * epoch)

    Returns:
        float: 当前学习率。

    Raises:
        ValueError: epoch 负 / decay_rate 非法 / decay_type 不支持。
        TypeError: 输入类型错误。
    """
    pass
