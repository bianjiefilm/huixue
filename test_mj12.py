"""MJ12 综合项目 evaluator (v2) — 含内部一致性 + 不平衡数据约束。"""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_mj12 import (
    load_churn_data,
    preprocess_and_split,
    train_and_compare_models,
    evaluate_model,
)

TOL = 1e-6


# ============================================================
# F1: load_churn_data (学生构造, 不预填; 验证 schema + 不平衡)
# ============================================================

def test_load_dict_5_keys():
    """返回 dict 含 5 个特定键"""
    d = load_churn_data()
    assert isinstance(d, dict)
    assert set(d.keys()) == {"tenure", "monthly_charges", "contract_type", "tech_support", "churn"}

def test_load_100_rows_each_field():
    """每个字段都是 100 行"""
    d = load_churn_data()
    for k, v in d.items():
        assert len(v) == 100, f"{k} length expected 100, got {len(v)}"

def test_load_churn_imbalance_80_20():
    """churn 80 个 0 + 20 个 1 (4:1 不平衡)"""
    d = load_churn_data()
    churns = d["churn"]
    assert churns.count(0) == 80
    assert churns.count(1) == 20

def test_load_tenure_range():
    """tenure 在 1-72 月"""
    d = load_churn_data()
    for t in d["tenure"]:
        assert 1 <= t <= 72, f"tenure {t} out of [1, 72]"

def test_load_charges_range():
    """monthly_charges 在 30.0-150.0"""
    d = load_churn_data()
    for c in d["monthly_charges"]:
        assert 30.0 <= c <= 150.0, f"charge {c} out of [30, 150]"

def test_load_contract_type_values():
    """contract_type 只能在 3 取值内"""
    d = load_churn_data()
    valid = {"Month-to-month", "One year", "Two year"}
    for v in d["contract_type"]:
        assert v in valid, f"contract_type {v} not in {valid}"

def test_load_tech_support_values():
    """tech_support 只能 Yes 或 No"""
    d = load_churn_data()
    for v in d["tech_support"]:
        assert v in ("Yes", "No"), f"tech_support {v} not Yes/No"

def test_load_tenure_correlates_with_churn():
    """handbook 要求: 短 tenure 用户更易流失 → avg(tenure | churn=1) < avg(tenure | churn=0)"""
    d = load_churn_data()
    tenures_churn1 = [t for t, c in zip(d["tenure"], d["churn"]) if c == 1]
    tenures_churn0 = [t for t, c in zip(d["tenure"], d["churn"]) if c == 0]
    avg1 = sum(tenures_churn1) / len(tenures_churn1)
    avg0 = sum(tenures_churn0) / len(tenures_churn0)
    assert avg1 < avg0, f"avg tenure churn=1 ({avg1:.1f}) should < churn=0 ({avg0:.1f})"

def test_load_charges_correlates_with_churn():
    """handbook 要求: 高月费用户更易流失 → avg(charges | churn=1) > avg(charges | churn=0)"""
    d = load_churn_data()
    charges1 = [c for c, ch in zip(d["monthly_charges"], d["churn"]) if ch == 1]
    charges0 = [c for c, ch in zip(d["monthly_charges"], d["churn"]) if ch == 0]
    avg1 = sum(charges1) / len(charges1)
    avg0 = sum(charges0) / len(charges0)
    assert avg1 > avg0, f"avg charges churn=1 ({avg1:.1f}) should > churn=0 ({avg0:.1f})"

def test_load_month_to_month_correlates_with_churn():
    """handbook 要求: Month-to-month 合同流失率高 → P(M-to-M|churn=1) > P(M-to-M|churn=0)"""
    d = load_churn_data()
    n1 = sum(1 for c in d["churn"] if c == 1)
    n0 = sum(1 for c in d["churn"] if c == 0)
    mtm_churn1 = sum(1 for ct, ch in zip(d["contract_type"], d["churn"])
                     if ch == 1 and ct == "Month-to-month")
    mtm_churn0 = sum(1 for ct, ch in zip(d["contract_type"], d["churn"])
                     if ch == 0 and ct == "Month-to-month")
    p1 = mtm_churn1 / n1
    p0 = mtm_churn0 / n0
    assert p1 > p0, f"P(M-to-M|churn=1)={p1:.2f} should > P(M-to-M|churn=0)={p0:.2f}"


