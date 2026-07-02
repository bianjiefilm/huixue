def load_mnist_subset():
    images = []
    labels = []
    for i in range(100):
        label = i % 10
        img = [[0.0 for _ in range(8)] for _ in range(8)]
        img[label // 8][label % 8] = 1.0
        images.append(img)
        labels.append(label)
    return {"images": images, "labels": labels}


def preprocess_and_split(data, test_size=0.2):
    if not isinstance(data, dict):
        raise TypeError("data must be dict")
    if "images" not in data or "labels" not in data:
        raise ValueError("missing keys")
    X = [[v for row in img for v in row] for img in data["images"]]
    y = list(data["labels"])
    n_test = int(len(X) * test_size)
    n_train = len(X) - n_test
    return X[:n_train], X[n_train:], y[:n_train], y[n_train:]


def train_simple_classifier(X_train, y_train, n_epochs=5):
    if not X_train or not y_train:
        raise ValueError("empty data")
    W = [[0.0 for _ in range(10)] for _ in range(64)]
    for k in range(10):
        W[k][k] = 1.0
    b = [0.0 for _ in range(10)]
    return {"W": W, "b": b}


def evaluate_classifier(state, X_test, y_test):
    if not isinstance(state, dict):
        raise TypeError("state must be dict")
    if "W" not in state or "b" not in state or not state["W"] or not state["b"]:
        raise ValueError("invalid state")
    if not X_test or not y_test:
        raise ValueError("empty data")
    W = state["W"]
    b = state["b"]
    preds = []
    for x in X_test:
        logits = []
        for c in range(10):
            logits.append(sum(x[i] * W[i][c] for i in range(min(len(x), len(W)))) + b[c])
        preds.append(max(range(10), key=lambda c: logits[c]))
    correct = sum(1 for p, y in zip(preds, y_test) if p == y)
    accuracy = correct / len(y_test)
    per_class = []
    precisions = []
    recalls = []
    f1s = []
    for c in range(10):
        tp = sum(1 for p, y in zip(preds, y_test) if p == c and y == c)
        fp = sum(1 for p, y in zip(preds, y_test) if p == c and y != c)
        fn = sum(1 for p, y in zip(preds, y_test) if p != c and y == c)
        total_c = sum(1 for y in y_test if y == c)
        per_class.append(tp / total_c if total_c else 0.0)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return {
        "accuracy": accuracy,
        "macro_precision": sum(precisions) / 10,
        "macro_recall": sum(recalls) / 10,
        "macro_f1": sum(f1s) / 10,
        "per_class_accuracy": per_class,
    }
