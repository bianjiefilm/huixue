"""MJ08 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj08 import (
    center_data,
    compute_covariance,
    pca_transform,
    explained_variance_ratio,
)

TOL = 1e-6


# ============================================================
# F1: center_data (transform 类, tuple 双结构全验)
# ============================================================

def test_cd_3x2_known_mean():
    """X=[[1,2],[3,4],[5,6]] mean=[3,4] centered=[[-2,-2],[0,0],[2,2]]"""
    cx, mean = center_data([[1, 2], [3, 4], [5, 6]])
    assert mean == [3.0, 4.0] or all(abs(m - e) < TOL for m, e in zip(mean, [3.0, 4.0]))
    expected = [[-2.0, -2.0], [0.0, 0.0], [2.0, 2.0]]
    for i in range(3):
        for j in range(2):
            assert abs(cx[i][j] - expected[i][j]) < TOL

def test_cd_1d_4_samples():
    """X=[[1],[2],[3],[4]] mean=[2.5] centered=[[-1.5],[-0.5],[0.5],[1.5]]"""
    cx, mean = center_data([[1], [2], [3], [4]])
    assert abs(mean[0] - 2.5) < TOL
    expected = [[-1.5], [-0.5], [0.5], [1.5]]
    for i in range(4):
        assert abs(cx[i][0] - expected[i][0]) < TOL

def test_cd_3d():
    """X=[[1,2,3],[4,5,6]] mean=[2.5,3.5,4.5]"""
    cx, mean = center_data([[1, 2, 3], [4, 5, 6]])
    expected_mean = [2.5, 3.5, 4.5]
    for i, e in enumerate(expected_mean):
        assert abs(mean[i] - e) < TOL
    expected_cx = [[-1.5, -1.5, -1.5], [1.5, 1.5, 1.5]]
    for i in range(2):
        for j in range(3):
            assert abs(cx[i][j] - expected_cx[i][j]) < TOL

def test_cd_constant_data():
    """边界: X=[[5,5],[5,5]] mean=[5,5] centered=[[0,0],[0,0]]"""
    cx, mean = center_data([[5, 5], [5, 5]])
    assert mean == [5.0, 5.0] or all(abs(m - e) < TOL for m, e in zip(mean, [5.0, 5.0]))
    for row in cx:
        assert abs(row[0]) < TOL and abs(row[1]) < TOL

def test_cd_single_sample():
    """边界: X=[[10,20]] 单样本 → mean=[10,20], centered=[[0,0]]"""
    cx, mean = center_data([[10, 20]])
    for i, e in enumerate([10.0, 20.0]):
        assert abs(mean[i] - e) < TOL
    assert abs(cx[0][0]) < TOL and abs(cx[0][1]) < TOL

def test_cd_raises_on_empty():
    with pytest.raises(ValueError):
        center_data([])

def test_cd_raises_on_inconsistent_rows():
    with pytest.raises(ValueError):
        center_data([[1, 2], [3]])

def test_cd_raises_on_non_list():
    with pytest.raises(TypeError):
        center_data("abc")


# ============================================================
# F2: compute_covariance (用 y=2x 数据精确断言)
# ============================================================

def test_cov_y_2x():
    """中心化后 [[-2,-4],[-1,-2],[0,0],[1,2],[2,4]] → cov=[[2,4],[4,8]]"""
    centered = [[-2, -4], [-1, -2], [0, 0], [1, 2], [2, 4]]
    cov = compute_covariance(centered)
    expected = [[2.0, 4.0], [4.0, 8.0]]
    for i in range(2):
        for j in range(2):
            assert abs(cov[i][j] - expected[i][j]) < TOL

def test_cov_diagonal():
    """中心化 [[1,0],[-1,0]] → cov=[[1,0],[0,0]]"""
    cov = compute_covariance([[1, 0], [-1, 0]])
    assert abs(cov[0][0] - 1.0) < TOL
    assert abs(cov[1][1] - 0.0) < TOL
    assert abs(cov[0][1] - 0.0) < TOL

def test_cov_3d():
    """中心化 [[1,1,1],[-1,-1,-1]] → cov=[[1,1,1],[1,1,1],[1,1,1]]"""
    cov = compute_covariance([[1, 1, 1], [-1, -1, -1]])
    for i in range(3):
        for j in range(3):
            assert abs(cov[i][j] - 1.0) < TOL

def test_cov_identity_data():
    """中心化 [[1,0],[0,1],[-1,0],[0,-1]] → cov 接近 [[0.5,0],[0,0.5]]"""
    cov = compute_covariance([[1, 0], [0, 1], [-1, 0], [0, -1]])
    assert abs(cov[0][0] - 0.5) < TOL
    assert abs(cov[1][1] - 0.5) < TOL
    assert abs(cov[0][1] - 0.0) < TOL
    assert abs(cov[1][0] - 0.0) < TOL

def test_cov_anti_correlated():
    """[[1,-1],[-1,1]] → cov=[[1,-1],[-1,1]]"""
    cov = compute_covariance([[1, -1], [-1, 1]])
    assert abs(cov[0][0] - 1.0) < TOL
    assert abs(cov[0][1] - (-1.0)) < TOL
    assert abs(cov[1][0] - (-1.0)) < TOL
    assert abs(cov[1][1] - 1.0) < TOL

def test_cov_raises_on_empty():
    with pytest.raises(ValueError):
        compute_covariance([])

def test_cov_raises_on_inconsistent_rows():
    with pytest.raises(ValueError):
        compute_covariance([[1, 2], [3]])

def test_cov_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_covariance("abc")


# ============================================================
# F3: pca_transform (transform 类)
# ============================================================

def test_pt_project_to_first_axis():
    """投影到 x 轴: components=[[1,0]], X=[[1,2],[3,4]] → [[1],[3]] (k=1 严格)"""
    r = pca_transform([[1, 2], [3, 4]], [[1, 0]])
    assert len(r) == 2 and len(r[0]) == 1 and len(r[1]) == 1
    assert abs(r[0][0] - 1.0) < TOL
    assert abs(r[1][0] - 3.0) < TOL

def test_pt_project_to_y_axis():
    """投影到 y 轴: components=[[0,1]], X=[[1,2],[3,4]] → [[2],[4]] (k=1 严格)"""
    r = pca_transform([[1, 2], [3, 4]], [[0, 1]])
    assert len(r) == 2 and len(r[0]) == 1 and len(r[1]) == 1
    assert abs(r[0][0] - 2.0) < TOL
    assert abs(r[1][0] - 4.0) < TOL

def test_pt_project_diagonal():
    """对角方向: X=[[1,2]], components=[[1/sqrt(2), 1/sqrt(2)]] → [[3/sqrt(2)]]"""
    s = 1.0 / math.sqrt(2)
    r = pca_transform([[1, 2]], [[s, s]])
    assert len(r) == 1 and len(r[0]) == 1
    assert abs(r[0][0] - 3 * s) < TOL

def test_pt_two_components_3d():
    """X=[[1,2,3]], components=[[1,0,0],[0,1,0]] → [[1, 2]] (k=2 严格)"""
    r = pca_transform([[1, 2, 3]], [[1, 0, 0], [0, 1, 0]])
    assert len(r) == 1 and len(r[0]) == 2
    assert abs(r[0][0] - 1.0) < TOL
    assert abs(r[0][1] - 2.0) < TOL

def test_pt_zero_input():
    """边界: X=[[0,0]] components=[[1,0]] → [[0]] (k=1 严格)"""
    r = pca_transform([[0, 0]], [[1, 0]])
    assert len(r) == 1 and len(r[0]) == 1
    assert abs(r[0][0] - 0.0) < TOL

def test_pt_raises_on_empty_X():
    with pytest.raises(ValueError):
        pca_transform([], [[1, 0]])

def test_pt_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        pca_transform([[1, 2]], [[1, 0, 0]])

def test_pt_raises_on_non_list():
    with pytest.raises(TypeError):
        pca_transform("abc", [[1, 0]])


# ============================================================
# F4: explained_variance_ratio (transform, 多组独特 expected)
# ============================================================

def test_evr_y_2x_perfect():
    """eigvals=[10, 0] → [1.0, 0.0]"""
    r = explained_variance_ratio([10, 0])
    assert abs(r[0] - 1.0) < TOL
    assert abs(r[1] - 0.0) < TOL

def test_evr_uniform():
    """eigvals=[1,1,1,1] → [0.25]*4"""
    r = explained_variance_ratio([1, 1, 1, 1])
    for v in r:
        assert abs(v - 0.25) < TOL

def test_evr_proportional():
    """eigvals=[2, 4, 6, 8] → [0.1, 0.2, 0.3, 0.4]"""
    r = explained_variance_ratio([2, 4, 6, 8])
    expected = [0.1, 0.2, 0.3, 0.4]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_evr_typical_pca():
    """eigvals=[50, 30, 15, 5] → [0.5, 0.3, 0.15, 0.05]"""
    r = explained_variance_ratio([50, 30, 15, 5])
    expected = [0.5, 0.3, 0.15, 0.05]
    for i, e in enumerate(expected):
        assert abs(r[i] - e) < TOL

def test_evr_decimals():
    """eigvals=[0.5, 0.5] → [0.5, 0.5]"""
    r = explained_variance_ratio([0.5, 0.5])
    assert abs(r[0] - 0.5) < TOL
    assert abs(r[1] - 0.5) < TOL

def test_evr_raises_on_all_zero():
    with pytest.raises(ValueError):
        explained_variance_ratio([0, 0, 0])

def test_evr_raises_on_negative():
    with pytest.raises(ValueError):
        explained_variance_ratio([1, -1, 2])

def test_evr_raises_on_non_list():
    with pytest.raises(TypeError):
        explained_variance_ratio("abc")
