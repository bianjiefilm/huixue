"""图像分割 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def binary_threshold_segment(values: List[float], thresh: float) -> List[int]:
    """
    二值阈值分割: >= thresh 标 1, 否则标 0。

    Args:
        values: 1D list[float] (灰度值)。
        thresh: 阈值。

    Returns:
        list[int]: 与输入同长度的 0/1 列表。

    Raises:
        ValueError: 输入空。
        TypeError: 输入类型错误。
    """
    pass


def connected_components_count_1d(values: List[int]) -> int:
    """
    1D 二值序列的连通区域数 = 1 的连续段个数。

    Args:
        values: 1D list[int], 元素 0 或 1。

    Returns:
        int: 连通区域数 (>= 0)。

    Raises:
        ValueError: 元素不在 {0, 1}。
        TypeError: 输入不是 list。
    """
    pass


def dice_coefficient(pred: List[int], gt: List[int]) -> float:
    """
    Dice 系数 = 2 * |A ∩ B| / (|A| + |B|)。
    特殊情况: 两者都全 0 → Dice = 1.0 (约定)。

    Args:
        pred, gt: 同长度 1D list[int], 元素 0 或 1。

    Returns:
        float: Dice ∈ [0.0, 1.0]。

    Raises:
        ValueError: 长度不一致 / 元素不在 {0,1}。
        TypeError: 输入类型错误。
    """
    pass


def pixel_accuracy(pred: List[int], gt: List[int]) -> float:
    """
    Pixel Accuracy = sum([pred_i == gt_i]) / N。

    Args:
        pred, gt: 同长度 1D list[int]。

    Returns:
        float: PA ∈ [0.0, 1.0]。

    Raises:
        ValueError: 长度不一致 / 输入空。
        TypeError: 输入类型错误。
    """
    pass
