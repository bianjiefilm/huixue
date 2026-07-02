"""形态学操作 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def erode_1d(values: List[int], kernel_size: int = 3) -> List[int]:
    """
    1D 二值腐蚀 (full-1 SE, valid 模式)。
    输入长度 N, 输出长度 N - kernel_size + 1。

    Args:
        values: list[int], 元素 0 或 1。
        kernel_size: 奇数 (>= 1)。

    Returns:
        list[int]: 0/1 列表, 长度 N - kernel_size + 1。

    Raises:
        ValueError: kernel_size 偶数 / 非正 / 大于 N / 元素不在 {0,1}。
        TypeError: 输入类型错误。
    """
    pass


def dilate_1d(values: List[int], kernel_size: int = 3) -> List[int]:
    """
    1D 二值膨胀 (full-1 SE, valid 模式)。
    输入长度 N, 输出长度 N - kernel_size + 1。

    Args:
        values: list[int], 元素 0 或 1。
        kernel_size: 奇数 (>= 1)。

    Returns:
        list[int]: 0/1 列表, 长度 N - kernel_size + 1。

    Raises:
        ValueError: kernel_size 偶数 / 非正 / 大于 N / 元素不在 {0,1}。
        TypeError: 输入类型错误。
    """
    pass


def get_morph_operation_order(operation: str) -> str:
    """
    返回形态学操作的执行顺序描述字符串。

    输入对应输出:
      'erosion'  → 'erosion'
      'dilation' → 'dilation'
      'opening'  → 'erosion_then_dilation'
      'closing'  → 'dilation_then_erosion'

    Args:
        operation: 操作名 (上述 4 个之一)。

    Returns:
        str: 顺序描述。

    Raises:
        ValueError: 未知操作名。
        TypeError: 输入不是字符串。
    """
    pass


def get_cross_se_3x3() -> List[List[int]]:
    """
    返回 3×3 十字结构元 (center + 上下左右 4 邻, 4 角为 0)。

    Returns:
        list[list[int]]: 形状 (3, 3), 角为 0, 中心+四邻为 1。
    """
    pass
