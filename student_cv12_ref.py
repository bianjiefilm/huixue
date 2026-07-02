"""CV12 ref 实现 — 物体识别端到端 4 函数."""
from typing import List, Tuple, Dict


def validate_input_image_shape(shape, min_h=8, min_w=8):
    if not isinstance(min_h, int) or isinstance(min_h, bool):
        raise TypeError("min_h must be int")
    if not isinstance(min_w, int) or isinstance(min_w, bool):
        raise TypeError("min_w must be int")
    if not isinstance(shape, (tuple, list)):
        raise TypeError("shape must be tuple/list")
    if len(shape) != 3:
        return False
    h, w, c = shape
    if not (isinstance(h, int) and isinstance(w, int) and isinstance(c, int)):
        return False
    if c not in (1, 3):
        return False
    if h < min_h or w < min_w:
        return False
    return True


def get_pipeline_step_for_subtask(subtask):
    if not isinstance(subtask, str):
        raise TypeError("subtask must be str")
    mapping = {
        'denoise': 'gaussian_filter',
        'edge': 'sobel_canny',
        'feature': 'harris_response',
        'classify': 'cnn_softmax',
        'detect': 'bbox_nms',
        'segment': 'binary_threshold',
    }
    if subtask not in mapping:
        raise ValueError(f"unknown subtask: {subtask}")
    return mapping[subtask]


def recognition_metrics(tp, fp, fn):
    for name, v in (("tp", tp), ("fp", fp), ("fn", fn)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(f"{name} must be int")
        if v < 0:
            raise ValueError(f"{name} must be >= 0")
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return {'precision': p, 'recall': r, 'f1': f1}


def combine_recognition_output(class_pred, bbox, score):
    if not isinstance(class_pred, int) or isinstance(class_pred, bool):
        raise TypeError("class_pred must be int")
    if class_pred < 0:
        raise ValueError("class_pred must be >= 0")
    if not isinstance(bbox, list):
        raise TypeError("bbox must be list")
    if len(bbox) != 4:
        raise ValueError("bbox length must be 4")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise TypeError("score must be number")
    if score < 0 or score > 1:
        raise ValueError("score out of [0,1]")
    return {'class': class_pred, 'bbox': bbox, 'score': score}