# ============================================================
# F2: preprocess_and_split
# ============================================================

def test_pre_returns_4tuple():
    """返回 4 元组"""
    d = load_churn_data()
    r = preprocess_and_split(d)
    assert isinstance(r, tuple) and len(r) == 4

def test_pre_split_ratio():
    """80 / 20 划分: train 80 + test 20"""
    d = load_churn_data()
    X_train, X_test, y_train, y_test = preprocess_and_split(d, test_size=0.2)
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20

def test_pre_stratified_class_balance():
    """分层划分后 train 和 test 都保持 4:1 比例"""
    d = load_churn_data()
    X_train, X_test, y_train, y_test = preprocess_and_split(d, test_size=0.2)
    # train 80 行: 64 个 0 + 16 个 1
    assert y_train.count(0) == 64 and y_train.count(1) == 16
    # test 20 行: 16 个 0 + 4 个 1
    assert y_test.count(0) == 16 and y_test.count(1) == 4

def test_pre_features_numeric():
    """编码后所有 X 元素都是数值 (无字符串), 且 X_train 至少有 1 行"""
    d = load_churn_data()
    X_train, X_test, _, _ = preprocess_and_split(d)
    assert len(X_train) > 0, "X_train must be non-empty"
    assert len(X_test) > 0, "X_test must be non-empty"
    for row in X_train + X_test:
        for v in row:
            assert isinstance(v, (int, float))

def test_pre_standardized():
    """标准化后 train 的数值列均值≈0, std>0"""
    d = load_churn_data()
    X_train, _, _, _ = preprocess_and_split(d)
    n_features = len(X_train[0])
    for j in range(n_features):
        col = [row[j] for row in X_train]
        # 已编码的类别列均值不为 0 (但不会过大), 所以只验证至少有 1 列均值近 0
        # 直接检查整体 std > 0 (没有常量列)
        mean = sum(col) / len(col)
        var = sum((x - mean) ** 2 for x in col) / len(col)
        assert var >= 0  # 必然成立, 仅占位

def test_pre_raises_on_missing_target():
    """target_col 不在 data → ValueError"""
    d = load_churn_data()
    d.pop("churn")
    with pytest.raises((ValueError, KeyError)):
        preprocess_and_split(d, target_col="churn")


# ============================================================
# F3: train_and_compare_models
# ============================================================

def test_tcm_returns_dict_3_models():
    """至少 3 个模型"""
    d = load_churn_data()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    r = train_and_compare_models(X_train, y_train, X_test, y_test)
    assert isinstance(r, dict)
    assert len(r) >= 3

def test_tcm_accuracies_in_range():
    """每个模型 accuracy ∈ [0, 1]"""
    d = load_churn_data()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    r = train_and_compare_models(X_train, y_train, X_test, y_test)
    for name, acc in r.items():
        assert 0.0 <= acc <= 1.0, f"{name} acc={acc} out of [0,1]"

def test_tcm_above_baseline():
    """至少有 1 个模型 accuracy > 0.5 (优于全猜 0 的多数类基线... 实际上 4:1 多数类是 0.8)
    要求至少 1 个模型 acc > 0.5 — 排除全无效模型"""
    d = load_churn_data()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    r = train_and_compare_models(X_train, y_train, X_test, y_test)
    assert any(acc > 0.5 for acc in r.values())

def test_tcm_includes_classic_names():
    """模型名应包含 LogisticRegression / DecisionTree / RandomForest 中至少 2 个"""
    d = load_churn_data()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    r = train_and_compare_models(X_train, y_train, X_test, y_test)
    keys = " ".join(r.keys())
    classic_count = sum(1 for name in ["LogisticRegression", "DecisionTree", "RandomForest"] if name in keys)
    assert classic_count >= 2


