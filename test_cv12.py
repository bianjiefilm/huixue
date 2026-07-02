"""CV12 evaluator (v2). 综合项目 schema-validation focus."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv12 import (
    validate_input_image_shape,
    get_pipeline_step_for_subtask,
    recognition_metrics,
    combine_recognition_output,
)

TOL = 1e-6


# F1: validate_input_image_shape
def test_shape_rgb_valid():
    """(28, 28, 3) → True"""
    assert validate_input_image_shape((28, 28, 3)) is True

def test_shape_grayscale_valid():
    """(28, 28, 1) → True"""
    assert validate_input_image_shape((28, 28, 1)) is True

def test_shape_too_small_h():
    """H < min_h → False"""
    assert validate_input_image_shape((4, 28, 3)) is False

def test_shape_too_small_w():
    """W < min_w → False"""
    assert validate_input_image_shape((28, 4, 3)) is False

def test_shape_invalid_channels():
    """C=2 不合法 → False"""
    assert validate_input_image_shape((28, 28, 2)) is False

def test_shape_4_channels():
    """C=4 (RGBA) 不合法 → False"""
    assert validate_input_image_shape((28, 28, 4)) is False

def test_shape_custom_min():
    """(64, 64, 3), min_h=64 min_w=64 → True (boundary 边界)"""
    assert validate_input_image_shape((64, 64, 3), 64, 64) is True

def test_shape_wrong_length():
    """长度 != 3 → False"""
    assert validate_input_image_shape((28, 28)) is False

def test_shape_raises_on_non_tuple():
    with pytest.raises(TypeError):
        validate_input_image_shape("28x28x3")


# F2: get_pipeline_step_for_subtask
def test_subtask_denoise():
    assert get_pipeline_step_for_subtask("denoise") == "gaussian_filter"

def test_subtask_edge():
    assert get_pipeline_step_for_subtask("edge") == "sobel_canny"

def test_subtask_feature():
    assert get_pipeline_step_for_subtask("feature") == "harris_response"

def test_subtask_classify():
    assert get_pipeline_step_for_subtask("classify") == "cnn_softmax"

def test_subtask_detect():
    assert get_pipeline_step_for_subtask("detect") == "bbox_nms"

def test_subtask_segment():
    assert get_pipeline_step_for_subtask("segment") == "binary_threshold"

def test_subtask_raises_on_unknown():
    with pytest.raises(ValueError):
        get_pipeline_step_for_subtask("unknown")

def test_subtask_raises_on_empty():
    """空字符串 boundary"""
    with pytest.raises(ValueError):
        get_pipeline_step_for_subtask("")

def test_subtask_raises_on_non_string():
    with pytest.raises(TypeError):
        get_pipeline_step_for_subtask(123)


# F3: recognition_metrics
def test_metrics_perfect():
    """TP=10, FP=0, FN=0 → precision=1, recall=1, f1=1"""
    r = recognition_metrics(10, 0, 0)
    assert abs(r['precision'] - 1.0) < TOL
    assert abs(r['recall'] - 1.0) < TOL
    assert abs(r['f1'] - 1.0) < TOL

def test_metrics_typical():
    """TP=8, FP=2, FN=4: p=8/10=0.8, r=8/12≈0.667, f1=2*0.8*0.667/(0.8+0.667)≈0.727"""
    r = recognition_metrics(8, 2, 4)
    assert abs(r['precision'] - 0.8) < TOL
    assert abs(r['recall'] - 8.0/12) < TOL
    expected_f1 = 2 * 0.8 * (8.0/12) / (0.8 + 8.0/12)
    assert abs(r['f1'] - expected_f1) < TOL

def test_metrics_high_fp():
    """TP=5, FP=15, FN=0: p=5/20=0.25, r=5/5=1, f1=2*0.25*1/1.25=0.4"""
    r = recognition_metrics(5, 15, 0)
    assert abs(r['precision'] - 0.25) < TOL
    assert abs(r['recall'] - 1.0) < TOL
    assert abs(r['f1'] - 0.4) < TOL

def test_metrics_high_fn():
    """TP=2, FP=0, FN=8: p=1, r=2/10=0.2, f1=2*1*0.2/1.2=1/3"""
    r = recognition_metrics(2, 0, 8)
    assert abs(r['precision'] - 1.0) < TOL
    assert abs(r['recall'] - 0.2) < TOL
    assert abs(r['f1'] - 1.0/3) < TOL

def test_metrics_zero_tp_fp():
    """TP=0, FP=0, FN=5: p=0 (约定), r=0, f1=0"""
    r = recognition_metrics(0, 0, 5)
    assert abs(r['precision'] - 0.0) < TOL
    assert abs(r['recall'] - 0.0) < TOL
    assert abs(r['f1'] - 0.0) < TOL

def test_metrics_all_zero():
    """全 0 → 全 0 (boundary)"""
    r = recognition_metrics(0, 0, 0)
    assert abs(r['precision'] - 0.0) < TOL
    assert abs(r['recall'] - 0.0) < TOL
    assert abs(r['f1'] - 0.0) < TOL

def test_metrics_raises_on_negative():
    with pytest.raises(ValueError):
        recognition_metrics(-1, 0, 0)

def test_metrics_raises_on_non_int():
    with pytest.raises(TypeError):
        recognition_metrics(1.0, 0, 0)


# F4: combine_recognition_output
def test_combine_basic():
    """基本组装"""
    r = combine_recognition_output(3, [10.0, 20.0, 30.0, 40.0], 0.85)
    assert r["class"] == 3
    assert r["bbox"] == [10.0, 20.0, 30.0, 40.0]
    assert abs(r["score"] - 0.85) < TOL

def test_combine_class_five():
    """class=5 (非 hardcode 默认 0)"""
    r = combine_recognition_output(5, [0.0, 0.0, 1.0, 1.0], 0.5)
    assert r["class"] == 5

def test_combine_score_zero():
    """score=0 boundary"""
    r = combine_recognition_output(1, [0.0, 0.0, 1.0, 1.0], 0.0)
    assert abs(r["score"] - 0.0) < TOL

def test_combine_score_one():
    """score=1 boundary"""
    r = combine_recognition_output(2, [0.0, 0.0, 1.0, 1.0], 1.0)
    assert abs(r["score"] - 1.0) < TOL

def test_combine_keys_present():
    """返回 dict 必须包含三个 key 'class' / 'bbox' / 'score'"""
    r = combine_recognition_output(1, [0.0, 0.0, 1.0, 1.0], 0.5)
    assert "class" in r
    assert "bbox" in r
    assert "score" in r

def test_combine_bbox_unchanged():
    """bbox 应原样保留 (元素一一相同)"""
    box = [10.5, 20.5, 30.5, 40.5]
    r = combine_recognition_output(1, box, 0.5)
    assert r["bbox"] == box

def test_combine_raises_on_bad_bbox_length():
    with pytest.raises(ValueError):
        combine_recognition_output(0, [0.0, 0.0, 1.0], 0.5)

def test_combine_raises_on_score_out_of_range():
    with pytest.raises(ValueError):
        combine_recognition_output(0, [0.0, 0.0, 1.0, 1.0], 1.5)

def test_combine_raises_on_negative_class():
    with pytest.raises(ValueError):
        combine_recognition_output(-1, [0.0, 0.0, 1.0, 1.0], 0.5)
