"""NN05 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn05 import (
    forward_propagate,
    backward_propagate,
    predict_labels,
    compute_accuracy_binary,
)

TOL = 1e-4
SIG1 = 0.7310585786  # sigmoid(1)
NSIG1 = 0.2689414214  # 1 - sigmoid(1)


# ============================================================
# F1: forward_propagate (transform 类, 4-tuple)
# ============================================================

def test_fp_zero_input():
    """X=[[0]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[0]] a1=[[0]] z2=[[0]] a2=[[0.5]]"""
    z1, a1, z2, a2 = forward_propagate([[0]], [[1]], [0], [[1]], [0])
    assert abs(z1[0][0] - 0.0) < TOL
    assert abs(a1[0][0] - 0.0) < TOL
    assert abs(z2[0][0] - 0.0) < TOL
    assert abs(a2[0][0] - 0.5) < TOL

def test_fp_unit_input():
    """X=[[1]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[1]] a1=[[1]] z2=[[1]] a2=[[σ(1)]]"""
    z1, a1, z2, a2 = forward_propagate([[1]], [[1]], [0], [[1]], [0])
    assert abs(z1[0][0] - 1.0) < TOL
    assert abs(a1[0][0] - 1.0) < TOL
    assert abs(z2[0][0] - 1.0) < TOL
    assert abs(a2[0][0] - SIG1) < TOL

def test_fp_negative_z1_relu_zeros():
    """X=[[-2]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[-2]] a1=[[0]] (ReLU 截断)"""
    z1, a1, z2, a2 = forward_propagate([[-2]], [[1]], [0], [[1]], [0])
    assert abs(z1[0][0] - (-2.0)) < TOL
    assert abs(a1[0][0] - 0.0) < TOL
    assert abs(z2[0][0] - 0.0) < TOL  # 0 * 1 + 0 = 0
    assert abs(a2[0][0] - 0.5) < TOL  # σ(0) = 0.5

def test_fp_two_by_two():
    """X=[[1,0],[0,1]] W1=I W2=[[1],[1]] b=0 → 详见 handbook 推导"""
    z1, a1, z2, a2 = forward_propagate(
        [[1, 0], [0, 1]], [[1, 0], [0, 1]], [0, 0], [[1], [1]], [0]
    )
    # z1 should be [[1,0],[0,1]]
    expected_z1 = [[1.0, 0.0], [0.0, 1.0]]
    for i in range(2):
        for j in range(2):
            assert abs(z1[i][j] - expected_z1[i][j]) < TOL
    # a1 should be [[1,0],[0,1]] (ReLU keeps)
    for i in range(2):
        for j in range(2):
            assert abs(a1[i][j] - expected_z1[i][j]) < TOL
    # z2 = [[1+0],[0+1]] = [[1],[1]]
    assert abs(z2[0][0] - 1.0) < TOL and abs(z2[1][0] - 1.0) < TOL
    # a2 = σ(1) twice
    assert abs(a2[0][0] - SIG1) < TOL and abs(a2[1][0] - SIG1) < TOL

def test_fp_with_bias():
    """X=[[0]] W1=[[1]] b1=[5] W2=[[1]] b2=[3] → z1=[[5]] a1=[[5]] z2=[[8]] a2=[[σ(8)]]"""
    z1, a1, z2, a2 = forward_propagate([[0]], [[1]], [5], [[1]], [3])
    assert abs(z1[0][0] - 5.0) < TOL
    assert abs(a1[0][0] - 5.0) < TOL
    assert abs(z2[0][0] - 8.0) < TOL
    expected_a2 = 1.0 / (1.0 + math.exp(-8))
    assert abs(a2[0][0] - expected_a2) < TOL

def test_fp_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        forward_propagate([[1, 2]], [[1]], [0], [[1]], [0])

def test_fp_raises_on_empty():
    with pytest.raises(ValueError):
        forward_propagate([], [[1]], [0], [[1]], [0])

def test_fp_raises_on_non_list():
    with pytest.raises(TypeError):
        forward_propagate("abc", [[1]], [0], [[1]], [0])


# ============================================================
# F2: backward_propagate (transform 类, 4-tuple multi-output)
# ============================================================

def test_bp_textbook_2x2():
    """与 handbook 一致的 2x2 案例: 完整反向梯度
    y=[1,0], a2=[[σ(1)],[σ(1)]] → dz2=[[σ(1)-1],[σ(1)]]
    """
    z1 = [[1, 0], [0, 1]]
    a1 = [[1, 0], [0, 1]]
    a2 = [[SIG1], [SIG1]]
    W2 = [[1], [1]]
    X = [[1, 0], [0, 1]]
    y = [1, 0]
    dW1, db1, dW2, db2 = backward_propagate(X, y, z1, a1, a2, W2)
    # dz2 = a2 - y = [[σ(1)-1], [σ(1)]] = [[-0.2689], [0.7311]]
    # dW2 = a1.T @ dz2 / 2 = [[-0.2689/2], [0.7311/2]] = [[-0.13447], [0.36553]]
    assert abs(dW2[0][0] - (-NSIG1 / 2)) < TOL
    assert abs(dW2[1][0] - (SIG1 / 2)) < TOL
    # db2 = mean(dz2) = (SIG1 - 1 + SIG1) / 2 = SIG1 - 0.5
    expected_db2 = (SIG1 - 1 + SIG1) / 2
    assert abs(db2[0] - expected_db2) < TOL

def test_bp_zero_loss_gradient():
    """y=a2 → dz2=0 → 所有梯度=0"""
    a2 = [[0.5], [0.5]]
    y = [0, 0]  # 注意: a2=0.5 - y=0 → dz2=0.5, NOT zero
    # Recompute: y=[1,0] vs a2=[[1.0], [0.0]] → dz2 = 0
    # 用 sigmoid 输出几乎 1 / 0 模拟
    a2 = [[0.99999999], [0.00000001]]
    y = [1, 0]
    z1 = [[1.0], [-1.0]]
    a1 = [[1.0], [0.0]]
    W2 = [[1]]
    X = [[1], [1]]
    dW1, db1, dW2, db2 = backward_propagate(X, y, z1, a1, a2, W2)
    # dz2 ≈ 0 → dW2 ≈ 0
    assert abs(dW2[0][0]) < 1e-6
    assert abs(db2[0]) < 1e-6

def test_bp_relu_mask_zeros_negative():
    """z1 含负值, ReLU 反向 mask 应让对应 dz1 = 0"""
    X = [[1]]
    y = [1]
    z1 = [[-2.0]]  # 负值
    a1 = [[0.0]]   # ReLU 后 0
    a2 = [[0.5]]
    W2 = [[1]]
    dW1, db1, dW2, db2 = backward_propagate(X, y, z1, a1, a2, W2)
    # dz2 = a2 - y = -0.5
    # da1 = dz2 @ W2.T = [[-0.5]]
    # dz1 = da1 * (z1>0) = [[-0.5 * 0]] = [[0]] → dW1 = 0
    assert abs(dW1[0][0]) < TOL
    # db1 = mean(dz1) = 0
    assert abs(db1[0]) < TOL

def test_bp_dW2_shape():
    """dW2 形状必须 (h, 1)"""
    z1 = [[1, 2], [3, 4]]
    a1 = [[1, 2], [3, 4]]
    a2 = [[0.5], [0.5]]
    W2 = [[1], [1]]
    X = [[1, 1], [1, 1]]
    y = [1, 0]
    dW1, db1, dW2, db2 = backward_propagate(X, y, z1, a1, a2, W2)
    assert len(dW2) == 2 and len(dW2[0]) == 1
    assert len(dW1) == 2 and len(dW1[0]) == 2
    assert len(db1) == 2
    assert len(db2) == 1

def test_bp_raises_on_dim_mismatch():
    """y 长度 2 vs X 长度 1 → ValueError"""
    with pytest.raises(ValueError):
        backward_propagate([[1]], [1, 0], [[1]], [[1]], [[0.5]], [[1]])

def test_bp_raises_on_empty():
    with pytest.raises(ValueError):
        backward_propagate([], [], [], [], [], [[1]])

def test_bp_raises_on_non_list():
    with pytest.raises(TypeError):
        backward_propagate("ab", [0, 1], [[1]], [[1]], [[0.5]], [[1]])


# ============================================================
# F3: predict_labels (transform 类)
# ============================================================

def test_pl_basic():
    """[[0.1],[0.5],[0.9]] → [0, 1, 1] (0.5 边界 >=)"""
    assert predict_labels([[0.1], [0.5], [0.9]]) == [0, 1, 1]

def test_pl_high_threshold():
    """阈值 0.95: [[0.5],[0.99]] → [0, 1]"""
    assert predict_labels([[0.5], [0.99]], threshold=0.95) == [0, 1]

def test_pl_low_threshold():
    """阈值 0.1: [[0.05],[0.2]] → [0, 1]"""
    assert predict_labels([[0.05], [0.2]], threshold=0.1) == [0, 1]

def test_pl_all_above():
    """全部 >= 0.5 → 全 1"""
    assert predict_labels([[0.6], [0.7], [0.8]]) == [1, 1, 1]

def test_pl_all_below():
    """全部 < 0.5 → 全 0"""
    assert predict_labels([[0.1], [0.2], [0.3]]) == [0, 0, 0]

def test_pl_raises_on_wrong_shape():
    """非 (N, 1) 形状 → ValueError"""
    with pytest.raises(ValueError):
        predict_labels([[0.5, 0.5]])

def test_pl_raises_on_empty():
    """空列表 → ValueError"""
    with pytest.raises(ValueError):
        predict_labels([])

def test_pl_raises_on_non_list():
    with pytest.raises(TypeError):
        predict_labels("abc")


# ============================================================
# F4: compute_accuracy_binary
# ============================================================

def test_acc_perfect():
    """全对 → 1.0"""
    assert abs(compute_accuracy_binary([1, 0, 1, 0], [1, 0, 1, 0]) - 1.0) < TOL

def test_acc_all_wrong():
    """全错 → 0.0"""
    assert abs(compute_accuracy_binary([1, 0, 1, 0], [0, 1, 0, 1]) - 0.0) < TOL

def test_acc_three_quarters():
    """3/4 对 → 0.75"""
    assert abs(compute_accuracy_binary([1, 0, 1, 0], [1, 0, 1, 1]) - 0.75) < TOL

def test_acc_half():
    """1/2 对 → 0.5"""
    assert abs(compute_accuracy_binary([1, 1, 0, 0], [1, 0, 1, 0]) - 0.5) < TOL

def test_acc_one_third():
    """1/3 对 → 1/3"""
    assert abs(compute_accuracy_binary([1, 1, 1], [1, 0, 0]) - 1 / 3) < TOL

def test_acc_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        compute_accuracy_binary([1, 0], [1])

def test_acc_raises_on_empty():
    with pytest.raises(ValueError):
        compute_accuracy_binary([], [])

def test_acc_raises_on_invalid_label():
    with pytest.raises(ValueError):
        compute_accuracy_binary([1, 2], [1, 0])
