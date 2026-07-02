"""单个神经元与激活函数 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def sigmoid_activation(z: list) -> List[float]:
    """
    对数值列表逐元素计算 sigmoid 值。

    Returns:
        与输入等长的 float 列表; 输入空列表返回空列表。

    Raises:
        TypeError: 输入不是 list / 含非数值。
    """
    pass


def tanh_activation(z: list) -> List[float]:
    """
    对数值列表逐元素计算 tanh 值。

    Returns:
        与输入等长的 float 列表; 输入空列表返回空列表。

    Raises:
        TypeError: 输入不是 list / 含非数值。
    """
    pass


def relu_activation(z: list) -> List[float]:
    """
    对数值列表逐元素计算 ReLU 值 (max(0, z))。

    Returns:
        与输入等长的 float 列表。

    Raises:
        TypeError: 输入不是 list / 含非数值。
    """
    pass


def leaky_relu_activation(z: list, alpha: float = 0.01) -> List[float]:
    """
    对数值列表逐元素计算 Leaky ReLU 值: z>0 返回 z, 否则返回 alpha*z。

    Args:
        z: 数值列表。
        alpha: 负区斜率, 通常 0 < alpha < 1。

    Returns:
        与输入等长的 float 列表。

    Raises:
        TypeError: 输入不是 list / 含非数值; alpha 不是数值。
    """
    pass
