import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj10 import stratified_kfold_split, cross_val_score, bootstrap_sample, compute_learning_curve
import numpy as np

def test_kfold_split():
    y = np.array([0, 0, 0, 1, 1, 1, 0, 0])
    splits = stratified_kfold_split(y, n_splits=4, random_state=42)
    assert splits is not None, "pass-only 不得分"
    assert len(splits) == 4

def test_bootstrap():
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    y = np.array([0, 1, 0, 1])
    X_boot, y_boot = bootstrap_sample(X, y)
    assert X_boot is not None, "pass-only 不得分"
    assert len(X_boot) == len(X) and len(y_boot) == len(y)

def test_learning_curve():
    train_sizes = np.array([10, 20, 30, 40])
    train_scores = np.random.rand(4, 5)
    test_scores = np.random.rand(4, 5)
    result = compute_learning_curve(train_sizes, train_scores, test_scores)
    assert result is not None, "pass-only 不得分"
    assert 'train_mean' in result and 'test_mean' in result
