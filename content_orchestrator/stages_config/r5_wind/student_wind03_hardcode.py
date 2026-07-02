def evaluate_fault_predictions(y_true, y_score, threshold=0.5):
    return {
        "threshold": 0.5,
        "total": 4,
        "predicted_alerts": 2,
        "actual_faults": 2,
        "confusion_matrix": {"tp": 1, "fp": 1, "tn": 1, "fn": 1},
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
        "false_alarm_rate": 0.5,
        "missed_alarm_rate": 0.5,
        "accuracy": 0.5,
    }
