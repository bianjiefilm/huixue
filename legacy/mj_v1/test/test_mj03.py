import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj03 import encode_label, one_hot_encode, standardize, variance_threshold_selection
import pandas as pd
import numpy as np

def test_encode_label():
    s = pd.Series(['cat', 'dog', 'cat', 'bird'])
    encoded, mapping = encode_label(s)
    assert encoded is not None, "pass-only 不得分"
    assert len(set(encoded)) == 4
    assert isinstance(mapping, dict) and len(mapping) == 4

def test_one_hot_encode():
    df = pd.DataFrame({'a': [1, 2, 3], 'color': ['red', 'blue', 'red']})
    result = one_hot_encode(df, 'color')
    assert result is not None, "pass-only 不得分"
    assert 'color' in result.columns or any('color' in c for c in result.columns)

def test_standardize():
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    X_test = np.array([[2, 3]])
    X_tr, X_te = standardize(X_train, X_test)
    assert X_tr is not None, "pass-only 不得分"
    assert X_tr.shape == (3, 2) and X_te.shape == (1, 2)

def test_variance_threshold():
    X = np.array([[1, 100], [2, 200], [3, 300], [4, 400], [5, 500]])
    X_sel, indices = variance_threshold_selection(X, threshold=0.0)
    assert X_sel is not None, "pass-only 不得分"
    assert isinstance(indices, list)
