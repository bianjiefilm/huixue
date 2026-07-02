"""卷积神经网络基础 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def conv1d_single_step(x_slice: list, kernel: list, bias: float) -> float:
    """
    单卷积窗口: z = sum(x_slice[i] * kernel[i]) + bias。

    Args:
        x_slice: 输入切片 (与 kernel 等长)。
        kernel: 卷积核。
        bias: 偏置。

    Returns:
        float: 标量输出。

    Raises:
        ValueError: 长度不一致 / 空。
        TypeError: 输入类型错误。
    """
    pass


def compute_output_shape(input_size: int, kernel_size: int,
                         padding: int = 0, stride: int = 1) -> int:
    """
    卷积输出大小 (1D): floor((N + 2P - K) / S) + 1。

    Args:
        input_size: 输入长度 (>0)。
        kernel_size: 卷积核长度 (>0)。
        padding: padding 大小 (>=0)。
        stride: 步长 (>0)。

    Returns:
        int: 输出长度。

    Raises:
        ValueError: 任一参数非法 / 输入加 padding 仍小于 kernel。
        TypeError: 输入类型错误。
    """
    pass


def max_pool_2x2(matrix: list) -> List[List[float]]:
    """
    2×2 最大池化, stride=2。要求输入高宽都为偶数。

    Args:
        matrix: list[list[float]] 形状 (H, W), H 与 W 都是偶数。

    Returns:
        list[list[float]] 形状 (H/2, W/2)。

    Raises:
        ValueError: 输入空 / 行长度不一致 / H 或 W 非偶数。
        TypeError: 输入类型错误。
    """
    pass


def count_conv_params(in_channels: int, out_channels: int, kernel_size: int) -> int:
    """
    卷积层参数总数: in*out*K^2 + out (含偏置)。

    Args:
        in_channels: 输入通道 (>0)。
        out_channels: 输出通道 (>0)。
        kernel_size: 卷积核大小 (>0, 假设方形)。

    Returns:
        int: 参数总数。

    Raises:
        ValueError: 任一参数非正。
        TypeError: 输入类型错误。
    """
    pass
