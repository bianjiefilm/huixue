"""特征检测 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def harris_response_single(Ixx: float, Iyy: float, Ixy: float, k: float = 0.04) -> float:
    """
    Harris 角点响应 R 值 (单个像素位置)。

    Args:
        Ixx, Iyy, Ixy: 结构张量元素。
        k: 经验常数, 默认 0.04。

    Returns:
        float: 响应值 R。

    Raises:
        TypeError: 输入不是数值。
    """
    pass


def sift_block_descriptor_dim(num_orientations: int, num_blocks: int) -> int:
    """
    SIFT 风格描述子总维度 = 方向数 × 子块数。
    标准 SIFT: num_orientations=8, num_blocks=16 (= 4x4 grid), 总维度 = 128。

    Args:
        num_orientations: 每子块的方向 bin 数 (>= 1)。
        num_blocks: 子块数 (>= 1)。

    Returns:
        int: 总描述子维度。

    Raises:
        ValueError: 输入非正。
        TypeError: 输入不是 int。
    """
    pass


def extrema_check_3x3(window: List[List[float]]) -> str:
    """
    判断 3x3 窗口的中心 (1,1) 是否为局部极值。
    严格大于所有 8 邻居 → 'max'
    严格小于所有 8 邻居 → 'min'
    其他 → 'neither'

    Args:
        window: list[list[float]] 形状 (3, 3)。

    Returns:
        str: 'max' / 'min' / 'neither'。

    Raises:
        ValueError: 形状不是 3x3。
        TypeError: 输入不是 list。
    """
    pass


def hessian_2x2_eigenvalues(a: float, b: float, d: float) -> Tuple[float, float]:
    """
    对称 Hessian H = [[a, b], [b, d]] 的两个特征值。

    Args:
        a, b, d: 矩阵元素。

    Returns:
        (lambda_1, lambda_2): 大的在前, 小的在后。

    Raises:
        TypeError: 输入不是数值。
    """
    pass
