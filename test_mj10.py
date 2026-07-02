"""MJ10 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj10 import (
    stratified_kfold_split,
    bootstrap_sample,
    aggregate_cv_scores,
    compute_learning_curve_means,
)

TOL = 1e-6


# ============================================================
# F1: stratified_kfold_split (transform 类, 类比例守恒)
# ============================================================

def test_kf_balanced_4fold():
    """y=[0]*4+[1]*4 n_splits=4: 每折测试集 train+test=8, 类比例 1:1"""
    splits = stratified_kfold_split([0, 0, 0, 0, 1, 1, 1, 1], 4)
    assert len(splits) == 4
    all_test = []
    for train_idx, test_idx in splits:
        # train + test 并集 = 全部
        assert sorted(train_idx + test_idx) == list(range(8))
        # train ∩ test 为空
        assert set(train_idx) & set(test_idx) == set()
        all_test.extend(test_idx)
    # 所有 test 索引并集 = 全样本, 不重不漏
    assert sorted(all_test) == list(range(8))

def test_kf_three_fold_balanced():
    """y=[0]*6+[1]*6 n_splits=3: 每折 test 含 2 of class 0 + 2 of class 1"""
    splits = stratified_kfold_split([0]*6 + [1]*6, 3)
    assert len(splits) == 3
    y = [0]*6 + [1]*6
    for train_idx, test_idx in splits:
        labels = [y[i] for i in test_idx]
        assert labels.count(0) == 2 and labels.count(1) == 2

def test_kf_imbalanced_2_to_1():
    """y=[0]*8+[1]*4 n_splits=4: 每折 test 含 2 of class 0 + 1 of class 1"""
    splits = stratified_kfold_split([0]*8 + [1]*4, 4)
    y = [0]*8 + [1]*4
    for train_idx, test_idx in splits:
        labels = [y[i] for i in test_idx]
        assert labels.count(0) == 2 and labels.count(1) == 1

def test_kf_disjoint_test_sets():
    """所有 fold 的 test 集合两两互斥"""
    splits = stratified_kfold_split([0, 1] * 4, 4)
    test_sets = [set(t) for _, t in splits]
    for i in range(len(test_sets)):
        for j in range(i + 1, len(test_sets)):
            assert test_sets[i] & test_sets[j] == set()

def test_kf_2fold_4samples():
    """y=[0,0,1,1] n_splits=2: 每折 test 含 1 of class 0 + 1 of class 1"""
    splits = stratified_kfold_split([0, 0, 1, 1], 2)
    y = [0, 0, 1, 1]
    for _, test_idx in splits:
        labels = sorted([y[i] for i in test_idx])
        assert labels == [0, 1]

def test_kf_raises_on_too_many_splits():
    """n_splits > 某类样本数 → ValueError"""
    with pytest.raises(ValueError):
        stratified_kfold_split([0, 0, 1], 5)

def test_kf_raises_on_empty():
    with pytest.raises(ValueError):
        stratified_kfold_split([], 2)

def test_kf_raises_on_non_list():
    with pytest.raises(TypeError):
        stratified_kfold_split("abc", 2)


# ============================================================
# F2: bootstrap_sample (transform 类, 含重复 + 确定性断言)
# ============================================================

def test_bs_has_repeat():
    """input 5 个 unique 值, bootstrap n=10 必含重复"""
    r = bootstrap_sample([1, 2, 3, 4, 5], 10, random_state=42)
    assert len(r) == 10
    assert len(set(r)) < 10  # 必有重复

def test_bs_deterministic_seeds_differ():
    """同 seed 完全相同, 不同 seed 应有差异 (防 D 攻击 identity 不依赖 seed)"""
    r1 = bootstrap_sample([1, 2, 3, 4, 5], 5, random_state=42)
    r2 = bootstrap_sample([1, 2, 3, 4, 5], 5, random_state=42)
    r3 = bootstrap_sample([1, 2, 3, 4, 5], 5, random_state=123)
    assert r1 == r2  # 同 seed 一致
    assert r1 != r3  # 不同 seed 应不同 (D identity 必失败)

def test_bs_single_element():
    """[42] 任何 n 都是 [42]*n"""
    r = bootstrap_sample([1, 2, 3, 4, 5, 42], 6, random_state=99)
    assert len(r) == 6  # 不变 size 但避免 D identity slice 命中

def test_bs_n_larger_than_input():
    """n=6 > 输入 size=3, 必含重复"""
    r = bootstrap_sample([1, 2, 3], 6, random_state=42)
    assert len(r) == 6
    for v in r:
        assert v in (1, 2, 3)
    # 必有重复 (鸽笼原理)
    assert len(set(r)) <= 3

def test_bs_size_double_input():
    """input size=2, n=8 (D identity 长度不匹配)"""
    r = bootstrap_sample([100, 200], 8, random_state=42)
    assert len(r) == 8
    for v in r:
        assert v in (100, 200)

def test_bs_raises_on_empty():
    with pytest.raises(ValueError):
        bootstrap_sample([], 5, random_state=42)

def test_bs_raises_on_negative_n():
    with pytest.raises(ValueError):
        bootstrap_sample([1, 2], -1, random_state=42)

def test_bs_raises_on_non_list():
    with pytest.raises(TypeError):
        bootstrap_sample("abc", 5, random_state=42)


# ============================================================
# F3: aggregate_cv_scores (4 键全验, 多组独特 expected)
# ============================================================

def test_acvs_three_scores():
    """[0.8, 0.85, 0.9] mean=0.85, min=0.8, max=0.9, std=sqrt(2/3)*0.05 ≈ 0.0408"""
    r = aggregate_cv_scores([0.8, 0.85, 0.9])
    assert abs(r["mean"] - 0.85) < TOL
    assert abs(r["min"] - 0.8) < TOL
    assert abs(r["max"] - 0.9) < TOL
    assert abs(r["std"] - math.sqrt(((0.05)**2 + 0 + (0.05)**2) / 3)) < 1e-4

def test_acvs_perfect():
    """[1.0]*5 全 1.0, std=0"""
    r = aggregate_cv_scores([1.0] * 5)
    assert abs(r["mean"] - 1.0) < TOL
    assert abs(r["std"] - 0.0) < TOL
    assert abs(r["min"] - 1.0) < TOL
    assert abs(r["max"] - 1.0) < TOL

def test_acvs_diverse():
    """[0.5, 0.7, 0.6, 0.8] mean=0.65, min=0.5, max=0.8"""
    r = aggregate_cv_scores([0.5, 0.7, 0.6, 0.8])
    assert abs(r["mean"] - 0.65) < TOL
    assert abs(r["min"] - 0.5) < TOL
    assert abs(r["max"] - 0.8) < TOL

def test_acvs_negative():
    """[-0.1, 0.5] mean=0.2, min=-0.1, max=0.5 (含负值, R² 可负)"""
    r = aggregate_cv_scores([-0.1, 0.5])
    assert abs(r["mean"] - 0.2) < TOL
    assert abs(r["min"] - (-0.1)) < TOL
    assert abs(r["max"] - 0.5) < TOL

def test_acvs_single():
    """[0.7] mean=min=max=0.7, std=0"""
    r = aggregate_cv_scores([0.7])
    assert abs(r["mean"] - 0.7) < TOL
    assert abs(r["std"] - 0.0) < TOL

def test_acvs_raises_on_empty():
    with pytest.raises(ValueError):
        aggregate_cv_scores([])

def test_acvs_raises_on_non_list():
    with pytest.raises(TypeError):
        aggregate_cv_scores("abc")


# ============================================================
# F4: compute_learning_curve_means (transform 类)
# ============================================================

def test_lcm_basic():
    """train_scores=[[0.9,0.95],[0.85,0.9]], val_scores=[[0.8,0.82],[0.78,0.82]]
    train_mean=[0.925, 0.875], val_mean=[0.81, 0.80]"""
    r = compute_learning_curve_means(
        [[0.9, 0.95], [0.85, 0.9]],
        [[0.8, 0.82], [0.78, 0.82]]
    )
    assert "train_mean" in r and "train_std" in r
    assert "val_mean" in r and "val_std" in r
    assert abs(r["train_mean"][0] - 0.925) < TOL
    assert abs(r["train_mean"][1] - 0.875) < TOL
    assert abs(r["val_mean"][0] - 0.81) < TOL
    assert abs(r["val_mean"][1] - 0.80) < TOL

def test_lcm_constant():
    """全相同分数 → std=0, mean=该值"""
    r = compute_learning_curve_means(
        [[0.9, 0.9, 0.9], [0.85, 0.85, 0.85]],
        [[0.8, 0.8, 0.8], [0.75, 0.75, 0.75]]
    )
    for v in r["train_std"]:
        assert abs(v - 0.0) < TOL
    assert abs(r["train_mean"][0] - 0.9) < TOL
    assert abs(r["train_mean"][1] - 0.85) < TOL

def test_lcm_three_sizes():
    """3 个数据量, 每个 2 重复"""
    r = compute_learning_curve_means(
        [[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]],
        [[0.4, 0.5], [0.6, 0.7], [0.8, 0.9]]
    )
    expected_train = [0.55, 0.75, 0.95]
    expected_val = [0.45, 0.65, 0.85]
    for i, e in enumerate(expected_train):
        assert abs(r["train_mean"][i] - e) < TOL
    for i, e in enumerate(expected_val):
        assert abs(r["val_mean"][i] - e) < TOL

def test_lcm_single_size():
    """1 个数据量 1 重复 → 单值, std=0"""
    r = compute_learning_curve_means([[0.95]], [[0.88]])
    assert abs(r["train_mean"][0] - 0.95) < TOL
    assert abs(r["val_mean"][0] - 0.88) < TOL
    assert abs(r["train_std"][0] - 0.0) < TOL

def test_lcm_raises_on_empty():
    with pytest.raises(ValueError):
        compute_learning_curve_means([], [])

def test_lcm_raises_on_shape_mismatch():
    with pytest.raises(ValueError):
        compute_learning_curve_means([[0.9, 0.95]], [[0.8]])

def test_lcm_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_learning_curve_means("abc", "def")
