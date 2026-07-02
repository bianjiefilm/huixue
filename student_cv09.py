"""图像分类 CNN 基础 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def conv_layer_param_count(in_channels: int, out_channels: int,
                           kernel_h: int, kernel_w: int,
                           bias: bool = True) -> int:
    """
    2D 卷积层总参数量。

    Args:
        in_channels, out_channels: 输入/输出通道数。
        kernel_h, kernel_w: kernel 高/宽。
        bias: 是否有偏置项。

    Returns:
        int: 参数量。

    Raises:
        ValueError: 维度参数非正。
        TypeError: 输入类型错误。
    """
    pass


def conv_output_size_2d(input_h: int, input_w: int,
                        kernel: int, padding: int = 0,
                        stride: int = 1) -> Tuple[int, int]:
    """
    2D 卷积输出形状 (H_out, W_out)。
    H_out = floor((H + 2p - k) / s) + 1, W_out 同公式。

    Args:
        input_h, input_w: 输入高/宽。
        kernel: kernel 边长 (方形)。
        padding: padding (>= 0)。
        stride: 步长 (>= 1)。

    Returns:
        (H_out, W_out)。

    Raises:
        ValueError: 输出尺寸 <= 0 或参数非法。
        TypeError: 输入类型错误。
    """
    pass


def softmax_predict(logits: List[float]) -> int:
    """
    返回 argmax 类别 (softmax 单调性, 不需算 softmax)。

    Args:
        logits: 1D list[float]。

    Returns:
        int: argmax 索引 (并列取最小)。

    Raises:
        ValueError: 输入空。
        TypeError: 输入不是 list。
    """
    pass


def cross_entropy_loss_single(probs: List[float], label: int) -> float:
    """
    单样本交叉熵损失: -log(probs[label])。
    用 ln (natural log)。

    Args:
        probs: 类别概率分布 (sum ≈ 1, 元素 > 0)。
        label: 真实类别索引 (0 <= label < len(probs))。

    Returns:
        float: 损失值 (>= 0)。

    Raises:
        ValueError: label 越界 / probs 含 0 或负数 / 输入空。
        TypeError: 输入类型错误。
    """
    pass
