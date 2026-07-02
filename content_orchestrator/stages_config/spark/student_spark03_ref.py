def run_transform_action(data, operation, param=None):
    """Run a Spark transformation/action style operation on Python data."""
    if not isinstance(data, list):
        raise TypeError("data must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "coalesce_partitions":
        if not isinstance(param, int) or param <= 0:
            raise ValueError("param must be a positive integer")
        return min(len(data), param)
    if operation == "reduce_by_key_count":
        totals = {}
        for key, value in data:
            totals[key] = totals.get(key, 0) + value
        return len(totals)
    if operation == "self_join_count":
        counts = {}
        for key, _ in data:
            counts[key] = counts.get(key, 0) + 1
        return sum(count * count for count in counts.values())
    if operation == "sort_desc_first":
        return sorted(data, reverse=True)[0] if data else None
    if operation == "union_distinct_count":
        other = param if isinstance(param, list) else []
        return len(set(data + other))
    if operation == "map_double_sum":
        return sum(item * 2 for item in data)
    if operation == "flatmap_triple_count":
        return len(data) * 3
    if operation == "collect_length":
        return len(data)
    if operation == "filter_gt_max":
        filtered = [item for item in data if item > param]
        return max(filtered) if filtered else None
    if operation == "cartesian_count":
        return len(data) * len(data)
    if operation == "filter_even_count":
        return sum(1 for item in data if item % 2 == 0)
    if operation == "take_top_n":
        return sorted(data, reverse=True)[:param]
    return {"error": "unsupported_operation"}
