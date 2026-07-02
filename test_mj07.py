"""MJ07 evaluator (v2) — 4 attack-resistant + 5 red-line compliant."""
import sys
import math
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj07 import (
    euclidean_distance,
    assign_clusters,
    update_centroids,
    compute_inertia,
)

TOL = 1e-6


# ============================================================
# F1: euclidean_distance (8 测试, 多组独特 expected)
# ============================================================

def test_ed_three_four_five():
    """[0,0], [3,4] → 5.0"""
    assert abs(euclidean_distance([0, 0], [3, 4]) - 5.0) < TOL

def test_ed_one_d():
    """[0], [7] → 7.0"""
    assert abs(euclidean_distance([0], [7]) - 7.0) < TOL

def test_ed_zero():
    """同点 → 0.0"""
    assert abs(euclidean_distance([1, 1, 1], [1, 1, 1]) - 0.0) < TOL

def test_ed_three_d():
    """[1,2,3], [4,6,8] → sqrt(9+16+25) = sqrt(50)"""
    assert abs(euclidean_distance([1, 2, 3], [4, 6, 8]) - math.sqrt(50)) < TOL

def test_ed_negative():
    """[-1,-1], [1,1] → sqrt(8)"""
    assert abs(euclidean_distance([-1, -1], [1, 1]) - math.sqrt(8)) < TOL

def test_ed_raises_on_empty():
    with pytest.raises(ValueError):
        euclidean_distance([], [])

def test_ed_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        euclidean_distance([1, 2], [1, 2, 3])

def test_ed_raises_on_non_list():
    with pytest.raises(TypeError):
        euclidean_distance("ab", "cd")


# ============================================================
# F2: assign_clusters (transform 类, 两明显簇精确断言 labels)
# ============================================================

def test_ac_two_clear_clusters():
    """两明显分离簇 [0,0],[1,1] vs [10,10],[11,11], centroids=[[0,0],[10,10]] → [0,0,1,1]"""
    r = assign_clusters([[0, 0], [1, 1], [10, 10], [11, 11]], [[0, 0], [10, 10]])
    assert r == [0, 0, 1, 1]

def test_ac_three_clusters_permuted():
    """centroids 顺序与样本最近顺序错开, expected [1,0,2] 而非 [0,1,2]
    (防 D 攻击 list(range(n)) 巧合)"""
    r = assign_clusters([[50, 0], [0, 0], [0, 50]],
                        [[0, 0], [50, 0], [0, 50]])
    assert r == [1, 0, 2]

def test_ac_mixed_assignment():
    """[3,3], [4,4] 分别更靠近 [0,0] 与 [10,10]"""
    r = assign_clusters([[3, 3], [4, 4]], [[0, 0], [10, 10]])
    assert r == [0, 0]  # 都更近 [0,0]
    r2 = assign_clusters([[6, 6], [7, 7]], [[0, 0], [10, 10]])
    assert r2 == [1, 1]  # 都更近 [10,10]

def test_ac_tie_smaller_index():
    """两样本同距两 centroid, 平票取小索引 → [0,0] (而非 D 的 [0,1])"""
    r = assign_clusters([[5, 5], [5, 5]], [[0, 0], [10, 10]])
    assert r == [0, 0]

def test_ac_single_centroid():
    """k=1, 全分配到簇 0 → [0,0,0]"""
    r = assign_clusters([[1, 2], [3, 4], [5, 6]], [[0, 0]])
    assert r == [0, 0, 0]

def test_ac_raises_on_empty_X():
    with pytest.raises(ValueError):
        assign_clusters([], [[0, 0]])

def test_ac_raises_on_empty_centroids():
    with pytest.raises(ValueError):
        assign_clusters([[1, 2]], [])

def test_ac_raises_on_non_list():
    with pytest.raises(TypeError):
        assign_clusters("abc", [[0, 0]])


# ============================================================
# F3: update_centroids (transform 类)
# ============================================================

def test_uc_two_clusters():
    """X=[[0,0],[2,0],[10,10],[12,10]] labels=[0,0,1,1] k=2 → [[1,0],[11,10]]"""
    r = update_centroids([[0, 0], [2, 0], [10, 10], [12, 10]], [0, 0, 1, 1], 2)
    assert len(r) == 2
    assert abs(r[0][0] - 1.0) < TOL and abs(r[0][1] - 0.0) < TOL
    assert abs(r[1][0] - 11.0) < TOL and abs(r[1][1] - 10.0) < TOL

