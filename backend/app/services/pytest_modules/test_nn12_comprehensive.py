"""NN12 综合关 pytest_module 测试."""
import pytest
from student_nn12 import (
    load_mnist_subset,
    preprocess_and_split,
    train_simple_classifier,
    evaluate_classifier,
)

TOL = 1e-6


# F1: load_mnist_subset (5 cases)
def test_load_returns_dict():
    d = load_mnist_subset()
    assert isinstance(d, dict)

def test_load_has_2_keys():
    d = load_mnist_subset()
    assert "images" in d and "labels" in d

def test_load_100_samples():
    d = load_mnist_subset()
    assert len(d["images"]) == 100
    assert len(d["labels"]) == 100

def test_load_image_shape():
    d = load_mnist_subset()
    assert len(d["images"]) > 0
    for img in d["images"]:
        assert len(img) == 8
        assert all(len(row) == 8 for row in img)

def test_load_labels_0_to_9():
    d = load_mnist_subset()
    assert all(0 <= l <= 9 for l in d["labels"])
    assert len(set(d["labels"])) >= 5  # 至少 5 类


# F2: preprocess_and_split (5 cases)
def test_pp_returns_4():
    d = load_mnist_subset()
    r = preprocess_and_split(d)
    assert len(r) == 4

def test_pp_split_size():
    d = load_mnist_subset()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d, test_size=0.2)
    assert len(X_te) == 20
    assert len(X_tr) == 80

def test_pp_features_64():
    d = load_mnist_subset()
    X_tr, _, _, _ = preprocess_and_split(d)
    assert len(X_tr) > 0
    assert all(len(row) == 64 for row in X_tr)

def test_pp_raises_on_missing():
    with pytest.raises(ValueError):
        preprocess_and_split({"foo": []})

def test_pp_raises_on_non_dict():
    with pytest.raises(TypeError):
        preprocess_and_split("not dict")


# F3: train_simple_classifier (4 cases)
def test_tsc_returns_dict():
    d = load_mnist_subset()
    X_tr, _, y_tr, _ = preprocess_and_split(d)
    r = train_simple_classifier(X_tr, y_tr, n_epochs=2)
    assert isinstance(r, dict)
    assert "W" in r and "b" in r
    # 红线: 实质 state, 不能空 dict
    assert len(r["W"]) > 0
    assert len(r["b"]) > 0

def test_tsc_W_shape():
    d = load_mnist_subset()
    X_tr, _, y_tr, _ = preprocess_and_split(d)
    r = train_simple_classifier(X_tr, y_tr, n_epochs=2)
    W = r["W"]
    assert len(W) == 64  # 64 features
    assert len(W[0]) == 10  # 10 classes

def test_tsc_b_shape():
    d = load_mnist_subset()
    X_tr, _, y_tr, _ = preprocess_and_split(d)
    r = train_simple_classifier(X_tr, y_tr, n_epochs=2)
    assert len(r["b"]) == 10

def test_tsc_raises_on_empty():
    with pytest.raises(ValueError):
        train_simple_classifier([], [], n_epochs=1)


# F4: evaluate_classifier (8 cases)
def test_ec_returns_dict():
    d = load_mnist_subset()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    state = train_simple_classifier(X_tr, y_tr, n_epochs=5)
    r = evaluate_classifier(state, X_te, y_te)
    assert isinstance(r, dict)


def test_ec_zero_state_predicts_class_0():
    """红线: W=0, b=0 时 logits 全 0, argmax=0, accuracy = (y==0 占比). hardcode 0.5 fail."""
    W = [[0.0] * 10 for _ in range(64)]
    b = [0.0] * 10
    # 5 个 class-0 + 5 个 class-1 sample → accuracy = 0.5 if predict 0, but
    # 用全 class-3 的 y_test 让 hardcode 0.5 不能通过
    X_test = [[0.0] * 64 for _ in range(10)]
    y_test = [3] * 10  # all class 3
    r = evaluate_classifier({"W": W, "b": b}, X_test, y_test)
    # zero-state predicts class 0, y_test 全是 3 → accuracy=0
    assert abs(r["accuracy"] - 0.0) < TOL, f"zero-state should give acc=0 (predict 0 on all-3), got {r['accuracy']}"

