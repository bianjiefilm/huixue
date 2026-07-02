import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj11 import bagging_predict, weighted_bagging_predict, stacking_predict, adaboost_weights_update
import numpy as np

def test_bagging_predict():
    X = np.array([[1], [2], [3]])
    base_preds = np.array([[0, 1, 1], [1, 1, 0], [1, 1, 1]])
    result = bagging_predict(X, base_preds)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (3,)
    assert all(v in (0, 1) for v in result)

def test_weighted_bagging():
    X = np.array([[1], [2], [3]])
    base_preds = np.array([[0, 1, 1], [1, 1, 0]])
    weights = np.array([0.7, 0.3])
    result = weighted_bagging_predict(X, base_preds, weights)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (3,)

class DummyMetaModel:
    def predict(self, X):
        return np.zeros(X.shape[0])

def test_stacking_predict():
    meta_features = np.array([[0.8, 0.2], [0.3, 0.7], [0.6, 0.4]])
    model = DummyMetaModel()
    result = stacking_predict(meta_features, model)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (3,)

def test_adaboost_weights():
    weights = np.array([1.0, 1.0, 1.0, 1.0])
    y_true = np.array([1, 1, -1, -1])
    y_pred = np.array([1, -1, -1, 1])
    alpha = 0.5
    result = adaboost_weights_update(weights, y_true, y_pred, alpha)
    assert result is not None, "pass-only 不得分"
    assert result.shape == (4,)
    assert np.all(result >= 0)
