def evaluate_fault_predictions(y_true, y_score, threshold=0.5):
    return {"y_true": y_true, "y_score": y_score, "threshold": threshold}
