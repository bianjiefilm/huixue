"""图像几何变换 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def translate_point(x: float, y: float, dx: float, dy: float) -> Tuple[float, float]:
    """
    平移: (x+dx, y+dy)。

    Returns:
        (new_x, new_y)。

    Raises:
        TypeError: 输入不是数值。
    """
    pass


def rotate_point(x: float, y: float, angle_deg: float,
                 cx: float = 0.0, cy: float = 0.0) -> Tuple[float, float]:
    """
    绕中心 (cx, cy) 顺时针旋转 angle_deg 度。

    Args:
        x, y: 原始点坐标。
        angle_deg: 旋转角度 (度)。
        cx, cy: 旋转中心, 默认原点。

    Returns:
        (new_x, new_y)。

    Raises:
        TypeError: 输入不是数值。
    """
    pass


def scale_dimensions(width: int, height: int, fx: float, fy: float) -> Tuple[int, int]:
    """
    各向异性缩放尺寸: (floor(width*fx), floor(height*fy))。

    Args:
        width, height: 正整数。
        fx, fy: 正浮点缩放因子。

    Returns:
        (new_w, new_h): 整数尺寸。

    Raises:
        ValueError: 任一参数非正。
        TypeError: 输入类型错误。
    """
    pass


def apply_affine_transform(x: float, y: float, matrix: list) -> Tuple[float, float]:
    """
    2×3 仿射变换: 给定 2×3 矩阵 M = [[a00,a01,a02],[a10,a11,a12]]:
      x' = a00*x + a01*y + a02
      y' = a10*x + a11*y + a12

    Args:
        x, y: 原始点。
        matrix: list[list[float]] 形状 (2, 3)。

    Returns:
        (new_x, new_y)。

    Raises:
        ValueError: matrix 形状不是 2×3。
        TypeError: 输入类型错误。
    """
    pass
