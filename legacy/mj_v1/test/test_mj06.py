import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj06 import mean_squared_error, mean_absolute_error, r2_score, ridge_loss, normal_equation
import numpy as np

def test_mse():
    y_true = np.array([3, -0.5, 2, 7])
    y_pred = np.array([2.5, 0.0, 2, 8])
    result = mean_squared_error(y_true, y_pred)
    assert result is not None, "pass-only 不得分"
    assert abs(result - 0.375) < 0.01, f"MSE 应为 0.375，实际 {result}"

def test_mae():
    y_true = np.array([3, -0.5, 2, 7])
    y_pred = np.array([2.5, 0.0, 2, 8])
    result = mean_absolute_error(y_true, y_pred)
    assert result is not None, "pass-only 不得分"
    assert abs(result - 0.5) < 0.01

def test_r2():
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
    result = r2_score(y_true, y_pred)
    assert result is not None, "pass-only 不得分"
    assert 0 <= result <= 1

def test_ridge_loss():
    X = np.array([[1, 1], [1, 2], [1, 3]])
    y = np.array([1, 2, 3])
    weights = np.array([0.5, 0.5])
    result = ridge_loss(X, y, weights, alpha=1.0)
    assert result is not None, "pass-only 不得分"
    assert result > 0

def test_normal_equation():
    X = np.array([[1, 1], [1, 2], [1, 3], [1, 4]])
    y = np.array([1, 2, 3, 4])
    result = normal_equation(X, y)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (2,)
