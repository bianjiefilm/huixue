"""NN10 evaluator (v2)."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn10 import (
    rnn_single_step,
    lstm_gates,
    gru_gates,
    compute_sequence_length_after_truncate,
)

TOL = 1e-4


# F1: rnn_single_step
def test_rnn_zero_input_zero_hidden():
    """tanh(0+0+0) = 0"""
    h = rnn_single_step([0.0], [0.0], [[1.0]], [[1.0]], [0.0])
    assert abs(h[0] - 0.0) < TOL

def test_rnn_unit_input():
    """x=[1] h=[0] W_xh=[[1]] W_hh=[[1]] b=[0] → tanh(1) ≈ 0.7616"""
    h = rnn_single_step([1.0], [0.0], [[1.0]], [[1.0]], [0.0])
    assert abs(h[0] - math.tanh(1.0)) < TOL

def test_rnn_with_hidden():
    """x=[0] h=[2] W_hh=[[0.5]] b=[0] → tanh(0+1+0)=tanh(1)"""
    h = rnn_single_step([0.0], [2.0], [[1.0]], [[0.5]], [0.0])
    assert abs(h[0] - math.tanh(1.0)) < TOL

def test_rnn_two_dim():
    """x=[1,1] h=[0,0], W_xh=[[1,0],[0,1]] (id), W_hh=[[0,0],[0,0]] (zero), b=[0,0]
    → tanh([1, 1]) = [tanh(1), tanh(1)]"""
    h = rnn_single_step([1.0, 1.0], [0.0, 0.0],
                        [[1.0, 0.0], [0.0, 1.0]],
                        [[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0])
    assert abs(h[0] - math.tanh(1.0)) < TOL
    assert abs(h[1] - math.tanh(1.0)) < TOL

def test_rnn_with_bias():
    """x=[0] h=[0] b=[5] → tanh(5) ≈ 0.9999"""
    h = rnn_single_step([0.0], [0.0], [[1.0]], [[1.0]], [5.0])
    assert abs(h[0] - math.tanh(5.0)) < TOL

def test_rnn_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        rnn_single_step([1.0, 2.0], [0.0], [[1.0]], [[1.0]], [0.0])

def test_rnn_raises_on_empty():
    with pytest.raises(ValueError):
        rnn_single_step([], [], [], [], [])

def test_rnn_raises_on_non_list():
    with pytest.raises(TypeError):
        rnn_single_step("ab", [0.0], [[1.0]], [[1.0]], [0.0])


# F2: lstm_gates
def test_lstm_basic():
    """x=[1], h=[0], 4 门各自 W=[[0.5],[0.3]] (concat 2 dim → 1 hidden)
    concat = [1, 0]
    z = 1*0.5 + 0*0.3 + 0 = 0.5
    i = sigmoid(0.5) ≈ 0.6225
    f = sigmoid(0.5) ≈ 0.6225 (用相同 W, 不同 b 区分)
    o = sigmoid(0.5) ≈ 0.6225
    g = tanh(0.5) ≈ 0.4621
    """
    W = [[[0.5], [0.3]]] * 4  # 4 门相同 W (简化)
    b = [[0.0]] * 4
    i, f, o, g = lstm_gates([1.0], [0.0], W, b)
    sig_05 = 1.0 / (1.0 + math.exp(-0.5))
    tanh_05 = math.tanh(0.5)
    assert abs(i[0] - sig_05) < TOL
    assert abs(f[0] - sig_05) < TOL
    assert abs(o[0] - sig_05) < TOL
    assert abs(g[0] - tanh_05) < TOL

def test_lstm_different_gates():
    """各门用不同 W 区分"""
    W_i = [[1.0], [0.0]]; W_f = [[0.0], [0.0]]; W_o = [[2.0], [0.0]]; W_g = [[1.0], [0.0]]
    b = [[0.0]] * 4
    i, f, o, g = lstm_gates([1.0], [0.0], [W_i, W_f, W_o, W_g], b)
    # i: z=1, sigmoid(1)≈0.7311
    assert abs(i[0] - (1.0 / (1.0 + math.exp(-1.0)))) < TOL
    # f: z=0, sigmoid(0)=0.5
    assert abs(f[0] - 0.5) < TOL
    # o: z=2, sigmoid(2)≈0.881
    assert abs(o[0] - (1.0 / (1.0 + math.exp(-2.0)))) < TOL
    # g: z=1, tanh(1)≈0.762
    assert abs(g[0] - math.tanh(1.0)) < TOL

def test_lstm_with_h_prev():
    """h_prev 非零, x=0, W=[[0],[1]] → z=h_prev"""
    W = [[[0.0], [1.0]]] * 4
    b = [[0.0]] * 4
    i, f, o, g = lstm_gates([0.0], [2.0], W, b)
    sig_2 = 1.0 / (1.0 + math.exp(-2.0))
    assert abs(i[0] - sig_2) < TOL
    assert abs(g[0] - math.tanh(2.0)) < TOL

def test_lstm_with_bias():
    """全 0 输入, b=[1] → z=1"""
    W = [[[0.0], [0.0]]] * 4
    b = [[1.0]] * 4
    i, f, o, g = lstm_gates([0.0], [0.0], W, b)
    assert abs(i[0] - (1.0 / (1.0 + math.exp(-1.0)))) < TOL
    assert abs(g[0] - math.tanh(1.0)) < TOL

def test_lstm_raises_on_wrong_W_count():
    """W_list 必须 4 个"""
    with pytest.raises(ValueError):
        lstm_gates([1.0], [0.0], [[[0.5], [0.3]]] * 3, [[0.0]] * 3)

def test_lstm_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        lstm_gates([1.0, 2.0], [0.0], [[[0.5], [0.3]]] * 4, [[0.0]] * 4)

def test_lstm_raises_on_non_list():
    with pytest.raises(TypeError):
        lstm_gates("ab", [0.0], [[[0.5]]] * 4, [[0]] * 4)


# F3: gru_gates
def test_gru_basic():
    """x=[1] h=[0] W=[[0.5],[0]] b=[0] for all 3
    z = sigmoid(0.5) ≈ 0.6225
    r = sigmoid(0.5) ≈ 0.6225
    h_tilde = tanh([1; r*0] @ [[0.5],[0]] + 0) = tanh(0.5)
    """
    W_z = [[0.5], [0.0]]; W_r = [[0.5], [0.0]]; W_h = [[0.5], [0.0]]
    z, r, h_tilde = gru_gates([1.0], [0.0], [W_z, W_r, W_h], [[0.0]] * 3)
    sig_05 = 1.0 / (1.0 + math.exp(-0.5))
    assert abs(z[0] - sig_05) < TOL
    assert abs(r[0] - sig_05) < TOL
    assert abs(h_tilde[0] - math.tanh(0.5)) < TOL

def test_gru_with_hidden_no_reset():
    """x=[0] h=[1], W_z=[[0],[1]] (z 直接读 h), W_r=[[0],[0]] (r=sigmoid(0)=0.5)
    W_h=[[0],[1]] → h_tilde 输入 [0; 0.5*1] = [0, 0.5]
    h_tilde = tanh(0*0 + 0.5*1 + 0) = tanh(0.5)"""
    W_z = [[0.0], [1.0]]; W_r = [[0.0], [0.0]]; W_h = [[0.0], [1.0]]
    z, r, h_tilde = gru_gates([0.0], [1.0], [W_z, W_r, W_h], [[0.0]] * 3)
    assert abs(z[0] - (1.0 / (1.0 + math.exp(-1.0)))) < TOL
    assert abs(r[0] - 0.5) < TOL
    assert abs(h_tilde[0] - math.tanh(0.5)) < TOL

def test_gru_zero_input_and_hidden():
    """全 0, b=0 → 全 0.5/0.5/0"""
    W = [[[0.0], [0.0]]] * 3
    b = [[0.0]] * 3
    z, r, h_tilde = gru_gates([0.0], [0.0], W, b)
    assert abs(z[0] - 0.5) < TOL
    assert abs(r[0] - 0.5) < TOL
    assert abs(h_tilde[0] - 0.0) < TOL

def test_gru_with_bias():
    """全 0 输入 + b=1 各门"""
    W = [[[0.0], [0.0]]] * 3
    b = [[1.0]] * 3
    z, r, h_tilde = gru_gates([0.0], [0.0], W, b)
    sig_1 = 1.0 / (1.0 + math.exp(-1.0))
    assert abs(z[0] - sig_1) < TOL
    assert abs(r[0] - sig_1) < TOL
    assert abs(h_tilde[0] - math.tanh(1.0)) < TOL

def test_gru_raises_on_wrong_W_count():
    with pytest.raises(ValueError):
        gru_gates([1.0], [0.0], [[[0.5]]] * 2, [[0]] * 2)

def test_gru_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        gru_gates([1.0, 2.0], [0.0], [[[0.5]]] * 3, [[0]] * 3)

def test_gru_raises_on_non_list():
    with pytest.raises(TypeError):
        gru_gates("ab", [0.0], [[[0.5]]] * 3, [[0]] * 3)


# F4: compute_sequence_length_after_truncate
def test_trunc_within_max():
    assert compute_sequence_length_after_truncate(50, 100) == 50

def test_trunc_exceeds_max():
    assert compute_sequence_length_after_truncate(200, 100) == 100

def test_trunc_equal():
    assert compute_sequence_length_after_truncate(100, 100) == 100

def test_trunc_zero_seq():
    assert compute_sequence_length_after_truncate(0, 100) == 0

def test_trunc_one_seq():
    assert compute_sequence_length_after_truncate(1, 100) == 1

def test_trunc_raises_on_negative_seq():
    with pytest.raises(ValueError):
        compute_sequence_length_after_truncate(-1, 100)

def test_trunc_raises_on_zero_max():
    with pytest.raises(ValueError):
        compute_sequence_length_after_truncate(50, 0)

def test_trunc_raises_on_non_int():
    with pytest.raises(TypeError):
        compute_sequence_length_after_truncate(50.5, 100)
