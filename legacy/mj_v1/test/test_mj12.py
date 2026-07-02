import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj12 import load_churn_data, preprocess_and_split, train_and_compare_models, evaluate_model, get_top_features
import pandas as pd
import numpy as np

def test_load_data():
    df = load_churn_data()
    assert df is not None, "pass-only 不得分"
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'churn' in df.columns

def test_preprocess():
    df = load_churn_data()
    result = preprocess_and_split(df)
    assert result is not None, "pass-only 不得分"
    assert len(result) == 5
    X_train, X_test, y_train, y_test, scaler = result
    assert X_train.shape[0] + X_test.shape[0] == len(df)

def test_train_compare():
    X = np.random.rand(100, 5)
    y = np.random.randint(0, 2, 100)
    result = train_and_compare_models(X, y)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict)
    assert len(result) >= 2

def test_get_top_features():
    feature_names = ['tenure', 'monthly_charges', 'total_charges', 'contract_type', 'tech_support']
    class FakeModel:
        @property
        def feature_importances_(self):
            return np.array([0.4, 0.3, 0.1, 0.1, 0.1])
    result = get_top_features(FakeModel(), feature_names, top_k=3)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, list)
    assert len(result) <= 3
