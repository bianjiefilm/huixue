"""NN06 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn06 import (
    xavier_init,
    he_init,
    check_gradient_health,
    forward_deep,
)

TOL = 1e-4


def _flatten(matrix):
    return [v for row in matrix for v in row]


def _matrix_std(W):
    flat = _flatten(W)
    n = len(flat)
    mean = sum(flat) / n
    var = sum((v - mean) ** 2 for v in flat) / n
    return math.sqrt(var)


def _matrix_max_abs(W):
    return max(abs(v) for v in _flatten(W))


def _matrices_close(W1, W2, tol=1e-9):
    f1, f2 = _flatten(W1), _flatten(W2)
    if len(f1) != len(f2):
        return False
    return all(abs(a - b) < tol for a, b in zip(f1, f2))


# ============================================================
# F1: xavier_init (transform 类, 含统计验证)
# ============================================================

def test_xavier_shape():
    """形状正确"""
    W = xavier_init(3, 4, seed=42)
    assert len(W) == 3
    for row in W:
        assert len(row) == 4

def test_xavier_uniform_bounds():
    """所有元素绝对值 ≤ sqrt(6/(fan_in+fan_out)) (seed=42 防 identity all-0)"""
    W = xavier_init(5, 7, seed=42)
    limit = math.sqrt(6.0 / (5 + 7))
    for v in _flatten(W):
        assert abs(v) <= limit + 1e-6

def test_xavier_std_correct():
    """大矩阵 std ≈ sqrt(2/(fan_in+fan_out))"""
    W = xavier_init(50, 50, seed=42)
    flat = _flatten(W)
    n = len(flat)
    mean = sum(flat) / n
    var = sum((v - mean) ** 2 for v in flat) / n
    std = math.sqrt(var)
    expected_std = math.sqrt(2.0 / (50 + 50))
    # 允许 30% 的统计波动
    assert 0.7 * expected_std < std < 1.3 * expected_std

def test_xavier_deterministic_and_valid():
    """同 seed 同结果 (可复现性) + std > 0.01 (非常量) + max(|W|) < 5 (合理范围)

    设计加强 (非删测试): hardcode return zeros 在 std=0 fail;
    hardcode 常量 0.5 在 std=0 fail; identity all-seed 在 std=0 fail。"""
    W1 = xavier_init(10, 5, seed=42)
    W2 = xavier_init(10, 5, seed=42)
    assert _matrices_close(W1, W2)
    assert _matrix_std(W1) > 0.01
    assert _matrix_max_abs(W1) < 5

def test_xavier_different_seeds_with_validity():
    """不同 seed 不同结果 + 双方 std 都非零 (防 identity 返回常量)"""
    W1 = xavier_init(10, 5, seed=42)
    W2 = xavier_init(10, 5, seed=99)
    assert not _matrices_close(W1, W2)
    assert _matrix_std(W1) > 0.01
    assert _matrix_std(W2) > 0.01

def test_xavier_not_all_zero():
    """xavier 必产生有变化的权重 (防 hardcode 全 0)"""
    W = xavier_init(5, 5, seed=42)
    flat = _flatten(W)
    assert not all(v == 0.0 for v in flat)
    assert any(v > 0 for v in flat) and any(v < 0 for v in flat)

def test_xavier_raises_on_zero_fan():
    with pytest.raises(ValueError):
        xavier_init(0, 5, seed=0)

def test_xavier_raises_on_non_int():
    with pytest.raises(TypeError):
        xavier_init(3.5, 4, seed=0)


# ============================================================
# F2: he_init (transform 类)
# ============================================================

def test_he_shape():
    W = he_init(3, 4, seed=42)
    assert len(W) == 3 and len(W[0]) == 4

def test_he_std_correct():
    """大矩阵 std ≈ sqrt(2/fan_in) — He 公式"""
    W = he_init(100, 50, seed=42)
    flat = _flatten(W)
    n = len(flat)
    mean = sum(flat) / n
    var = sum((v - mean) ** 2 for v in flat) / n
    std = math.sqrt(var)
    expected_std = math.sqrt(2.0 / 100)  # fan_in=100
    assert 0.7 * expected_std < std < 1.3 * expected_std

def test_he_deterministic_and_valid():
    """同 seed 同结果 + std > 0.01 + max(|W|) < 5 (设计加强)"""
    W1 = he_init(10, 5, seed=42)
    W2 = he_init(10, 5, seed=42)
    assert _matrices_close(W1, W2)
    assert _matrix_std(W1) > 0.01
    assert _matrix_max_abs(W1) < 5

def test_he_different_seeds_with_validity():
    """不同 seed 不同结果 + 双方 std 非零"""
    W1 = he_init(10, 5, seed=42)
    W2 = he_init(10, 5, seed=99)
    assert not _matrices_close(W1, W2)
    assert _matrix_std(W1) > 0.01
    assert _matrix_std(W2) > 0.01

def test_he_max_value_reasonable():
    """he 大矩阵 max(|W|) 应在 5σ 内 (5*sqrt(2/fan_in)), 防 identity 返回 seed 值"""
    W = he_init(50, 50, seed=42)
    flat = _flatten(W)
    max_abs = max(abs(v) for v in flat)
    expected_std = math.sqrt(2.0 / 50)
    # 正态分布几乎所有样本在 5σ 内
    assert max_abs < 5 * expected_std

def test_he_not_all_zero():
    """he 必产生有变化的权重 (防 hardcode 全 0)"""
    W = he_init(5, 5, seed=42)
    flat = _flatten(W)
    assert not all(v == 0.0 for v in flat)
    assert any(v > 0 for v in flat) and any(v < 0 for v in flat)

def test_he_raises_on_zero_fan():
    with pytest.raises(ValueError):
        he_init(5, 0, seed=0)

def test_he_raises_on_non_int():
    with pytest.raises(TypeError):
        he_init(3, "4", seed=0)


# ============================================================
# F3: check_gradient_health (5 键 dict 全验)
# ============================================================

def test_cgh_healthy():
    """健康梯度: [0.1, -0.2, 0.05] → mean/std 合理, 无 vanishing/exploding"""
    r = check_gradient_health([0.1, -0.2, 0.05])
    assert "mean" in r and "std" in r and "max_abs" in r
    assert "has_vanishing" in r and "has_exploding" in r
    assert r["has_vanishing"] is False
    assert r["has_exploding"] is False
    assert abs(r["mean"] - (-0.05/3)) < TOL
    assert abs(r["max_abs"] - 0.2) < TOL

def test_cgh_vanishing():
    """全极小值 mean(|grad|) < 1e-7 → has_vanishing=True"""
    r = check_gradient_health([1e-9, -1e-9, 5e-10])
    assert r["has_vanishing"] is True
    assert r["has_exploding"] is False

def test_cgh_exploding():
    """含极大值 max(|grad|) > 1e3 → has_exploding=True"""
    r = check_gradient_health([0.1, 1e5, -0.2])
    assert r["has_exploding"] is True
    assert abs(r["max_abs"] - 1e5) < TOL

def test_cgh_specific_values():
    """[1, 2, 3] mean=2, std=sqrt(2/3) (population), max_abs=3"""
    r = check_gradient_health([1, 2, 3])
    assert abs(r["mean"] - 2.0) < TOL
    assert abs(r["std"] - math.sqrt(2/3)) < TOL
    assert abs(r["max_abs"] - 3.0) < TOL

def test_cgh_negative_max_abs():
    """[-5, -3, -1] max_abs=5 (绝对值)"""
    r = check_gradient_health([-5, -3, -1])
    assert abs(r["max_abs"] - 5.0) < TOL

def test_cgh_zero_grad():
    """全 0 → has_vanishing=True (mean=0 < 1e-7)"""
    r = check_gradient_health([0, 0, 0])
    assert r["has_vanishing"] is True
    assert r["max_abs"] == 0.0

def test_cgh_raises_on_empty():
    with pytest.raises(ValueError):
        check_gradient_health([])

def test_cgh_raises_on_non_list():
    with pytest.raises(TypeError):
        check_gradient_health("abc")


# ============================================================
# F4: forward_deep (transform 类, 多层链式)
# ============================================================

def test_fd_two_layers_relu_sigmoid():
    """X=[[1]], W1=[[1]], b1=[0], relu → 1; W2=[[1]], b2=[0], sigmoid → σ(1)"""
    out = forward_deep(
        [[1]],
        [[[1]], [[1]]],
        [[0], [0]],
        ["relu", "sigmoid"]
    )
    assert abs(out[0][0] - 0.7310585786) < TOL

def test_fd_three_layers_all_relu():
    """X=[[1]], 三层都 W=[[2]], b=[0], relu → 1*2*2*2 = 8"""
    out = forward_deep(
        [[1]],
        [[[2]], [[2]], [[2]]],
        [[0], [0], [0]],
        ["relu", "relu", "relu"]
    )
    assert abs(out[0][0] - 8.0) < TOL

def test_fd_with_negative_relu_kills_then_bias():
    """X=[[-1]], relu 杀负 → 0; 第二层 b=3 linear → 3 (避 0 巧合)"""
    out = forward_deep(
        [[-1]],
        [[[1]], [[5]]],
        [[0], [3]],
        ["relu", "linear"]
    )
    assert abs(out[0][0] - 3.0) < TOL

def test_fd_linear_activation():
    """linear (no activation): X=[[2]], W=[[3]], b=[1], linear → 7"""
    out = forward_deep([[2]], [[[3]]], [[1]], ["linear"])
    assert abs(out[0][0] - 7.0) < TOL

def test_fd_tanh_layer():
    """X=[[1]], W=[[1]], b=[0], tanh → tanh(1)"""
    out = forward_deep([[1]], [[[1]]], [[0]], ["tanh"])
    assert abs(out[0][0] - math.tanh(1)) < TOL

def test_fd_raises_on_length_mismatch():
    """weights/biases/activations 长度不一致"""
    with pytest.raises(ValueError):
        forward_deep([[1]], [[[1]]], [[0], [0]], ["relu"])

def test_fd_raises_on_invalid_activation():
    with pytest.raises(ValueError):
        forward_deep([[1]], [[[1]]], [[0]], ["xxx"])

def test_fd_raises_on_non_list():
    with pytest.raises(TypeError):
        forward_deep("abc", [[[1]]], [[0]], ["relu"])
