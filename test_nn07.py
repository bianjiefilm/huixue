"""NN07 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn07 import (
    sgd_update,
    momentum_update,
    adam_update,
    apply_lr_decay,
)

TOL = 1e-6


# ============================================================
# F1: sgd_update
# ============================================================

def test_sgd_textbook():
    """W=[1,2,3] dW=[0.1,0.2,0.3] lr=10 → [0,0,0]"""
    r = sgd_update([1.0, 2.0, 3.0], [0.1, 0.2, 0.3], 10.0)
    for i, e in enumerate([0.0, 0.0, 0.0]):
        assert abs(r[i] - e) < TOL

def test_sgd_negative_grad():
    """W=[5] dW=[-2] lr=0.5 → [6]"""
    r = sgd_update([5.0], [-2.0], 0.5)
    assert abs(r[0] - 6.0) < TOL

def test_sgd_small_lr():
    """W=[10] dW=[1] lr=0.01 → [9.99]"""
    r = sgd_update([10.0], [1.0], 0.01)
    assert abs(r[0] - 9.99) < TOL

def test_sgd_multi_param():
    """W=[1,2,3,4] dW=[1,1,1,1] lr=0.5 → [0.5, 1.5, 2.5, 3.5]"""
    r = sgd_update([1, 2, 3, 4], [1, 1, 1, 1], 0.5)
    expected = [0.5, 1.5, 2.5, 3.5]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sgd_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        sgd_update([1, 2], [1], 0.1)

def test_sgd_raises_on_empty():
    with pytest.raises(ValueError):
        sgd_update([], [], 0.1)

def test_sgd_raises_on_non_list():
    with pytest.raises(TypeError):
        sgd_update("ab", [0.1, 0.2], 0.01)


# ============================================================
# F2: momentum_update (multi-output tuple)
# ============================================================

def test_mom_first_step():
    """v_prev=0, dW=1, mu=0.9, lr=0.1 → v=1, W_new = W - 0.1*1
    W=[10] → W_new=[9.9], v=[1]"""
    W_new, v_new = momentum_update([10.0], [1.0], [0.0], 0.1, 0.9)
    assert abs(W_new[0] - 9.9) < TOL
    assert abs(v_new[0] - 1.0) < TOL

def test_mom_second_step():
    """v_prev=[1], dW=[1], mu=0.9 → v_new = 0.9*1+1 = 1.9
    W=[10] lr=0.1 → W_new = 10 - 0.1*1.9 = 9.81"""
    W_new, v_new = momentum_update([10.0], [1.0], [1.0], 0.1, 0.9)
    assert abs(v_new[0] - 1.9) < TOL
    assert abs(W_new[0] - 9.81) < TOL

def test_mom_zero_momentum_equals_sgd():
    """mu=0 退化为 SGD: v_new = dW; W_new = W - lr*dW"""
    W_new, v_new = momentum_update([10.0], [2.0], [5.0], 0.5, 0.0)
    # v = 0*5 + 2 = 2
    # W = 10 - 0.5*2 = 9
    assert abs(v_new[0] - 2.0) < TOL
    assert abs(W_new[0] - 9.0) < TOL

def test_mom_multi_param():
    """W=[1,2], dW=[0.1,0.2], v_prev=[0,0], lr=1, mu=0.5
    v = [0.1, 0.2]; W_new = [1-0.1, 2-0.2] = [0.9, 1.8]"""
    W_new, v_new = momentum_update([1, 2], [0.1, 0.2], [0, 0], 1.0, 0.5)
    assert abs(v_new[0] - 0.1) < TOL and abs(v_new[1] - 0.2) < TOL
    assert abs(W_new[0] - 0.9) < TOL and abs(W_new[1] - 1.8) < TOL

def test_mom_negative_grad():
    """dW 负 → v 负 → W 增"""
    W_new, v_new = momentum_update([5.0], [-1.0], [0.0], 0.5, 0.0)
    # v = 0*0 + (-1) = -1; W_new = 5 - 0.5*(-1) = 5.5
    assert abs(v_new[0] - (-1.0)) < TOL
    assert abs(W_new[0] - 5.5) < TOL

def test_mom_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        momentum_update([1, 2], [0.1], [0, 0], 0.1, 0.9)

def test_mom_raises_on_empty():
    with pytest.raises(ValueError):
        momentum_update([], [], [], 0.1, 0.9)

def test_mom_raises_on_non_list():
    with pytest.raises(TypeError):
        momentum_update("ab", [0.1], [0], 0.1, 0.9)


# ============================================================
# F3: adam_update (multi-output 3-tuple)
# ============================================================

def test_adam_first_step():
    """t=1, m_prev=v_prev=0
    m = 0.1*1 = 0.1; v = 0.001*1 = 0.001
    m_hat = 0.1/(1-0.9) = 1; v_hat = 0.001/(1-0.999) = 1
    W_new = W - lr * m_hat / (sqrt(v_hat)+eps)
    取 W=[1], dW=[1], lr=0.001, b1=0.9, b2=0.999
    W_new = 1 - 0.001 * 1 / (1 + 1e-8) ≈ 0.999"""
    W_new, m_new, v_new = adam_update(
        [1.0], [1.0], [0.0], [0.0],
        lr=0.001, beta1=0.9, beta2=0.999, t=1
    )
    assert abs(m_new[0] - 0.1) < TOL
    assert abs(v_new[0] - 0.001) < TOL
    assert abs(W_new[0] - 0.999) < 1e-3

def test_adam_zero_grad():
    """dW=0 → m=0, v=0, W 不变"""
    W_new, m_new, v_new = adam_update(
        [5.0, 3.0], [0.0, 0.0], [0.5, 0.3], [0.1, 0.2],
        lr=0.001, beta1=0.9, beta2=0.999, t=10
    )
    # m = 0.9*0.5 = 0.45; v = 0.999*0.1 = 0.0999
    # 但 dW=0 时, 与上一步无关, m/v 仅含历史衰减
    assert abs(m_new[0] - 0.45) < TOL
    assert abs(m_new[1] - 0.27) < TOL

def test_adam_known_step_t10():
    """t=10, m_prev=v_prev=0, dW=1, lr=0.001
    m = 0.1 (t=1 起算实际是 1 步, 但这里假设 t 直接给 10, m_prev 给 0)
    m_hat = 0.1 / (1 - 0.9^10) = 0.1 / 0.6513 ≈ 0.1535
    v_hat = 0.001 / (1 - 0.999^10) ≈ 0.001 / 0.00996 ≈ 0.1004
    W_new = 1 - 0.001 * 0.1535 / sqrt(0.1004) ≈ 1 - 0.000485"""
    W_new, m_new, v_new = adam_update(
        [1.0], [1.0], [0.0], [0.0],
        lr=0.001, beta1=0.9, beta2=0.999, t=10
    )
    # 验证 m, v 的原始值 (未校正)
    assert abs(m_new[0] - 0.1) < TOL
    assert abs(v_new[0] - 0.001) < TOL

def test_adam_dimensions_consistent():
    """W=[1,2,3] → m, v, W_new 都是 3 元素"""
    W_new, m_new, v_new = adam_update(
        [1, 2, 3], [0.1, 0.2, 0.3], [0, 0, 0], [0, 0, 0],
        lr=0.001, beta1=0.9, beta2=0.999, t=1
    )
    assert len(W_new) == 3 and len(m_new) == 3 and len(v_new) == 3

def test_adam_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        adam_update([1, 2], [0.1], [0, 0], [0, 0],
                    lr=0.001, beta1=0.9, beta2=0.999, t=1)

def test_adam_raises_on_zero_t():
    """t 必须 >= 1 (防偏差校正除零)"""
    with pytest.raises(ValueError):
        adam_update([1], [0.1], [0], [0],
                    lr=0.001, beta1=0.9, beta2=0.999, t=0)

def test_adam_raises_on_non_list():
    with pytest.raises(TypeError):
        adam_update("ab", [0.1], [0], [0],
                    lr=0.001, beta1=0.9, beta2=0.999, t=1)


# ============================================================
# F4: apply_lr_decay
# ============================================================

def test_lrd_step():
    """step: 1.0 * 0.5^3 = 0.125"""
    assert abs(apply_lr_decay(1.0, 3, 0.5, "step") - 0.125) < TOL

def test_lrd_step_epoch_zero():
    """epoch=0 → 不衰减"""
    assert abs(apply_lr_decay(0.5, 0, 0.9, "step") - 0.5) < TOL

def test_lrd_exp():
    """exp: 1.0 * exp(-0.1*5) = exp(-0.5) ≈ 0.6065"""
    r = apply_lr_decay(1.0, 5, 0.1, "exp")
    assert abs(r - math.exp(-0.5)) < TOL

def test_lrd_inverse():
    """inverse: 1.0 / (1 + 0.1*9) = 1/1.9 ≈ 0.5263"""
    assert abs(apply_lr_decay(1.0, 9, 0.1, "inverse") - 1 / 1.9) < TOL

def test_lrd_decay_decreases():
    """epoch 增 → lr 严格减"""
    lr0 = apply_lr_decay(1.0, 0, 0.5, "step")
    lr1 = apply_lr_decay(1.0, 1, 0.5, "step")
    lr2 = apply_lr_decay(1.0, 5, 0.5, "step")
    assert lr0 > lr1 > lr2

def test_lrd_raises_on_negative_epoch():
    with pytest.raises(ValueError):
        apply_lr_decay(1.0, -1, 0.5, "step")

def test_lrd_raises_on_invalid_type():
    with pytest.raises(ValueError):
        apply_lr_decay(1.0, 5, 0.5, "unknown")

def test_lrd_raises_on_non_numeric():
    with pytest.raises(TypeError):
        apply_lr_decay("1.0", 5, 0.5, "step")
