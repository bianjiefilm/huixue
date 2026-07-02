"""CV12 综合关 pytest_module 测试."""
import pytest
from student_cv12 import (
    validate_input_image_shape,
    get_pipeline_step_for_subtask,
    recognition_metrics,
    combine_recognition_output,
)

TOL = 1e-6


# F1: validate_input_image_shape (8 cases)
def test_viis_valid_rgb():
    assert validate_input_image_shape((224, 224, 3)) is True

def test_viis_valid_grayscale():
    assert validate_input_image_shape((28, 28, 1)) is True

def test_viis_invalid_shape_length():
    assert validate_input_image_shape((224, 224)) is False

def test_viis_invalid_channel():
    assert validate_input_image_shape((224, 224, 4)) is False

def test_viis_too_small():
    assert validate_input_image_shape((4, 4, 3)) is False

def test_viis_custom_min():
    assert validate_input_image_shape((100, 100, 3), min_h=50, min_w=50) is True
    assert validate_input_image_shape((40, 40, 3), min_h=50, min_w=50) is False

def test_viis_raises_on_non_tuple():
    with pytest.raises(TypeError):
        validate_input_image_shape("abc")

def test_viis_raises_on_non_int_min():
    with pytest.raises(TypeError):
        validate_input_image_shape((100, 100, 3), min_h="50")


# F2: get_pipeline_step_for_subtask (8 cases)
def test_gpss_denoise():
    assert get_pipeline_step_for_subtask("denoise") == "gaussian_filter"

def test_gpss_edge():
    assert get_pipeline_step_for_subtask("edge") == "sobel_canny"

def test_gpss_feature():
    assert get_pipeline_step_for_subtask("feature") == "harris_response"

def test_gpss_classify():
    assert get_pipeline_step_for_subtask("classify") == "cnn_softmax"

def test_gpss_detect():
    assert get_pipeline_step_for_subtask("detect") == "bbox_nms"

def test_gpss_segment():
    assert get_pipeline_step_for_subtask("segment") == "binary_threshold"

def test_gpss_raises_on_unknown():
    with pytest.raises(ValueError):
        get_pipeline_step_for_subtask("unknown_xx")

def test_gpss_raises_on_non_str():
    with pytest.raises(TypeError):
        get_pipeline_step_for_subtask(42)


# F3: recognition_metrics (7 cases)
def test_rm_perfect():
    r = recognition_metrics(10, 0, 0)
    assert abs(r['precision'] - 1.0) < TOL
    assert abs(r['recall'] - 1.0) < TOL
    assert abs(r['f1'] - 1.0) < TOL

def test_rm_balanced():
    # tp=8 fp=2 fn=2 → p=0.8 r=0.8 f1=0.8
    r = recognition_metrics(8, 2, 2)
    assert abs(r['precision'] - 0.8) < TOL
    assert abs(r['recall'] - 0.8) < TOL
    assert abs(r['f1'] - 0.8) < TOL

def test_rm_zero_tp():
    # tp=0 fp=5 fn=5 → p=r=f1=0
    r = recognition_metrics(0, 5, 5)
    assert r['precision'] == 0
    assert r['recall'] == 0
    assert r['f1'] == 0

def test_rm_no_predictions():
    # tp=fp=0 fn=10 → p=0 r=0 f1=0
    r = recognition_metrics(0, 0, 10)
    assert r['precision'] == 0
    assert r['recall'] == 0

def test_rm_no_groundtruth():
    # tp=fn=0 fp=5 → r=0
    r = recognition_metrics(0, 5, 0)
    assert r['recall'] == 0

def test_rm_raises_on_negative():
    with pytest.raises(ValueError):
        recognition_metrics(-1, 0, 0)

def test_rm_raises_on_non_int():
    with pytest.raises(TypeError):
        recognition_metrics(1.5, 0, 0)


# F4: combine_recognition_output (7 cases)
def test_cro_basic():
    r = combine_recognition_output(3, [10.0, 20.0, 30.0, 40.0], 0.95)
    assert r == {'class': 3, 'bbox': [10.0, 20.0, 30.0, 40.0], 'score': 0.95}

def test_cro_zero_class():
    r = combine_recognition_output(0, [0.0, 0.0, 1.0, 1.0], 0.5)
    assert r['class'] == 0

def test_cro_score_extremes():
    r = combine_recognition_output(1, [1.0, 2.0, 3.0, 4.0], 0.0)
    assert r['score'] == 0.0
    r = combine_recognition_output(1, [1.0, 2.0, 3.0, 4.0], 1.0)
    assert r['score'] == 1.0

def test_cro_raises_on_neg_class():
    with pytest.raises(ValueError):
        combine_recognition_output(-1, [0, 0, 1, 1], 0.5)

def test_cro_raises_on_bbox_len():
    with pytest.raises(ValueError):
        combine_recognition_output(1, [0, 0, 1], 0.5)

def test_cro_raises_on_score_oor():
    with pytest.raises(ValueError):
        combine_recognition_output(1, [0, 0, 1, 1], 1.5)

def test_cro_raises_on_non_list_bbox():
    with pytest.raises(TypeError):
        combine_recognition_output(1, "not a list", 0.5)
