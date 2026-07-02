def run_rdd_operation(data, operation, threshold=0):
    """Run a Spark RDD-style operation on Python data."""
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")
    if not isinstance(data, list):
        raise TypeError("data must be a list")

    if operation == "word_count":
        counts = {}
        for item in data:
            counts[item] = counts.get(item, 0) + 1
        return dict(sorted(counts.items()))
    if operation == "filter_gt":
        return [item for item in data if item > threshold]
    if operation == "flat_chars":
        return [char for word in data for char in word]
    if operation == "collect_even_times10":
        return [item * 10 for item in data if item % 2 == 0]
    if operation == "group_count":
        counts = {}
        for item in data:
            counts[item] = counts.get(item, 0) + 1
        return dict(sorted(counts.items()))
    if operation == "distinct":
        result = []
        for item in data:
            if item not in result:
                result.append(item)
        return result
    return {"error": "unsupported_operation"}
