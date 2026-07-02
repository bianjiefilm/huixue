def map_activity_to_phase(activity):
    if not isinstance(activity, str):
        raise TypeError("activity must be str")
    if not activity:
        return "未知"
    if any(k in activity for k in ("上线", "监控", "线上")):
        return "部署"
    if any(k in activity for k in ("业务", "目标", "成功标准")):
        return "业务理解"
    if any(k in activity for k in ("缺失", "填充", "特征", "编码")):
        return "数据准备"
    if any(k in activity for k in ("模型", "超参数", "随机森林")):
        return "建模"
    return "未知"


def classify_learning_type(has_labels, all_labeled):
    if not isinstance(has_labels, bool) or not isinstance(all_labeled, bool):
        raise TypeError("inputs must be bool")
    if not has_labels:
        return "unsupervised"
    return "supervised" if all_labeled else "semi-supervised"


def compute_accuracy(y_true, y_pred):
    if not y_true or not y_pred:
        raise ValueError("empty input")
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true)


def is_overfit(train_score, val_score, threshold=0.1):
    if not isinstance(train_score, (int, float)) or not isinstance(val_score, (int, float)):
        raise TypeError("scores must be numeric")
    gap = round(train_score - val_score, 10)
    return {"is_overfitting": gap > threshold, "gap": gap}
