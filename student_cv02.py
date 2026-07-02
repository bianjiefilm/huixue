"""图像基础与色彩空间 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def rgb_to_grayscale(rgb) -> float:
    """
    RGB 三元组转灰度值: 0.299R + 0.587G + 0.114B。

    Args:
        rgb: list 或 tuple (r, g, b), 各值在 [0, 255]。

    Returns:
        float: 灰度值 [0, 255]。

    Raises:
        ValueError: 长度不是 3 / 含越界值。
        TypeError: 输入既非 list 也非 tuple。
    """
    pass


def rgb_to_hsv(rgb) -> Tuple[float, float, float]:
    """
    RGB 转 HSV (输入归一化 [0, 1] 浮点)。

    Args:
        rgb: list 或 tuple (r, g, b), 各值在 [0, 1]。

    Returns:
        (h, s, v):
          h ∈ [0, 360), s ∈ [0, 1], v ∈ [0, 1]。

    Raises:
        ValueError: 长度不是 3 / 含越界值。
        TypeError: 输入既非 list 也非 tuple。
    """
    pass


def apply_threshold(grayscale_array: list, threshold: int = 128) -> List[int]:
    """
    二值化: x > threshold → 255, 否则 0。

    Args:
        grayscale_array: list[int], 灰度像素列表 [0, 255]。
        threshold: 阈值 [0, 255]。

    Returns:
        list[int] 与输入等长, 元素 ∈ {0, 255}。

    Raises:
        ValueError: 输入空 / 阈值越界。
        TypeError: 输入类型错误。
    """
    pass


def compute_histogram(values: list, n_bins: int = 10, max_value: int = 255) -> List[int]:
    """
    像素直方图: 把 [0, max_value] 等分 n_bins 段, 统计各段频次。

    最后一个 bin 闭区间 (含 max_value)。

    Args:
        values: list[int]。
        n_bins: 分段数 (>0)。
        max_value: 像素最大值 (>0)。

    Returns:
        list[int] 长度 n_bins, 总和 = len(values)。

    Raises:
        ValueError: 输入空 / 含越界值 / n_bins 非正。
        TypeError: 输入类型错误。
    """
    pass
