def _validate_inputs(y_true, y_score, threshold):
    if not isinstance(y_true, list) or not isinstance(y_score, list):
        raise ValueError("y_true and y_score must be lists")
    if len(y_true) != len(y_score):
        raise ValueError("y_true and y_score must have the same length")
    if not y_true:
        raise ValueError("y_true must not be empty")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be numeric")
    if threshold < 0 or threshold > 1:
        raise ValueError("threshold must be between 0 and 1")


def _round(value):
    return round(value, 4)


def evaluate_fault_predictions(y_true, y_score, threshold=0.5):
    """返回故障预警分类指标。"""
    _validate_inputs(y_true, y_score, threshold)

    labels = []
    scores = []
    for label, score in zip(y_true, y_score):
        if label not in (0, 1):
            raise ValueError("labels must be 0 or 1")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("scores must be numeric")
        if score < 0 or score > 1:
            raise ValueError("scores must be between 0 and 1")
        labels.append(int(label))
        scores.append(float(score))

    predictions = [1 if score >= threshold else 0 for score in scores]
    tp = sum(1 for y, p in zip(labels, predictions) if y == 1 and p == 1)
    fp = sum(1 for y, p in zip(labels, predictions) if y == 0 and p == 1)
    tn = sum(1 for y, p in zip(labels, predictions) if y == 0 and p == 0)
    fn = sum(1 for y, p in zip(labels, predictions) if y == 1 and p == 0)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    false_alarm_rate = fp / (fp + tn) if fp + tn else 0.0
    missed_alarm_rate = fn / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / len(labels)

    return {
        "threshold": _round(float(threshold)),
        "total": len(labels),
        "predicted_alerts": sum(predictions),
        "actual_faults": sum(labels),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": _round(precision),
        "recall": _round(recall),
        "f1": _round(f1),
        "false_alarm_rate": _round(false_alarm_rate),
        "missed_alarm_rate": _round(missed_alarm_rate),
        "accuracy": _round(accuracy),
    }
