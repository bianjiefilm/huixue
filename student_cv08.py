"""模板匹配 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def template_match_ssd(template: List[float], patch: List[float]) -> float:
    """
    SSD 相似度: 平方差之和。

    Args:
        template: 模板 list[float]。
        patch: 同长度 list[float]。

    Returns:
        float: SSD 值 (>= 0)。

    Raises:
        ValueError: 长度不一致 / 输入空。
        TypeError: 输入类型错误。
    """
    pass


def find_max_correlation(scores: List[float]) -> int:
    """
    找最大相关度位置 (argmax)。

    Args:
        scores: 1D 列表。

    Returns:
        int: 最大值索引 (出现并列时返回最小索引)。

    Raises:
        ValueError: 输入空。
        TypeError: 输入不是 list。
    """
    pass


def non_max_suppression_1d(scores: List[float], radius: int) -> List[int]:
    """
    1D 非极大值抑制: 在抑制半径内只保留局部最大。
    步骤: 反复找 argmax 位置 p, 加入结果列表, 把 [p-radius, p+radius] 范围标为已抑制 (跳过), 直到所有位置处理完。

    Args:
        scores: 1D list[float]。
        radius: 抑制半径 (>= 0)。

    Returns:
        list[int]: 保留的索引升序列表。

    Raises:
        ValueError: 输入空 / radius 非负整数。
        TypeError: 输入类型错误。
    """
    pass


def sliding_window_count(image_size: int, window_size: int, stride: int) -> int:
    """
    1D 滑窗 valid 模式总数 = floor((image_size - window_size) / stride) + 1。

    Args:
        image_size: 图像尺寸 (>= window_size)。
        window_size: 窗口尺寸 (>= 1)。
        stride: 步长 (>= 1)。

    Returns:
        int: 滑窗数。

    Raises:
        ValueError: 参数非正 / window > image。
        TypeError: 输入不是 int。
    """
    pass
