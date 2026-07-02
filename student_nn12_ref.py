"""NN12 ref — 手写数字识别. 纯 Python (无 sklearn / numpy)."""
from typing import Dict, List, Tuple
import random
import math


CLASS_COUNTS = [5, 8, 10, 12, 15, 8, 10, 12, 10, 10]  # 100 总样本


def load_mnist_subset():
    rng = random.Random(42)
    images = []
    labels = []
    for cls, n in enumerate(CLASS_COUNTS):
        for _ in range(n):
            # 每类随机 8x8 图像 + 类别相关偏置 (cls / 9 * 16 加成中心)
            img = [[rng.uniform(0, 16) for _ in range(8)] for _ in range(8)]
            # 加类别 bias 让类别可分
            for i in range(8):
                for j in range(8):
                    img[i][j] = max(0, min(16, img[i][j] + (cls - 4) * 0.5))
            images.append(img)
            labels.append(cls)
    return {"images": images, "labels": labels}


def preprocess_and_split(data, test_size=0.2, random_state=42):
    if not isinstance(data, dict):
        raise TypeError("data must be dict")
    if "images" not in data or "labels" not in data:
        raise ValueError("data missing images/labels")

    images = data["images"]
    labels = data["labels"]
    n = len(images)

    # 扁平化 8x8 → 64
    flat = [[v for row in img for v in row] for img in images]

    rng = random.Random(random_state)
    indices = list(range(n))
    rng.shuffle(indices)
    n_test = int(n * test_size)
    test_idx = set(indices[:n_test])

    X_train, X_test, y_train, y_test = [], [], [], []
    train_features = []
    for i in range(n):
        if i not in test_idx:
            train_features.append(flat[i])

    # z-score 用 train 统计量
    n_features = len(flat[0]) if flat else 64
    means = []
    stds = []
    for j in range(n_features):
        col = [row[j] for row in train_features]
        m = sum(col) / len(col) if col else 0
        v = sum((x - m) ** 2 for x in col) / len(col) if col else 0
        means.append(m)
        stds.append(math.sqrt(v) if v > 0 else 1.0)

    for i in range(n):
        feat = [(flat[i][j] - means[j]) / stds[j] for j in range(n_features)]
        if i in test_idx:
            X_test.append(feat)
            y_test.append(int(labels[i]))
        else:
            X_train.append(feat)
            y_train.append(int(labels[i]))
    return X_train, X_test, y_train, y_test


def _softmax(logits):
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [e / s for e in exps]


def train_simple_classifier(X_train, y_train, n_epochs=20, lr=0.1):
    if not isinstance(X_train, list) or not isinstance(y_train, list):
        raise TypeError("X_train / y_train must be list")
    if len(X_train) != len(y_train):
        raise ValueError("length mismatch")
    if not X_train:
        raise ValueError("empty input")
    n = len(X_train)
    n_features = len(X_train[0])
    n_classes = max(y_train) + 1

    W = [[0.0] * n_classes for _ in range(n_features)]
    b = [0.0] * n_classes

    rng = random.Random(0)
    for epoch in range(n_epochs):
        order = list(range(n))
        rng.shuffle(order)
        for idx in order:
            x = X_train[idx]
            y = y_train[idx]
            logits = [sum(x[j] * W[j][k] for j in range(n_features)) + b[k] for k in range(n_classes)]
            probs = _softmax(logits)
            for k in range(n_classes):
                grad = probs[k] - (1.0 if k == y else 0.0)
                for j in range(n_features):
                    W[j][k] -= lr * grad * x[j]
                b[k] -= lr * grad
    return {"W": W, "b": b}


def evaluate_classifier(state, X_test, y_test):
    if not isinstance(state, dict):
        raise TypeError("state must be dict")
    if "W" not in state or "b" not in state:
        raise ValueError("state missing W/b")
    if not isinstance(X_test, list) or not isinstance(y_test, list):
        raise TypeError("X_test / y_test must be list")
    if len(X_test) != len(y_test):
        raise ValueError("length mismatch")
    if not X_test:
        raise ValueError("empty input")

    W = state["W"]
    b = state["b"]
    n_features = len(W)
    n_classes = len(b)

    preds = []
    for x in X_test:
        logits = [sum(x[j] * W[j][k] for j in range(n_features)) + b[k] for k in range(n_classes)]
        preds.append(logits.index(max(logits)))

    correct = sum(1 for p, y in zip(preds, y_test) if p == y)
    accuracy = correct / len(y_test)

    # per-class metrics
    per_class_acc = []
    precisions = []
    recalls = []
    f1s = []
    for c in range(n_classes):
        tp = sum(1 for p, y in zip(preds, y_test) if p == c and y == c)
        fp = sum(1 for p, y in zip(preds, y_test) if p == c and y != c)
        fn = sum(1 for p, y in zip(preds, y_test) if p != c and y == c)
        tn = sum(1 for p, y in zip(preds, y_test) if p != c and y != c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        # per_class_accuracy: TP+TN / total
        per_class_acc.append((tp + tn) / len(y_test))

    return {
        "accuracy": accuracy,
        "macro_precision": sum(precisions) / n_classes,
        "macro_recall": sum(recalls) / n_classes,
        "macro_f1": sum(f1s) / n_classes,
        "per_class_accuracy": per_class_acc,
    }