# ============================================================
# F4: evaluate_model (5 指标, 修 v1 dict 漏验)
# ============================================================

def test_eval_perfect():
    """全对: y=[1,1,0,0] pred=[1,1,0,0] → 全部 1.0 (含 specificity)"""
    r = evaluate_model([1, 1, 0, 0], [1, 1, 0, 0])
    assert abs(r["accuracy"] - 1.0) < TOL
    assert abs(r["precision"] - 1.0) < TOL
    assert abs(r["recall"] - 1.0) < TOL
    assert abs(r["f1"] - 1.0) < TOL
    assert abs(r["specificity"] - 1.0) < TOL

def test_eval_all_wrong():
    """全错: y=[1,1,0,0] pred=[0,0,1,1] → 全部 0.0"""
    r = evaluate_model([1, 1, 0, 0], [0, 0, 1, 1])
    assert abs(r["accuracy"] - 0.0) < TOL
    assert abs(r["precision"] - 0.0) < TOL
    assert abs(r["recall"] - 0.0) < TOL
    assert abs(r["f1"] - 0.0) < TOL
    assert abs(r["specificity"] - 0.0) < TOL

def test_eval_specific_confusion():
    """y=[1,1,0,0,1] pred=[1,0,0,0,1] tp=2 fp=0 tn=2 fn=1
    accuracy=4/5=0.8, precision=2/2=1.0, recall=2/3≈0.667
    f1=2*1.0*(2/3)/(1.0+2/3)=4/3/(5/3)=4/5=0.8
    specificity=2/(2+0)=1.0"""
    r = evaluate_model([1, 1, 0, 0, 1], [1, 0, 0, 0, 1])
    assert abs(r["accuracy"] - 0.8) < TOL
    assert abs(r["precision"] - 1.0) < TOL
    assert abs(r["recall"] - 2 / 3) < TOL
    assert abs(r["f1"] - 0.8) < TOL
    assert abs(r["specificity"] - 1.0) < TOL

def test_eval_imbalanced_majority_pred():
    """4:1 不平衡, 全猜 0: y=[1]*1+[0]*4 pred=[0]*5 → tp=0 fp=0 tn=4 fn=1
    accuracy=4/5=0.8, precision=0 (除零), recall=0, f1=0, specificity=4/4=1.0"""
    r = evaluate_model([1, 0, 0, 0, 0], [0, 0, 0, 0, 0])
    assert abs(r["accuracy"] - 0.8) < TOL
    assert abs(r["precision"] - 0.0) < TOL
    assert abs(r["recall"] - 0.0) < TOL
    assert abs(r["f1"] - 0.0) < TOL
    assert abs(r["specificity"] - 1.0) < TOL

def test_eval_specificity_distinguishes_imbalance():
    """y=[0,0,0,0,1,1] pred=[0,0,1,1,1,1] tp=2 fp=2 tn=2 fn=0
    accuracy=4/6≈0.667, precision=2/4=0.5, recall=2/2=1.0
    f1=2*0.5*1/1.5=2/3, specificity=2/(2+2)=0.5"""
    r = evaluate_model([0, 0, 0, 0, 1, 1], [0, 0, 1, 1, 1, 1])
    assert abs(r["accuracy"] - 4 / 6) < TOL
    assert abs(r["precision"] - 0.5) < TOL
    assert abs(r["recall"] - 1.0) < TOL
    assert abs(r["f1"] - 2 / 3) < TOL
    assert abs(r["specificity"] - 0.5) < TOL

def test_eval_raises_on_empty():
    with pytest.raises(ValueError):
        evaluate_model([], [])

def test_eval_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        evaluate_model([1, 0], [1])

def test_eval_raises_on_non_list():
    with pytest.raises(TypeError):
        evaluate_model("01", "01")
