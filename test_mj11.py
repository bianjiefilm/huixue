"""MJ11 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj11 import (
    bagging_predict,
    weighted_vote,
    stacking_predict,
    boosting_combine,
)

TOL = 1e-6


# ============================================================
# F1: bagging_predict (transform 类, 列方向多数表决)
# ============================================================

def test_bp_user_example():
    """base_preds=[[0,1,1],[1,1,0],[1,1,1]] → 列多数 [1,1,1]"""
    assert bagging_predict([[0, 1, 1], [1, 1, 0], [1, 1, 1]]) == [1, 1, 1]

def test_bp_first_estimator_minority():
    """base_preds=[[1,1],[0,0],[0,0]] 第一估计器全错, 多数投 0 → [0,0] (b[0] 与结果不一致防 D 巧合)"""
    assert bagging_predict([[1, 1], [0, 0], [0, 0]]) == [0, 0]

def test_bp_unanimous_mixed():
    """base_preds=[[0],[1],[1]] (2/3 投 1) → [1] (b[0]=[0] 与 majority 不一致)"""
    assert bagging_predict([[0], [1], [1]]) == [1]

def test_bp_tie_smaller():
    """base_preds=[[0,1],[1,0]] 列 0: 0+1 平票 → 0; 列 1: 1+0 平票 → 0"""
    assert bagging_predict([[0, 1], [1, 0]]) == [0, 0]

def test_bp_three_estimators_three_samples():
    """base_preds=[[1,0,0],[0,1,1],[1,1,0]] 列 0: 1+0+1=2 → 1; 列 1: 0+1+1=2 → 1; 列 2: 0+1+0=1 → 0
    预期 [1,1,0]"""
    assert bagging_predict([[1, 0, 0], [0, 1, 1], [1, 1, 0]]) == [1, 1, 0]

def test_bp_raises_on_empty():
    with pytest.raises(ValueError):
        bagging_predict([])

def test_bp_raises_on_inconsistent_rows():
    with pytest.raises(ValueError):
        bagging_predict([[0, 1], [1]])

def test_bp_raises_on_non_list():
    with pytest.raises(TypeError):
        bagging_predict("abc")


# ============================================================
# F2: weighted_vote (transform 类)
# ============================================================

def test_wv_user_example():
    """base_preds=[[0,1,1],[1,1,0]] weights=[0.3,0.7] (调整以避 b[0]=expected D 巧合)
    s0: 0*0.3+1*0.7=0.7 >= 0.5 → 1
    s1: 1*0.3+1*0.7=1.0 >= 0.5 → 1
    s2: 1*0.3+0*0.7=0.3 < 0.5 → 0
    expected [1, 1, 0] 与 b[0]=[0,1,1] 不一致"""
    assert weighted_vote([[0, 1, 1], [1, 1, 0]], [0.3, 0.7]) == [1, 1, 0]

def test_wv_dominant_first():
    """weights=[1.0, 0.0] base_preds=[[1,0],[0,1]] → 完全由第一个估计器决定 → [1,0]"""
    assert weighted_vote([[1, 0], [0, 1]], [1.0, 0.0]) == [1, 0]

def test_wv_dominant_second():
    """weights=[0.0, 1.0] base_preds=[[1,0],[0,1]] → [0,1]"""
    assert weighted_vote([[1, 0], [0, 1]], [0.0, 1.0]) == [0, 1]

def test_wv_balanced_50_50():
    """weights=[0.5,0.5] base_preds=[[0,1],[1,0]] → 都等于 0.5, 阈值 >=0.5 → [1,1]"""
    assert weighted_vote([[0, 1], [1, 0]], [0.5, 0.5]) == [1, 1]

def test_wv_three_estimators():
    """weights=[0.5, 0.3, 0.2] base_preds=[[1,0,0],[1,1,0],[0,1,1]]
    s0: 1*0.5+1*0.3+0*0.2=0.8 → 1
    s1: 0*0.5+1*0.3+1*0.2=0.5 → 1 (>=0.5)
    s2: 0*0.5+0*0.3+1*0.2=0.2 → 0
    expected [1,1,0]"""
    assert weighted_vote([[1, 0, 0], [1, 1, 0], [0, 1, 1]], [0.5, 0.3, 0.2]) == [1, 1, 0]

def test_wv_raises_on_empty():
    with pytest.raises(ValueError):
        weighted_vote([], [])

def test_wv_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        weighted_vote([[1, 0]], [0.5, 0.5])  # weights 长 ≠ estimators 数

def test_wv_raises_on_non_list():
    with pytest.raises(TypeError):
        weighted_vote("abc", [0.5, 0.5])


# ============================================================
# F3: stacking_predict (transform 类)
# ============================================================

def test_sp_basic():
    """base_probs=[[0.8,0.2],[0.3,0.7]] meta_weights=[0.6,0.4]
    s0: 0.8*0.6+0.2*0.4 = 0.48+0.08 = 0.56
    s1: 0.3*0.6+0.7*0.4 = 0.18+0.28 = 0.46"""
    r = stacking_predict([[0.8, 0.2], [0.3, 0.7]], [0.6, 0.4])
    assert len(r) == 2
    assert abs(r[0] - 0.56) < TOL
    assert abs(r[1] - 0.46) < TOL

def test_sp_single_estimator():
    """meta_weights=[1.0] → 回显 base_probs[:, 0]"""
    r = stacking_predict([[0.7], [0.3], [0.5]], [1.0])
    expected = [0.7, 0.3, 0.5]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_sp_zero_weights():
    """meta_weights=[0,0] → 全 0 输出"""
    r = stacking_predict([[0.5, 0.5], [0.9, 0.1]], [0.0, 0.0])
    for v in r:
        assert abs(v - 0.0) < TOL

def test_sp_three_estimators():
    """3 estimators, 2 samples"""
    r = stacking_predict([[0.5, 0.6, 0.7], [0.2, 0.3, 0.4]], [0.2, 0.3, 0.5])
    # s0: 0.5*0.2+0.6*0.3+0.7*0.5 = 0.1+0.18+0.35 = 0.63
    # s1: 0.2*0.2+0.3*0.3+0.4*0.5 = 0.04+0.09+0.2 = 0.33
    assert abs(r[0] - 0.63) < TOL
    assert abs(r[1] - 0.33) < TOL

def test_sp_negative_weights():
    """meta_weights 含负值 (元学习器学到反向贡献)"""
    r = stacking_predict([[0.8, 0.2]], [1.0, -0.5])
    # s0: 0.8*1 + 0.2*(-0.5) = 0.8 - 0.1 = 0.7
    assert abs(r[0] - 0.7) < TOL

def test_sp_raises_on_empty():
    with pytest.raises(ValueError):
        stacking_predict([], [])

def test_sp_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        stacking_predict([[0.5, 0.5]], [0.3])

def test_sp_raises_on_non_list():
    with pytest.raises(TypeError):
        stacking_predict("abc", [0.5, 0.5])


# ============================================================
# F4: boosting_combine (transform 类)
# ============================================================

def test_bc_lr_one():
    """stage_preds=[[0.5,0.7],[0.3,0.4]] lr=1.0 → [0.8, 1.1]"""
    r = boosting_combine([[0.5, 0.7], [0.3, 0.4]], 1.0)
    assert abs(r[0] - 0.8) < TOL
    assert abs(r[1] - 1.1) < TOL

def test_bc_lr_half():
    """stage_preds=[[0.5,0.7],[0.3,0.4]] lr=0.5 → [0.4, 0.55]"""
    r = boosting_combine([[0.5, 0.7], [0.3, 0.4]], 0.5)
    assert abs(r[0] - 0.4) < TOL
    assert abs(r[1] - 0.55) < TOL

def test_bc_three_stages():
    """stage_preds=[[0.1],[0.2],[0.3]] lr=0.5 → [0.5*(0.1+0.2+0.3)]=[0.3]"""
    r = boosting_combine([[0.1], [0.2], [0.3]], 0.5)
    assert abs(r[0] - 0.3) < TOL

def test_bc_single_stage():
    """stage_preds=[[1.0, 2.0]] lr=1.0 → [1.0, 2.0]"""
    r = boosting_combine([[1.0, 2.0]], 1.0)
    assert abs(r[0] - 1.0) < TOL
    assert abs(r[1] - 2.0) < TOL

def test_bc_lr_zero():
    """lr=0 → 全 0"""
    r = boosting_combine([[1.0, 2.0], [3.0, 4.0]], 0.0)
    for v in r:
        assert abs(v - 0.0) < TOL

def test_bc_raises_on_empty():
    with pytest.raises(ValueError):
        boosting_combine([], 0.5)

def test_bc_raises_on_inconsistent_rows():
    with pytest.raises(ValueError):
        boosting_combine([[1.0, 2.0], [3.0]], 0.5)

def test_bc_raises_on_non_list():
    with pytest.raises(TypeError):
        boosting_combine("abc", 0.5)
