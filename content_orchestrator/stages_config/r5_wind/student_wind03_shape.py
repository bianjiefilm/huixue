def evaluate_fault_predictions(y_true, y_score, threshold=0.5):
    return {
        "threshold": threshold,
        "total": len(y_true) if isinstance(y_true, list) else 0,
        "predicted_alerts": 0,
        "actual_faults": 0,
        "confusion_matrix": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "false_alarm_rate": 0.0,
        "missed_alarm_rate": 0.0,
        "accuracy": 0.0,
    }
