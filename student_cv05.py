"""边缘检测 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def compute_sobel_x_kernel() -> List[List[int]]:
    """
    返回 3×3 的 Sobel-x 算子矩阵。

    Returns:
        list[list[int]]: 形状 (3, 3) 的整数矩阵。
    """
    pass


def compute_sobel_y_kernel() -> List[List[int]]:
    """
    返回 3×3 的 Sobel-y 算子矩阵。

    Returns:
        list[list[int]]: 形状 (3, 3) 的整数矩阵。
    """
    pass


def compute_gradient_magnitude(gx: float, gy: float) -> float:
    """
    给定 x/y 方向梯度, 计算梯度幅值 (L2)。

    Args:
        gx: x 方向梯度。
        gy: y 方向梯度。

    Returns:
        float: 幅值。

    Raises:
        TypeError: 输入不是数值。
    """
    pass


def canny_threshold_classify(magnitude: float, low: float, high: float) -> str:
    """
    Canny 双阈值: 把梯度幅值分类为 'strong' / 'weak' / 'non_edge'。

    Args:
        magnitude: 梯度幅值 (>= 0)。
        low: 低阈值。
        high: 高阈值。

    Returns:
        str: 'strong' / 'weak' / 'non_edge' 三选一。

    Raises:
        ValueError: low >= high 或 magnitude < 0 或阈值非正。
        TypeError: 输入不是数值。
    """
    pass
