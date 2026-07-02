"""目标检测 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def bbox_area(box: List[float]) -> float:
    """
    BBox [x1, y1, x2, y2] 的面积 = (x2-x1) * (y2-y1)。

    Args:
        box: 长度 4 的 list[float], 满足 x1 < x2, y1 < y2。

    Returns:
        float: 面积 (> 0)。

    Raises:
        ValueError: box 长度不是 4 或 x1 >= x2 / y1 >= y2。
        TypeError: 输入类型错误。
    """
    pass


def compute_iou(box_a: List[float], box_b: List[float]) -> float:
    """
    两个 BBox 的 IoU = 交集面积 / 并集面积。

    Args:
        box_a, box_b: [x1, y1, x2, y2] 各长度 4。

    Returns:
        float: IoU ∈ [0.0, 1.0]。

    Raises:
        ValueError: box 形状非法。
        TypeError: 输入类型错误。
    """
    pass


def confidence_threshold_filter(scores: List[float], thresh: float) -> List[int]:
    """
    过滤 score < thresh 的项, 返回保留索引 (升序)。

    Args:
        scores: 1D list[float]。
        thresh: 阈值。

    Returns:
        list[int]: 保留索引升序列表。

    Raises:
        ValueError: scores 空。
        TypeError: 输入类型错误。
    """
    pass


def nms_2d(boxes: List[List[float]], scores: List[float],
           iou_threshold: float) -> List[int]:
    """
    2D BBox NMS:
      1. 按 score 降序排序索引
      2. 选最高 score 的索引加入 keep
      3. 与已 keep 的 IoU > iou_threshold 的索引丢弃
      4. 重复直到所有索引处理完
      5. 返回 keep 升序

    Args:
        boxes: list[list[float]] 每个 4 元素。
        scores: list[float] 同长度 N。
        iou_threshold: 0 < t < 1。

    Returns:
        list[int]: 保留 BBox 的索引 (升序)。

    Raises:
        ValueError: 长度不一致 / iou_threshold 越界。
        TypeError: 输入类型错误。
    """
    pass
