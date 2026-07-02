def run_mllib_operation(data, operation, param=None):
    """Run an MLlib-style operation on Python data structures."""
    if not isinstance(data, list):
        raise TypeError("data must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "train_status":
        return "model trained" if data else "no data"
    if operation == "kmeans_center_count":
        return param
    if operation == "string_indexer_labels":
        return sorted({row["label"] for row in data})
    if operation == "pipeline_stage_count":
        return len(param)
    if operation == "als_rank":
        return param.get("rank", 0)
    if operation == "vector_assemble_first":
        return [float(data[0][col]) for col in param]
    if operation == "minmax_scale":
        values = [row[param] for row in data]
        low, high = min(values), max(values)
        return [0 if high == low else round((value - low) / (high - low), 4) for value in values]
    if operation == "threshold_predict":
        return [1 if row[param["feature"]] >= param["threshold"] else 0 for row in data]
    if operation == "accuracy":
        return round(sum(1 for row in data if row["label"] == row["prediction"]) / len(data), 4) if data else 0
    if operation == "top_recommendation":
        user = param
        rows = [row for row in data if row["user"] == user]
        return max(rows, key=lambda row: row["score"])["item"] if rows else None
    if operation == "dot_similarity":
        left, right = data
        return sum(a * b for a, b in zip(left, right))
    return {"error": "unsupported_operation"}
