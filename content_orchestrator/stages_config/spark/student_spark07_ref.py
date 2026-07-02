def run_streaming_operation(batches, operation, param=None):
    """Run a Spark Streaming-style operation on micro-batches."""
    if not isinstance(batches, list):
        raise TypeError("batches must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "init_status":
        return "stream processing initiated" if param else "stream processing stopped"
    if operation == "window_count":
        size = param
        return sum(len(batch) for batch in batches[-size:])
    if operation == "stateful_count_by_key":
        counts = {}
        for batch in batches:
            for key in batch:
                counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))
    if operation == "transform_non_empty_count":
        return sum(1 for batch in batches for item in batch if item)
    if operation == "checkpoint_status":
        return {"checkpoint": bool(param), "batches": len(batches)}
    if operation == "foreach_batch_sizes":
        return [len(batch) for batch in batches]
    if operation == "batch_count":
        return len(batches)
    if operation == "latest_batch_count":
        return len(batches[-1]) if batches else 0
    if operation == "flat_events":
        return [item for batch in batches for item in batch]
    if operation == "filter_keyword_count":
        return sum(1 for batch in batches for item in batch if param in item)
    if operation == "running_total":
        total = 0
        result = []
        for batch in batches:
            total += sum(batch)
            result.append(total)
        return result
    return {"error": "unsupported_operation"}
