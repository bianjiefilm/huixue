"""NN12 综合项目 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn12 import (
    load_mnist_subset,
    preprocess_and_split,
    train_simple_classifier,
    evaluate_classifier,
)

TOL = 1e-4


# F1: load_mnist_subset
def test_load_dict_2_keys():
    d = load_mnist_subset()
    assert isinstance(d, dict)
    assert set(d.keys()) == {"images", "labels"}

def test_load_100_samples():
    d = load_mnist_subset()
    assert len(d["images"]) == 100
    assert len(d["labels"]) == 100

def test_load_image_shape_8x8():
    d = load_mnist_subset()
    for img in d["images"]:
        assert len(img) == 8
        for row in img:
            assert len(row) == 8

def test_load_pixel_range():
    d = load_mnist_subset()
    for img in d["images"]:
        for row in img:
            for v in row:
                assert 0 <= v <= 16

def test_load_labels_in_0_9():
    d = load_mnist_subset()
    for lab in d["labels"]:
        assert 0 <= lab <= 9

def test_load_class_imbalance():
    """10 类比例 [5,8,10,12,15,8,10,12,10,10]"""
    d = load_mnist_subset()
    counts = [d["labels"].count(c) for c in range(10)]
    expected = [5, 8, 10, 12, 15, 8, 10, 12, 10, 10]
    assert counts == expected

def test_load_pixel_diversity():
    """图像不能全 0 或全 16 (有变化)"""
    d = load_mnist_subset()
    flat_all = [v for img in d["images"] for row in img for v in row]
    assert min(flat_all) < max(flat_all)


# F2: preprocess_and_split
def test_pre_returns_4tuple():
    d = load_mnist_subset()
    r = preprocess_and_split(d)
    assert isinstance(r, tuple) and len(r) == 4

def test_pre_split_80_20():
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    assert len(X_train) == 80 and len(X_test) == 20

def test_pre_flatten_to_64():
    d = load_mnist_subset()
    X_train, _, _, _ = preprocess_and_split(d)
    for row in X_train:
        assert len(row) == 64

def test_pre_stratified_class_balance():
    """80/20 分层后, train 类计数 = ceil(0.8 × 原计数), 大致保持比例"""
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    # 至少每类在 train 中有 >=1 个 (分层保证)
    counts_train = [y_train.count(c) for c in range(10)]
    for c in counts_train:
        assert c >= 1

def test_pre_numeric_features():
    d = load_mnist_subset()
    X_train, _, _, _ = preprocess_and_split(d)
    for row in X_train:
        for v in row:
            assert isinstance(v, (int, float))

def test_pre_raises_on_missing_field():
    """data 缺 images → 抛错"""
    d = load_mnist_subset()
    d.pop("images")
    with pytest.raises((ValueError, KeyError)):
        preprocess_and_split(d)


# F3: train_simple_classifier
def test_train_returns_dict():
    d = load_mnist_subset()
    X_train, _, y_train, _ = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    assert isinstance(state, dict)
    assert "W" in state and "b" in state

def test_train_W_shape():
    d = load_mnist_subset()
    X_train, _, y_train, _ = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    assert len(state["W"]) == 64
    for row in state["W"]:
        assert len(row) == 10

def test_train_b_shape():
    d = load_mnist_subset()
    X_train, _, y_train, _ = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    assert len(state["b"]) == 10

def test_train_W_not_zero_after_training():
    """训练后 W 应该不再是初始全 0 (有更新)"""
    d = load_mnist_subset()
    X_train, _, y_train, _ = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=10, lr=0.1)
    flat = [v for row in state["W"] for v in row]
    # 至少有一些非零权重
    assert any(abs(v) > 1e-6 for v in flat)


# F4: evaluate_classifier
def test_eval_returns_5_keys():
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    r = evaluate_classifier(state, X_test, y_test)
    assert set(r.keys()) == {"accuracy", "macro_precision", "macro_recall",
                              "macro_f1", "per_class_accuracy"}

def test_eval_accuracy_in_range():
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    r = evaluate_classifier(state, X_test, y_test)
    assert 0.0 <= r["accuracy"] <= 1.0

def test_eval_per_class_length_10():
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    r = evaluate_classifier(state, X_test, y_test)
    assert len(r["per_class_accuracy"]) == 10

def test_eval_above_baseline():
    """训练后准确率应高于随机猜测 (1/10 = 0.1)"""
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=20, lr=0.1)
    r = evaluate_classifier(state, X_test, y_test)
    # 100 样本简单线性, 至少应该 > 0.15 (优于纯随机)
    assert r["accuracy"] > 0.15

def test_eval_macro_metrics_in_range():
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    state = train_simple_classifier(X_train, y_train, n_epochs=5, lr=0.1)
    r = evaluate_classifier(state, X_test, y_test)
    for k in ["macro_precision", "macro_recall", "macro_f1"]:
        assert 0.0 <= r[k] <= 1.0

def test_eval_raises_on_invalid_state():
    d = load_mnist_subset()
    _, X_test, _, y_test = preprocess_and_split(d)
    with pytest.raises((ValueError, KeyError, TypeError)):
        evaluate_classifier({}, X_test, y_test)

def test_eval_actually_uses_state():
    """用 2 个不同的 state (零权重 vs 训练权重), accuracy 应不同 — 防 hardcode 返回常量"""
    d = load_mnist_subset()
    X_train, X_test, y_train, y_test = preprocess_and_split(d)
    state_zero = {"W": [[0.0] * 10 for _ in range(64)], "b": [0.0] * 10}
    state_trained = train_simple_classifier(X_train, y_train, n_epochs=20, lr=0.1)
    r_zero = evaluate_classifier(state_zero, X_test, y_test)
    r_trained = evaluate_classifier(state_trained, X_test, y_test)
    # accuracy/macro_f1 至少有一个不同
    different = (abs(r_zero["accuracy"] - r_trained["accuracy"]) > 0.01 or
                 abs(r_zero["macro_f1"] - r_trained["macro_f1"]) > 0.01)
    assert different, "两个不同 state 的评估结果不应相同"

def test_train_different_n_epochs_differ():
    """n_epochs=1 vs n_epochs=20 训练结果应不同"""
    d = load_mnist_subset()
    X_train, _, y_train, _ = preprocess_and_split(d)
    s1 = train_simple_classifier(X_train, y_train, n_epochs=1, lr=0.1)
    s20 = train_simple_classifier(X_train, y_train, n_epochs=20, lr=0.1)
    flat1 = [v for row in s1["W"] for v in row]
    flat20 = [v for row in s20["W"] for v in row]
    # 两个 W 必须不同
    diff = sum(abs(a - b) for a, b in zip(flat1, flat20))
    assert diff > 1e-6, "n_epochs 不同应得到不同 W"
