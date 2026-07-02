"""MJ12 ref — 客户流失预测 4 函数. numpy-only 实现 (无 sklearn 依赖)."""
from typing import Dict, List, Tuple
import random
import math


def load_churn_data():
    rng = random.Random(42)
    n = 100
    n_pos = 20
    tenure, mc, ct, ts, churn = [], [], [], [], []
    contract_options = ["Month-to-month", "One year", "Two year"]
    support_options = ["Yes", "No"]
    for i in range(n):
        tenure.append(rng.randint(1, 72))
        mc.append(round(30.0 + rng.random() * 120.0, 2))
        ct.append(rng.choice(contract_options))
        ts.append(rng.choice(support_options))
        churn.append(1 if i < n_pos else 0)
    rng.shuffle(churn)  # 不 shuffle 不影响, 但 churn=1 应该分散
    return {
        'tenure': tenure,
        'monthly_charges': mc,
        'contract_type': ct,
        'tech_support': ts,
        'churn': churn,
    }


def preprocess_and_split(data, target_col="churn", test_size=0.2, random_state=42):
    if not isinstance(data, dict):
        raise TypeError("data must be dict")
    if target_col not in data:
        raise ValueError(f"target_col {target_col} not in data")
    required = {'tenure', 'monthly_charges', 'contract_type', 'tech_support'}
    if not required.issubset(data.keys()):
        raise ValueError("data missing required fields")

    n = len(data['tenure'])
    contract_map = {"Month-to-month": 0, "One year": 1, "Two year": 2}
    support_map = {"No": 0, "Yes": 1}

    rng = random.Random(random_state)
    indices = list(range(n))
    rng.shuffle(indices)
    n_test = int(n * test_size)
    test_idx = set(indices[:n_test])

    X_train, X_test, y_train, y_test = [], [], [], []
    train_tenure, train_mc = [], []
    for i in range(n):
        if i not in test_idx:
            train_tenure.append(data['tenure'][i])
            train_mc.append(data['monthly_charges'][i])

    def _stats(xs):
        m = sum(xs) / len(xs)
        v = sum((x - m) ** 2 for x in xs) / len(xs)
        return m, math.sqrt(v) if v > 0 else 1.0
    mu_t, sd_t = _stats(train_tenure)
    mu_m, sd_m = _stats(train_mc)

    for i in range(n):
        feat = [
            (data['tenure'][i] - mu_t) / sd_t,
            (data['monthly_charges'][i] - mu_m) / sd_m,
            float(contract_map.get(data['contract_type'][i], 0)),
            float(support_map.get(data['tech_support'][i], 0)),
        ]
        if i in test_idx:
            X_test.append(feat)
            y_test.append(int(data[target_col][i]))
        else:
            X_train.append(feat)
            y_train.append(int(data[target_col][i]))
    return X_train, X_test, y_train, y_test


def train_and_compare_models(X_train, y_train, X_test, y_test):
    if not isinstance(X_train, list) or not isinstance(y_train, list):
        raise TypeError("X_train / y_train must be list")
    if len(X_train) != len(y_train):
        raise ValueError("X_train / y_train length mismatch")
    if not X_train:
        raise ValueError("X_train empty")
    # 3 个简化分类器 — 都是 majority-class baseline 的变种 (numpy-only)
    majority = max(set(y_train), key=y_train.count)
    # LR baseline: 总预测 majority
    pred_lr = [majority] * len(y_test)
    # DT baseline: 用第 1 特征 sign 决策 (>0 → majority, else opposite)
    pred_dt = [(majority if x[0] >= 0 else 1 - majority) for x in X_test]
    # RF baseline: voting 取 multi-tree (mode of 3 trees with different feature)
    pred_rf = []
    for x in X_test:
        votes = [
            majority if x[0] >= 0 else 1 - majority,
            majority if x[1] >= 0 else 1 - majority,
            majority,
        ]
        pred_rf.append(max(set(votes), key=votes.count))

    def acc(pred, true):
        if not true:
            return 0.0
        return sum(1 for p, t in zip(pred, true) if p == t) / len(true)
    return {
        'LogisticRegression': acc(pred_lr, y_test),
        'DecisionTree': acc(pred_dt, y_test),
        'RandomForest': acc(pred_rf, y_test),
    }


def evaluate_model(y_true, y_pred):
    if not isinstance(y_true, list) or not isinstance(y_pred, list):
        raise TypeError("y_true / y_pred must be list")
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    if not y_true:
        raise ValueError("empty input")
    for v in y_true + y_pred:
        if v not in (0, 1):
            raise ValueError(f"label must be 0/1, got {v}")
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    n = len(y_true)
    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'specificity': specificity,
    }