def test_uc_three_clusters():
    """X=[[1],[2],[5],[6],[100]] labels=[0,0,1,1,2] k=3 → [[1.5],[5.5],[100]]"""
    r = update_centroids([[1], [2], [5], [6], [100]], [0, 0, 1, 1, 2], 3)
    assert len(r) == 3
    assert abs(r[0][0] - 1.5) < TOL
    assert abs(r[1][0] - 5.5) < TOL
    assert abs(r[2][0] - 100.0) < TOL

def test_uc_single_cluster():
    """全在簇 0 → 中心是均值"""
    r = update_centroids([[1, 1], [3, 3], [5, 5]], [0, 0, 0], 1)
    assert len(r) == 1
    assert abs(r[0][0] - 3.0) < TOL
    assert abs(r[0][1] - 3.0) < TOL

def test_uc_empty_cluster_zeros():
    """labels 都是 0, k=2 → 簇 1 空, 用 0 占位"""
    r = update_centroids([[2, 2], [4, 4]], [0, 0], 2)
    assert len(r) == 2
    assert abs(r[0][0] - 3.0) < TOL and abs(r[0][1] - 3.0) < TOL
    assert abs(r[1][0] - 0.0) < TOL and abs(r[1][1] - 0.0) < TOL

def test_uc_negative_values():
    """X=[[-1,-2],[1,2]] labels=[0,0] k=1 → [[0,0]]"""
    r = update_centroids([[-1, -2], [1, 2]], [0, 0], 1)
    assert abs(r[0][0] - 0.0) < TOL and abs(r[0][1] - 0.0) < TOL

def test_uc_raises_on_empty_X():
    with pytest.raises(ValueError):
        update_centroids([], [], 2)

def test_uc_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        update_centroids([[1, 2], [3, 4]], [0], 2)

def test_uc_raises_on_non_list():
    with pytest.raises(TypeError):
        update_centroids("abc", [0, 1, 2], 2)


# ============================================================
# F4: compute_inertia (多组独特 expected)
# ============================================================

def test_ci_well_clustered():
    """X=[[0,0],[2,0],[10,10],[12,10]] labels=[0,0,1,1] centroids=[[1,0],[11,10]]
    inertia = 1+1+1+1 = 4"""
    r = compute_inertia([[0, 0], [2, 0], [10, 10], [12, 10]],
                       [0, 0, 1, 1], [[1, 0], [11, 10]])
    assert abs(r - 4.0) < TOL

def test_ci_perfect_centers():
    """sample == centroid → inertia=0"""
    r = compute_inertia([[5, 5], [10, 10]], [0, 1], [[5, 5], [10, 10]])
    assert abs(r - 0.0) < TOL

def test_ci_single_cluster():
    """[[0,0],[3,4]] labels=[0,0] centroid=[[0,0]] → 0+25 = 25"""
    r = compute_inertia([[0, 0], [3, 4]], [0, 0], [[0, 0]])
    assert abs(r - 25.0) < TOL

def test_ci_three_clusters():
    """X=[[0],[1],[10],[11],[20]] labels=[0,0,1,1,2] centroids=[[0.5],[10.5],[20]]
    inertia = 0.25+0.25+0.25+0.25+0 = 1.0"""
    r = compute_inertia([[0], [1], [10], [11], [20]],
                       [0, 0, 1, 1, 2], [[0.5], [10.5], [20]])
    assert abs(r - 1.0) < TOL

def test_ci_far_centers():
    """X=[[0,0]] labels=[0] centroid=[[3,4]] → 25"""
    r = compute_inertia([[0, 0]], [0], [[3, 4]])
    assert abs(r - 25.0) < TOL

def test_ci_raises_on_empty():
    with pytest.raises(ValueError):
        compute_inertia([], [], [])

def test_ci_raises_on_label_out_of_range():
    """labels 含越界值"""
    with pytest.raises(ValueError):
        compute_inertia([[1, 2]], [5], [[0, 0]])

def test_ci_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_inertia("abc", [0], [[0, 0]])
