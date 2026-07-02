"""计算机视觉概述与流程 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def classify_cv_task(input_shape, output_type: str) -> str:
    """
    根据输入形状与输出类型判断 CV 任务类别。

    映射规则:
      - 输入 3 维 (H, W, C), output_type='label' → 'classification'
      - 输入 3 维 (H, W, C), output_type='boxes' → 'detection'
      - 输入 3 维 (H, W, C), output_type='mask' → 'pixel_annotation'
      - 输入 3 维 (H, W, C), output_type='id' → 'recognition'

    Args:
        input_shape: list 或 tuple, 长度 3。
        output_type: str ∈ {'label', 'boxes', 'mask', 'id'}。

    Returns:
        str: 任务类别。

    Raises:
        ValueError: shape 长度不对 / output_type 无效。
        TypeError: input_shape 既非 list 也非 tuple, 或 output_type 非 str。
    """
    pass


def compute_image_size_bytes(width: int, height: int, channels: int,
                              bytes_per_pixel: int = 1) -> int:
    """
    计算原始图像存储大小: width * height * channels * bytes_per_pixel。

    Args:
        width, height, channels: 正整数。
        bytes_per_pixel: 每像素字节数 (uint8=1, fp16=2, fp32=4)。

    Returns:
        int: 字节数。

    Raises:
        ValueError: 任一参数非正。
        TypeError: 输入类型错误。
    """
    pass


def resize_aspect_ratio(orig_w: int, orig_h: int, target_max_dim: int) -> Tuple[int, int]:
    """
    保持长宽比缩放: 让最大边等于 target_max_dim。

    ratio = target_max_dim / max(orig_w, orig_h)
    new_w = round(orig_w * ratio), new_h = round(orig_h * ratio)

    Args:
        orig_w, orig_h: 原始尺寸 (>0)。
        target_max_dim: 目标最大边 (>0)。

    Returns:
        (new_w, new_h): 缩放后尺寸。

    Raises:
        ValueError: 任一参数非正。
        TypeError: 输入类型错误。
    """
    pass


def normalize_pixel_array(values: list, max_value: int = 255) -> List[float]:
    """
    把整数像素列表归一化到 [0, 1]: y = x / max_value。

    Args:
        values: list[int], 取值在 [0, max_value]。
        max_value: 像素最大值, 通常 255 (uint8)。

    Returns:
        list[float] 与输入等长, 范围 [0, 1]。

    Raises:
        ValueError: 输入空 / 含越界值 / max_value 非正。
        TypeError: 输入类型错误。
    """
    pass
