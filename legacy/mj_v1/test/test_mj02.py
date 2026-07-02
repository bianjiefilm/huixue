import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj02 import get_data_overview, calculate_correlation, find_high_correlation_pairs, detect_outliers_iqr
import pandas as pd
import numpy as np

def test_get_data_overview():
    df = pd.DataFrame({'a': [1, 2, None, 4], 'b': ['x', 'y', 'z', 'w'], 'c': [1.0, 2.0, 3.0, 4.0]})
    result = get_data_overview(df)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict)
    assert result['n_rows'] == 4
    assert result['n_columns'] == 3

def test_calculate_correlation():
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [2, 4, 6, 8, 10]})
    result = calculate_correlation(df)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, pd.DataFrame)
    assert result.shape == (2, 2)

def test_find_high_correlation_pairs():
    df = pd.DataFrame({'a': [1, 2, 3, 4, 5], 'b': [2, 4, 6, 8, 10], 'c': [1, 3, 5, 7, 9]})
    result = find_high_correlation_pairs(df, threshold=0.9)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, list)
    assert len(result) >= 1

def test_detect_outliers_iqr():
    df = pd.DataFrame({'val': [1, 2, 3, 4, 5, 100]})
    result = detect_outliers_iqr(df, 'val')
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, list)
    assert len(result) >= 1