def test_ec_5_keys():
    d = load_mnist_subset()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    state = train_simple_classifier(X_tr, y_tr, n_epochs=5)
    r = evaluate_classifier(state, X_te, y_te)
    for k in ['accuracy', 'macro_precision', 'macro_recall', 'macro_f1', 'per_class_accuracy']:
        assert k in r


def test_ec_perfect_identity_accuracy():
    """红线: 给 perfect identity state + 对应 X_test, accuracy 应 = 1.0 (不是固定 0.5)"""
    # W = identity-like (64 features → 10 classes, 让前 10 features 各对应 1 类)
    W = [[0.0] * 10 for _ in range(64)]
    for k in range(10):
        W[k][k] = 1.0  # feature[k] 强信号 class k
    b = [0.0] * 10
    # X_test: 10 个 one-hot 向量, y_test = 0..9
    X_test = []
    for k in range(10):
        x = [0.0] * 64
        x[k] = 1.0
        X_test.append(x)
    y_test = list(range(10))
    r = evaluate_classifier({"W": W, "b": b}, X_test, y_test)
    assert abs(r["accuracy"] - 1.0) < TOL, f"perfect state should give acc=1.0, got {r['accuracy']}"

def test_ec_metrics_in_range():
    d = load_mnist_subset()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    state = train_simple_classifier(X_tr, y_tr, n_epochs=5)
    r = evaluate_classifier(state, X_te, y_te)
    for k in ['accuracy', 'macro_precision', 'macro_recall', 'macro_f1']:
        assert 0 <= r[k] <= 1, f"{k}={r[k]} out of [0,1]"

def test_ec_per_class_length():
    d = load_mnist_subset()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    state = train_simple_classifier(X_tr, y_tr, n_epochs=5)
    r = evaluate_classifier(state, X_te, y_te)
    assert len(r["per_class_accuracy"]) == 10

def test_ec_accuracy_state_dependent():
    """红线: 不同 state 应给不同 accuracy. hardcode 0.5 fail."""
    # Perfect state
    W_perf = [[0.0] * 10 for _ in range(64)]
    for k in range(10):
        W_perf[k][k] = 10.0
    b_zero = [0.0] * 10
    X_one_hot = []
    for k in range(10):
        x = [0.0] * 64
        x[k] = 1.0
        X_one_hot.append(x)
    y_perfect = list(range(10))
    r_perf = evaluate_classifier({"W": W_perf, "b": b_zero}, X_one_hot, y_perfect)
    # Anti-perfect state (强信号反向)
    W_anti = [[0.0] * 10 for _ in range(64)]
    for k in range(10):
        W_anti[k][(k + 1) % 10] = 10.0  # feature[k] → predict class (k+1)%10
    r_anti = evaluate_classifier({"W": W_anti, "b": b_zero}, X_one_hot, y_perfect)
    assert r_perf["accuracy"] != r_anti["accuracy"], "evaluate_classifier 必须依赖 state"
    assert abs(r_perf["accuracy"] - 1.0) < TOL
    assert abs(r_anti["accuracy"] - 0.0) < TOL

def test_ec_raises_on_missing_state():
    d = load_mnist_subset()
    X_tr, X_te, y_tr, y_te = preprocess_and_split(d)
    with pytest.raises(ValueError):
        evaluate_classifier({"W": []}, X_te, y_te)

def test_ec_raises_on_empty():
    with pytest.raises(ValueError):
        evaluate_classifier({"W": [[0]*10]*64, "b": [0]*10}, [], [])

def test_ec_raises_on_non_dict_state():
    with pytest.raises(TypeError):
        evaluate_classifier("not dict", [], [])
