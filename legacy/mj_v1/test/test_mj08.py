import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj08 import pca_fit, pca_transform, explained_variance_ratio, reconstruct_from_pca
import numpy as np

def test_pca_fit():
    X = np.array([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]])
    components, variance = pca_fit(X, n_components=2)
    assert components is not None, "pass-only 不得分"
    assert components.shape == (2, 2)
    assert variance.shape == (2,)

def test_pca_transform():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    components = np.array([[0.71, 0.71], [-0.71, 0.71]])
    result = pca_transform(X, components)
    assert result is not None, "pass-only 不得分"
    assert result.shape[1] == 2

def test_explained_variance():
    variance = np.array([9.0, 1.0])
    ratio = explained_variance_ratio(variance)
    assert ratio is not None, "pass-only 不得分"
    assert abs(ratio.sum() - 1.0) < 0.01
    assert ratio[0] == 0.9

def test_reconstruct():
    X_pca = np.array([[1.0, 2.0], [3.0, 4.0]])
    components = np.array([[0.71, 0.71], [-0.71, 0.71]])
    mean = np.array([2.0, 3.0])
    result = reconstruct_from_pca(X_pca, components, mean)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (2, 2)
