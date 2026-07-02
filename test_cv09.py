"""CV09 evaluator (v2)."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_cv09 import (
    conv_layer_param_count,
    conv_output_size_2d,
    softmax_predict,
    cross_entropy_loss_single,
)

TOL = 1e-6


# F1: conv_layer_param_count = in*out*kh*kw + (out if bias else 0)
def test_conv_param_lenet_conv1():
    """LeNet Conv1 (1→6, 5×5, bias) = 1*6*25 + 6 = 156"""
    assert conv_layer_param_count(1, 6, 5, 5, True) == 156

def test_conv_param_vgg_block():
    """VGG (64→128, 3×3, bias) = 64*128*9 + 128 = 73856"""
    assert conv_layer_param_count(64, 128, 3, 3, True) == 73856

def test_conv_param_no_bias():
    """LeNet Conv1 无 bias: 1*6*25 = 150"""
    assert conv_layer_param_count(1, 6, 5, 5, False) == 150

def test_conv_param_1x1():
    """1×1 卷积 (32→64, bias) = 32*64 + 64 = 2112"""
    assert conv_layer_param_count(32, 64, 1, 1, True) == 2112

def test_conv_param_boundary_small():
    """边界: 1→2 3×1 无 bias = 1*2*3*1 = 6 (Shape: 1*2=2 不同)"""
    assert conv_layer_param_count(1, 2, 3, 1, False) == 6

def test_conv_param_default_bias_true():
    """bias 默认 True: 1*6*25 + 6 = 156"""
    assert conv_layer_param_count(1, 6, 5, 5) == 156

def test_conv_param_raises_on_zero():
    with pytest.raises(ValueError):
        conv_layer_param_count(0, 6, 5, 5)

def test_conv_param_raises_on_non_int():
    with pytest.raises(TypeError):
        conv_layer_param_count(1.0, 6, 5, 5)


# F2: conv_output_size_2d. (H + 2p - k)/s + 1
def test_conv_output_lenet():
    """28×28, k=5, p=0, s=1 → 24×24"""
    h, w = conv_output_size_2d(28, 28, 5, 0, 1)
    assert h == 24
    assert w == 24

def test_conv_output_same_padding():
    """32×32, k=3, p=1, s=1 → 32×32 (same)"""
    h, w = conv_output_size_2d(32, 32, 3, 1, 1)
    assert h == 32
    assert w == 32

def test_conv_output_stride_2():
    """32×32, k=3, p=1, s=2 → 16×16 (downsample)"""
    h, w = conv_output_size_2d(32, 32, 3, 1, 2)
    assert h == 16
    assert w == 16

def test_conv_output_imagenet():
    """224×224, k=7, p=3, s=2 → (224+6-7)/2+1 = 112"""
    h, w = conv_output_size_2d(224, 224, 7, 3, 2)
    assert h == 112
    assert w == 112

def test_conv_output_raises_on_too_small():
    with pytest.raises(ValueError):
        conv_output_size_2d(3, 3, 5, 0, 1)  # 输出会是 -1

def test_conv_output_raises_on_non_int():
    with pytest.raises(TypeError):
        conv_output_size_2d(28.0, 28, 3, 0, 1)


# F3: softmax_predict (argmax of logits)
def test_softmax_simple():
    """[1, 5, 3] → 1"""
    assert softmax_predict([1.0, 5.0, 3.0]) == 1

def test_softmax_last():
    """[1, 2, 9] → 2"""
    assert softmax_predict([1.0, 2.0, 9.0]) == 2

def test_softmax_negative_argmax_middle():
    """[-5, -1, -3] → 1 (-1 最大)"""
    assert softmax_predict([-5.0, -1.0, -3.0]) == 1

def test_softmax_ties_first():
    """并列取最小: [3, 5, 5] → 1"""
    assert softmax_predict([3.0, 5.0, 5.0]) == 1

def test_softmax_two_class():
    """[0.5, 2.0] → 1 (boundary 二分类)"""
    assert softmax_predict([0.5, 2.0]) == 1

def test_softmax_raises_on_empty():
    with pytest.raises(ValueError):
        softmax_predict([])

def test_softmax_raises_on_non_list():
    with pytest.raises(TypeError):
        softmax_predict("abc")


# F4: cross_entropy_loss_single. -ln(probs[label])
def test_ce_high_conf_label_1():
    """probs=[0.05, 0.9, 0.05], label=1 → -ln(0.9) (probs[0]≠probs[label])"""
    r = cross_entropy_loss_single([0.05, 0.9, 0.05], 1)
    assert abs(r - (-math.log(0.9))) < TOL

def test_ce_high_conf_label_2():
    """probs=[0.05, 0.05, 0.9], label=2 → -ln(0.9)"""
    r = cross_entropy_loss_single([0.05, 0.05, 0.9], 2)
    assert abs(r - (-math.log(0.9))) < TOL

def test_ce_wrong_class():
    """probs=[0.9, 0.05, 0.05], label=1 → -ln(0.05) ≈ 2.9957"""
    r = cross_entropy_loss_single([0.9, 0.05, 0.05], 1)
    assert abs(r - (-math.log(0.05))) < TOL

def test_ce_two_class_label_1():
    """probs=[0.7, 0.3], label=1 → -ln(0.3) (boundary 二分类)"""
    r = cross_entropy_loss_single([0.7, 0.3], 1)
    assert abs(r - (-math.log(0.3))) < TOL

def test_ce_skewed_label_3():
    """probs=[0.1, 0.2, 0.3, 0.4], label=3 → -ln(0.4)"""
    r = cross_entropy_loss_single([0.1, 0.2, 0.3, 0.4], 3)
    assert abs(r - (-math.log(0.4))) < TOL

def test_ce_skewed_label_2():
    """同上 label=2 → -ln(0.3)"""
    r = cross_entropy_loss_single([0.1, 0.2, 0.3, 0.4], 2)
    assert abs(r - (-math.log(0.3))) < TOL

def test_ce_raises_on_label_out_of_range():
    with pytest.raises(ValueError):
        cross_entropy_loss_single([0.5, 0.5], 2)

def test_ce_raises_on_non_list():
    with pytest.raises(TypeError):
        cross_entropy_loss_single("abc", 0)
