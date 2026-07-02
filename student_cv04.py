"""滤波与降噪 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def apply_mean_filter(window: list) -> float:
    """
    均值滤波单窗口: sum(window) / len(window)。

    Args:
        window: list[float] 窗口数据。

    Returns:
        float: 均值。

    Raises:
        ValueError: 输入空。
        TypeError: 输入类型错误。
    """
    pass


def apply_median_filter(window: list) -> float:
    """
    中值滤波单窗口: 排序后取中位数。

    Args:
        window: list[float]。

    Returns:
        float: 中位数 (奇数取中, 偶数取中间两个均值)。

    Raises:
        ValueError: 输入空。
        TypeError: 输入类型错误。
    """
    pass


def compute_gaussian_kernel_1d(size: int, sigma: float) -> List[float]:
    """
    生成归一化的 1D 高斯核, 长度 size (奇数)。

    步骤:
      1. 中心 c = (size-1)/2
      2. 各位置 i 计算 G(i-c) = exp(-(i-c)^2 / (2 sigma^2))
      3. 归一化: 每个值除以 sum 让总和 = 1.0

    Args:
        size: 奇数 (>= 1)。
        sigma: 标准差 (> 0)。

    Returns:
        list[float] 长度 size, 总和 = 1.0。

    Raises:
        ValueError: size 偶数 / 非正 / sigma 非正。
        TypeError: 输入类型错误。
    """
    pass


def apply_filter_1d(values: list, kernel: list) -> List[float]:
    """
    1D valid 卷积 (实际是互相关): 输出长度 = len(values) - len(kernel) + 1。

    y[i] = sum_j values[i+j] * kernel[j]

    Args:
        values: 信号 list[float] 长 N。
        kernel: 卷积核 list[float] 长 K。

    Returns:
        list[float] 长度 N - K + 1。

    Raises:
        ValueError: kernel 比 values 长 / 输入空。
        TypeError: 输入类型错误。
    """
    pass
