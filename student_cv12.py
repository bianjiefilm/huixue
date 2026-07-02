"""综合项目: 物体识别端到端 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple, Dict


def validate_input_image_shape(shape: Tuple[int, int, int],
                               min_h: int = 8, min_w: int = 8) -> bool:
    """
    校验图像 shape (H, W, C) 是否符合流水线输入要求:
    - 必须是长度 3 的 tuple/list
    - C ∈ {1, 3}
    - H >= min_h, W >= min_w

    Args:
        shape: (H, W, C) 长度 3。
        min_h, min_w: 最小允许尺寸 (>= 1)。

    Returns:
        bool: True if 合法, False otherwise。

    Raises:
        TypeError: shape 不是 tuple/list 或 min_h/min_w 不是 int。
    """
    pass


def get_pipeline_step_for_subtask(subtask: str) -> str:
    """
    子任务名称到 CV 课程算法名的映射。

    支持的输入:
      'denoise' → 'gaussian_filter'
      'edge' → 'sobel_canny'
      'feature' → 'harris_response'
      'classify' → 'cnn_softmax'
      'detect' → 'bbox_nms'
      'segment' → 'binary_threshold'

    Args:
        subtask: 上述 6 个之一。

    Returns:
        str: 对应算法名。

    Raises:
        ValueError: 未知子任务。
        TypeError: 输入不是字符串。
    """
    pass


def recognition_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """
    给定 TP / FP / FN, 计算 {'precision': p, 'recall': r, 'f1': f}。

    特殊情况 (避免 0/0):
    - TP+FP = 0 → precision = 0
    - TP+FN = 0 → recall = 0
    - precision + recall = 0 → f1 = 0

    Args:
        tp, fp, fn: 非负整数。

    Returns:
        {'precision': float, 'recall': float, 'f1': float}, 各 ∈ [0, 1]。

    Raises:
        ValueError: 任一参数 < 0。
        TypeError: 输入不是 int。
    """
    pass


def combine_recognition_output(class_pred: int, bbox: List[float],
                               score: float) -> Dict:
    """
    把识别结果组装成统一 dict: {'class': class_pred, 'bbox': bbox, 'score': score}。

    Args:
        class_pred: 类别索引 (>= 0)。
        bbox: [x1, y1, x2, y2] 长度 4。
        score: 置信度 ∈ [0, 1]。

    Returns:
        dict: 三个 key 'class', 'bbox', 'score'。

    Raises:
        ValueError: bbox 长度不是 4 / score 越界 / class_pred < 0。
        TypeError: 输入类型错误。
    """
    pass
