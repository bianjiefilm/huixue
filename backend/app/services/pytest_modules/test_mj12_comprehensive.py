"""MJ12 综合关 pytest_module 测试."""
import pytest
from student_mj12 import (
    load_churn_data,
    preprocess_and_split,
    train_and_compare_models,
    evaluate_model,
)

TOL = 1e-6


# F1: load_churn_data (5 cases)
def test_load_returns_dict():
    d = load_churn_data()
    assert isinstance(d, dict)

def test_load_has_5_keys():
    d = load_churn_data()
    for k in ['tenure', 'monthly_charges', 'contract_type', 'tech_support', 'churn']:
        assert k in d

def test_load_length_100():
    d = load_churn_data()
    for k in d:
        assert len(d[k]) == 100

def test_load_churn_imbalance():
    d = load_churn_data()
    pos = sum(1 for c in d['churn'] if c == 1)
    # 80/20 imbalance, allow ±5
    assert 15 <= pos <= 25

def test_load_value_ranges():
    d = load_churn_data()
    # 红线: 必须实质有值, 不空
    assert len(d['tenure']) > 0
    assert all(1 <= t <= 72 for t in d['tenure'])
    assert all(30.0 <= m <= 150.0 for m in d['monthly_charges'])
    assert all(c in ['Month-to-month', 'One year', 'Two year'] for c in d['contract_type'])
    assert all(s in ['Yes', 'No'] for s in d['tech_support'])
    assert all(c in (0, 1) for c in d['churn'])


# F2: preprocess_and_split (6 cases)
def test_pp_returns_tuple_4():
    d = load_churn_data()
    r = preprocess_and_split(d)
    assert len(r) == 4

def test_pp_split_size():
    d = load_churn_data()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d, test_size=0.2)
    assert len(X_te) == 20  # 100 * 0.2
    assert len(X_tr) == 80
    assert len(y_tr) == 80
    assert len(y_te) == 20

def test_pp_features_4():
    d = load_churn_data()
    X_tr, _, _, _ = preprocess_and_split(d)
    assert len(X_tr) > 0
    assert all(len(row) == 4 for row in X_tr)

def test_pp_y_binary():
    d = load_churn_data()
    _, _, y_tr, y_te = preprocess_and_split(d)
    assert len(y_tr) > 0 and len(y_te) > 0
    assert all(y in (0, 1) for y in y_tr + y_te)

def test_pp_raises_on_missing_target():
    d = load_churn_data()
    with pytest.raises(ValueError):
        preprocess_and_split(d, target_col="nonexistent")

def test_pp_raises_on_non_dict():
    with pytest.raises(TypeError):
        preprocess_and_split("not dict")


# F3: train_and_compare_models (4 cases)
def test_tcm_returns_dict():
    d = load_churn_data()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    r = train_and_compare_models(X_tr, y_tr, X_te, y_te)
    assert isinstance(r, dict)

def test_tcm_has_3_models():
    d = load_churn_data()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    r = train_and_compare_models(X_tr, y_tr, X_te, y_te)
    assert len(r) >= 3

def test_tcm_accuracies_in_range():
    d = load_churn_data()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    r = train_and_compare_models(X_tr, y_tr, X_te, y_te)
    assert len(r) >= 3
    for k, v in r.items():
        assert 0 <= v <= 1, f"{k}={v} out of [0,1]"

def test_tcm_at_least_one_above_baseline():
    """红线: 至少 1 个 model accuracy >= 0.6 (优于 50% 随机)"""
    d = load_churn_data()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    r = train_and_compare_models(X_tr, y_tr, X_te, y_te)
    assert max(r.values()) >= 0.6

def test_tcm_raises_on_empty():
    with pytest.raises(ValueError):
        train_and_compare_models([], [], [], [])


# F4: evaluate_model (8 cases)
def test_em_perfect():
    r = evaluate_model([1, 1, 0, 0], [1, 1, 0, 0])
    assert abs(r['accuracy'] - 1.0) < TOL
    assert abs(r['precision'] - 1.0) < TOL
    assert abs(r['recall'] - 1.0) < TOL
    assert abs(r['f1'] - 1.0) < TOL
    assert abs(r['specificity'] - 1.0) < TOL

def test_em_all_wrong():
    r = evaluate_model([1, 0], [0, 1])
    assert r['accuracy'] == 0.0

def test_em_keys():
    r = evaluate_model([0, 1], [0, 1])
    for k in ['accuracy', 'precision', 'recall', 'f1', 'specificity']:
        assert k in r

def test_em_imbalanced():
    # 8 neg + 2 pos all predicted neg → recall=0 precision=0 (no TP+FP)
    r = evaluate_model([0]*8 + [1]*2, [0]*10)
    assert r['accuracy'] == 0.8
    assert r['recall'] == 0
    assert r['specificity'] == 1.0

def test_em_specificity():
    # 2 pos + 2 neg, all predicted pos → spec=0
    r = evaluate_model([1, 1, 0, 0], [1, 1, 1, 1])
    assert r['specificity'] == 0

def test_em_raises_on_empty():
    with pytest.raises(ValueError):
        evaluate_model([], [])

def test_em_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        evaluate_model([1, 0], [1])

def test_em_raises_on_invalid_label():
    with pytest.raises(ValueError):
        evaluate_model([0, 2], [0, 1])
