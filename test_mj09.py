"""MJ09 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj09 import (
    compute_support,
    compute_confidence,
    compute_lift,
    find_frequent_itemsets,
)

TOL = 1e-6

# 标准 4 事务: T1={A,B} T2={A,C} T3={B,C} T4={A,B,C}
TRANS_4 = [{"A", "B"}, {"A", "C"}, {"B", "C"}, {"A", "B", "C"}]


# ============================================================
# F1: compute_support  (8 测试, 多组独特 expected)
# ============================================================

def test_sup_a_three_quarters():
    """{A} 在 3/4 事务中 → 0.75"""
    assert abs(compute_support(TRANS_4, {"A"}) - 0.75) < TOL

def test_sup_ab_half():
    """{A,B} 在 2/4 事务中 → 0.5"""
    assert abs(compute_support(TRANS_4, {"A", "B"}) - 0.5) < TOL

def test_sup_abc_quarter():
    """{A,B,C} 在 1/4 → 0.25"""
    assert abs(compute_support(TRANS_4, {"A", "B", "C"}) - 0.25) < TOL

def test_sup_zero():
    """{Z} 不在任何事务 → 0.0"""
    assert abs(compute_support(TRANS_4, {"Z"}) - 0.0) < TOL

def test_sup_full():
    """5 笔事务 [A] × 5 中 {A} 支持度 1.0"""
    assert abs(compute_support([{"A"}, {"A"}, {"A"}, {"A"}, {"A"}], {"A"}) - 1.0) < TOL

def test_sup_two_fifths():
    """5 笔事务 {B} 在 2 笔 → 0.4"""
    trans = [{"A"}, {"A", "B"}, {"A"}, {"B"}, {"A"}]
    assert abs(compute_support(trans, {"B"}) - 0.4) < TOL

def test_sup_raises_on_empty_trans():
    with pytest.raises(ValueError):
        compute_support([], {"A"})

def test_sup_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_support("abc", {"A"})


# ============================================================
# F2: compute_confidence  (7 测试)
# ============================================================

def test_conf_a_to_b():
    """conf({A}→{B}) = sup(A∪B)/sup(A) = 0.5/0.75 = 2/3"""
    assert abs(compute_confidence(TRANS_4, {"A"}, {"B"}) - 2 / 3) < TOL

def test_conf_b_to_a():
    """conf({B}→{A}) = 0.5/0.75 = 2/3"""
    assert abs(compute_confidence(TRANS_4, {"B"}, {"A"}) - 2 / 3) < TOL

def test_conf_a_to_z():
    """A 出现 3 次, A∩Z 出现 0 次 → 0.0"""
    assert abs(compute_confidence(TRANS_4, {"A"}, {"Z"}) - 0.0) < TOL

def test_conf_full_implication():
    """trans=[{A,B},{A,B}] conf({A}→{B}) = 1.0"""
    assert abs(compute_confidence([{"A", "B"}, {"A", "B"}], {"A"}, {"B"}) - 1.0) < TOL

def test_conf_partial():
    """trans=[{A,B},{A},{A,B},{A}] conf({A}→{B}) = sup(AB)/sup(A) = 0.5/1.0 = 0.5"""
    trans = [{"A", "B"}, {"A"}, {"A", "B"}, {"A"}]
    assert abs(compute_confidence(trans, {"A"}, {"B"}) - 0.5) < TOL

def test_conf_raises_on_zero_antecedent():
    """antecedent 支持度 0 → ValueError"""
    with pytest.raises(ValueError):
        compute_confidence(TRANS_4, {"Z"}, {"A"})

def test_conf_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_confidence("abc", {"A"}, {"B"})


# ============================================================
# F3: compute_lift  (7 测试)
# ============================================================

def test_lift_independent():
    """trans=[{A,B},{A},{B},{}] sup(A)=0.5 sup(B)=0.5 sup(AB)=0.25 → lift=1.0"""
    trans = [{"A", "B"}, {"A"}, {"B"}, set()]
    assert abs(compute_lift(trans, {"A"}, {"B"}) - 1.0) < TOL

def test_lift_positive():
    """完全相关: trans=[{A,B},{A,B},{C}] sup(A)=2/3 sup(B)=2/3 sup(AB)=2/3 → lift=1.5"""
    trans = [{"A", "B"}, {"A", "B"}, {"C"}]
    assert abs(compute_lift(trans, {"A"}, {"B"}) - 1.5) < TOL

def test_lift_classic_4trans():
    """4 trans: lift({A}→{B}) = sup(AB)/(sup(A)*sup(B)) = 0.5/(0.75*0.75) = 8/9"""
    assert abs(compute_lift(TRANS_4, {"A"}, {"B"}) - 8 / 9) < TOL

def test_lift_negative():
    """{A,B} 完全互斥: trans=[{A},{A},{B},{B}] sup(A)=0.5 sup(B)=0.5 sup(AB)=0 → lift=0"""
    trans = [{"A"}, {"A"}, {"B"}, {"B"}]
    assert abs(compute_lift(trans, {"A"}, {"B"}) - 0.0) < TOL

def test_lift_double_classical():
    """trans=[{A,B},{A,B},{A,C},{A,C}] sup(A)=1, sup(B)=0.5, sup(AB)=0.5 → lift=1.0"""
    trans = [{"A", "B"}, {"A", "B"}, {"A", "C"}, {"A", "C"}]
    assert abs(compute_lift(trans, {"A"}, {"B"}) - 1.0) < TOL

def test_lift_raises_on_zero_consequent():
    with pytest.raises(ValueError):
        compute_lift(TRANS_4, {"A"}, {"Z"})

def test_lift_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_lift("abc", {"A"}, {"B"})


# ============================================================
# F4: find_frequent_itemsets (transform 类, 全集合精确断言)
# ============================================================

def test_ffi_classic_4trans_half():
    """min_support=0.5: 应有 6 个频繁项集 (3 单项 + 3 双项)"""
    result = find_frequent_itemsets(TRANS_4, 0.5)
    expected = {
        frozenset({"A"}), frozenset({"B"}), frozenset({"C"}),
        frozenset({"A", "B"}), frozenset({"A", "C"}), frozenset({"B", "C"}),
    }
    assert set(result) == expected

def test_ffi_classic_4trans_three_quarter():
    """min_support=0.75: 仅 3 个单项"""
    result = find_frequent_itemsets(TRANS_4, 0.75)
    expected = {frozenset({"A"}), frozenset({"B"}), frozenset({"C"})}
    assert set(result) == expected

def test_ffi_classic_4trans_one():
    """min_support=1.0: 必须出现在所有事务 → 空"""
    result = find_frequent_itemsets(TRANS_4, 1.0)
    assert result == [] or set(result) == set()

def test_ffi_3trans_high_support():
    """trans=[{A,B},{A,B},{A,B}] min_support=1.0 → {A},{B},{A,B}"""
    trans = [{"A", "B"}, {"A", "B"}, {"A", "B"}]
    result = find_frequent_itemsets(trans, 1.0)
    expected = {frozenset({"A"}), frozenset({"B"}), frozenset({"A", "B"})}
    assert set(result) == expected

def test_ffi_specific_pair():
    """trans=[{A,B},{A,C},{B,C},{A,B,C}] min_support=0.4 → 应含 {A,B}"""
    result = find_frequent_itemsets(TRANS_4, 0.4)
    assert frozenset({"A", "B"}) in result
    assert frozenset({"A", "B", "C"}) not in result  # 0.25 < 0.4

def test_ffi_raises_on_empty_trans():
    with pytest.raises(ValueError):
        find_frequent_itemsets([], 0.5)

def test_ffi_raises_on_invalid_threshold():
    with pytest.raises(ValueError):
        find_frequent_itemsets(TRANS_4, 1.5)

def test_ffi_raises_on_non_list():
    with pytest.raises(TypeError):
        find_frequent_itemsets("abc", 0.5)
