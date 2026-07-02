import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj04 import sigmoid, logistic_regression_predict, compute_metrics, find_best_threshold
import numpy as np

def test_sigmoid():
    assert sigmoid(0) is not None
    result = sigmoid(np.array([0, 1, -1]))
    assert abs(result[0] - 0.5) < 0.01, f"sigmoid(0) 应为 0.5，实际 {result[0]}"
    assert 0 < result[1] < 1
    assert 0 < result[2] < 1

def test_logistic_predict():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    w = np.array([0.5, -0.3])
    b = 0.1
    result = logistic_regression_predict(X, w, b)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (3,)
    assert all(0 <= r <= 1 for r in result)

def test_compute_metrics():
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 0, 0, 0, 1])
    result = compute_metrics(y_true, y_pred)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict)
    assert all(k in result for k in ['accuracy', 'precision', 'recall', 'f1'])

def test_find_best_threshold():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.4, 0.6, 0.9])
    best_t, best_f1 = find_best_threshold(y_true, y_prob)
    assert best_t is not None, "pass-only 不得分"
    assert 0 <= best_t <= 1
    assert 0 <= best_f1 <= 1
