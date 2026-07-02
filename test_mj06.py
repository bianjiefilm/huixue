"""MJ06 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj06 import (
    compute_mse,
    compute_r2,
    linear_predict,
    normal_equation,
)

TOL = 1e-6


# ============================================================
# F1: compute_mse  (8 测试, 多组独特 expected)
# ============================================================

def test_mse_textbook():
    """[3,-0.5,2,7], [2.5,0,2,8] → 0.375"""
    assert abs(compute_mse([3, -0.5, 2, 7], [2.5, 0.0, 2, 8]) - 0.375) < TOL

def test_mse_perfect():
    """完美预测 → 0.0"""
    assert abs(compute_mse([1, 2, 3], [1, 2, 3]) - 0.0) < TOL

def test_mse_large():
    """[10,20], [0,0] → (100+400)/2 = 250"""
    assert abs(compute_mse([10, 20], [0, 0]) - 250.0) < TOL

def test_mse_doubled():
    """[1,2,3], [2,4,6] → (1+4+9)/3 = 14/3"""
    assert abs(compute_mse([1, 2, 3], [2, 4, 6]) - 14 / 3) < TOL

def test_mse_half_off():
    """[5,5,5,5], [4,5,5,4] → (1+0+0+1)/4 = 0.5"""
    assert abs(compute_mse([5, 5, 5, 5], [4, 5, 5, 4]) - 0.5) < TOL

def test_mse_raises_on_empty():
    with pytest.raises(ValueError):
        compute_mse([], [])

def test_mse_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        compute_mse([1, 2, 3], [1, 2])

def test_mse_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_mse("abc", "def")


# ============================================================
# F2: compute_r2  (8 测试, 含 R²<0 / R²=1 / R²=0.968 等独特值)
# ============================================================

def test_r2_perfect():
    """完美 → 1.0"""
    assert abs(compute_r2([1, 2, 3], [1, 2, 3]) - 1.0) < TOL

def test_r2_096():
    """y=[10,20,30,40], y_pred=[12,18,32,38] → SS_res=16, SS_tot=500, R²=0.968"""
    assert abs(compute_r2([10, 20, 30, 40], [12, 18, 32, 38]) - 0.968) < TOL

def test_r2_negative():
    """y=[1,2,3], y_pred=[3,3,3] → SS_res=5, SS_tot=2, R²=-1.5 (负, v1 漏)"""
    assert abs(compute_r2([1, 2, 3], [3, 3, 3]) - (-1.5)) < TOL

def test_r2_080():
    """y=[2,4,6,8], y_pred=[3,5,7,9] (恒偏 1) → SS_res=4, SS_tot=20, R²=0.8"""
    assert abs(compute_r2([2, 4, 6, 8], [3, 5, 7, 9]) - 0.8) < TOL

def test_r2_098():
    """y=[1,2,3,4,5], y_pred=[1.1,2.1,2.9,4.2,4.8] → R²=0.989"""
    assert abs(compute_r2([1, 2, 3, 4, 5], [1.1, 2.1, 2.9, 4.2, 4.8]) - 0.989) < TOL

def test_r2_raises_on_zero_variance():
    """y_true 全相同 → SS_tot=0, ValueError"""
    with pytest.raises(ValueError):
        compute_r2([5, 5, 5], [5, 5, 5])

def test_r2_raises_on_empty():
    with pytest.raises(ValueError):
        compute_r2([], [])

def test_r2_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_r2("abc", "def")


# ============================================================
# F3: linear_predict (transform 类)
# ============================================================

def test_lp_textbook():
    """X=[[1,2],[3,4]], w=[0.5,-0.3], b=0.1 → [0.0, 0.4]"""
    r = linear_predict([[1, 2], [3, 4]], [0.5, -0.3], 0.1)
    assert len(r) == 2
    assert abs(r[0] - 0.0) < TOL
    assert abs(r[1] - 0.4) < TOL

def test_lp_simple_doubling():
    """X=[[1],[2],[3]], w=[2.0], b=0 → [2,4,6]"""
    r = linear_predict([[1], [2], [3]], [2.0], 0.0)
    expected = [2.0, 4.0, 6.0]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_lp_three_features():
    """X=[[1,1,1]], w=[1,1,1], b=0 → [3]"""
    r = linear_predict([[1, 1, 1]], [1.0, 1.0, 1.0], 0.0)
    assert len(r) == 1
    assert abs(r[0] - 3.0) < TOL

def test_lp_only_bias():
    """X=[[0,0],[0,0]], w=[1,2], b=5 → [5,5]"""
    r = linear_predict([[0, 0], [0, 0]], [1.0, 2.0], 5.0)
    for v in r:
        assert abs(v - 5.0) < TOL

def test_lp_negative_weights():
    """X=[[10]], w=[-2], b=3 → [-17]"""
    r = linear_predict([[10]], [-2.0], 3.0)
    assert len(r) == 1
    assert abs(r[0] - (-17.0)) < TOL

def test_lp_raises_on_empty():
    with pytest.raises(ValueError):
        linear_predict([], [1.0], 0.0)

def test_lp_raises_on_dim_mismatch():
    """X 行宽与 weights 长度不一致"""
    with pytest.raises(ValueError):
        linear_predict([[1, 2]], [1.0], 0.0)

def test_lp_raises_on_non_list():
    with pytest.raises(TypeError):
        linear_predict("abc", [1.0], 0.0)


# ============================================================
# F4: normal_equation (transform 类, 用 y=x 等已知答案精确断言)
# ============================================================

def test_ne_y_equals_x():
    """X=[[1,1],[1,2],[1,3],[1,4]] y=[1,2,3,4] (intercept+slope) → w=[0,1]"""
    r = normal_equation([[1, 1], [1, 2], [1, 3], [1, 4]], [1, 2, 3, 4])
    assert len(r) == 2
    assert abs(r[0] - 0.0) < 1e-4
    assert abs(r[1] - 1.0) < 1e-4

def test_ne_y_2plus_x():
    """X=[[1,0],[1,1],[1,2]] y=[2,3,4] → w=[2,1]"""
    r = normal_equation([[1, 0], [1, 1], [1, 2]], [2, 3, 4])
    assert len(r) == 2
    assert abs(r[0] - 2.0) < 1e-4
    assert abs(r[1] - 1.0) < 1e-4

def test_ne_y_1plus_2x():
    """X=[[1,1],[1,2],[1,3]] y=[3,5,7] → w=[1,2]"""
    r = normal_equation([[1, 1], [1, 2], [1, 3]], [3, 5, 7])
    assert len(r) == 2
    assert abs(r[0] - 1.0) < 1e-4
    assert abs(r[1] - 2.0) < 1e-4

def test_ne_two_features():
    """X=[[1,1,2],[1,2,4],[1,3,6],[1,4,8]] y = 1 + 0*x1 + 0.5*x2 → w=[1,0,0.5]
    第 3 特征是第 2 特征的 2 倍 (共线), 但因为我们设计 y 也对应正确解就能解出唯一权重 — 实际上 X^T X 是奇异的, 这种共线场景在数值上会失败.
    改用独立两特征: x1=[1,2,3,4] x2=[2,1,4,3] (不共线), y = 1 + 1*x1 - 0.5*x2."""
    r = normal_equation(
        [[1, 1, 2], [1, 2, 1], [1, 3, 4], [1, 4, 3]],
        [1 + 1 - 0.5 * 2, 1 + 2 - 0.5 * 1, 1 + 3 - 0.5 * 4, 1 + 4 - 0.5 * 3]
    )
    assert len(r) == 3
    assert abs(r[0] - 1.0) < 1e-4
    assert abs(r[1] - 1.0) < 1e-4
    assert abs(r[2] - (-0.5)) < 1e-4

def test_ne_single_sample():
    """X=[[1]] y=[5] → w=[5] (1 sample 1 feature 唯一解)"""
    r = normal_equation([[1]], [5])
    assert len(r) == 1
    assert abs(r[0] - 5.0) < 1e-4

def test_ne_raises_on_singular():
    """X 重复行 → X^T X 奇异 → ValueError"""
    with pytest.raises(ValueError):
        normal_equation([[1, 1], [1, 1]], [1, 2])

def test_ne_raises_on_empty():
    with pytest.raises(ValueError):
        normal_equation([], [])

def test_ne_raises_on_non_list():
    with pytest.raises(TypeError):
        normal_equation("abc", "def")
