import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj05 import compute_gini, find_best_split, random_forest_predict, get_feature_importance
import numpy as np

def test_compute_gini():
    labels = np.array([0, 0, 0, 0])
    g = compute_gini(labels)
    assert g is not None, "pass-only 不得分"
    assert g == 0.0, f"纯集合基尼应为0，实际 {g}"
    labels2 = np.array([0, 1])
    g2 = compute_gini(labels2)
    assert 0 < g2 <= 0.5, f"二分类最大基尼 0.5，实际 {g2}"

def test_find_best_split():
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([0, 0, 1, 1, 1])
    result = find_best_split(X, y, [0])
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict)
    assert 'gini_gain' in result

def test_random_forest_predict():
    X = np.array([[1], [2], [3]])
    trees = [{'pred': np.array([0, 1, 0])}, {'pred': np.array([0, 0, 0])}]
    result = random_forest_predict(X, trees, n_classes=2)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (3,)

def test_get_feature_importance():
    importance_dicts = [{0: 10, 1: 5}, {0: 5, 1: 10}]
    result = get_feature_importance(importance_dicts)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, np.ndarray)
    assert len(result) >= 2
