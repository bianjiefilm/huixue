"""神经网络与深度学习概述 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def count_dense_parameters(layer_sizes: list) -> int:
    """
    计算全连接网络的参数总数 (含权重 W 与偏置 b)。

    Args:
        layer_sizes: list[int], 每层神经元数量, 长度 >= 1。
                     单层无连接, 返回 0。

    Returns:
        int: 总参数数。

    Raises:
        ValueError: 输入空 / 含非正整数。
        TypeError: 输入不是 list / 含非整数。
    """
    pass


def classify_input_modality(input_shape) -> str:
    """
    根据输入数据 shape 判断模态类别。

    映射规则:
      - 长度 1: 'tabular'
      - 长度 2: 'sequence'
      - 长度 3: 'image'
      - 长度 4: 'video'
      - 其他长度 (含 0 / 5+): 抛 ValueError

    Args:
        input_shape: list 或 tuple, 数据形状。

    Returns:
        str: 'tabular' / 'sequence' / 'image' / 'video' 之一。

    Raises:
        ValueError: shape 长度不在 1-4 之间。
        TypeError: 输入既非 list 也非 tuple。
    """
    pass


def compute_data_split_sizes(total: int, ratios: list) -> List[int]:
    """
    按比例把样本数划分为多段, 返回每段整数大小。

    规则:
      - 各段 size = int(total * ratio_i)
      - 余数补到最后一段, 保证 sum == total

    Args:
        total: 总样本数 (>=0)。
        ratios: list[float], 各段比例, 总和应为 1.0 (容差 1e-6)。

    Returns:
        list[int] 与 ratios 等长, 总和 == total。

    Raises:
        ValueError: total 负 / ratios 总和不为 1 / 含负值 / 空。
        TypeError: 输入类型错误。
    """
    pass


def estimate_param_size_mb(n_params: int) -> float:
    """
    估算 fp32 模型的存储大小 (MB)。

    公式: n_params * 4 bytes / (1024 * 1024)

    Args:
        n_params: 参数总数 (>= 0)。

    Returns:
        float: 存储大小 (MB)。

    Raises:
        ValueError: n_params 负数。
        TypeError: 输入不是整数。
    """
    pass
