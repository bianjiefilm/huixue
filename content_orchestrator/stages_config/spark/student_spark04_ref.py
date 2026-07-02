def run_shared_variable_operation(data, operation, shared=None):
    """Run an accumulator or broadcast-variable style operation."""
    if not isinstance(data, list):
        raise TypeError("data must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "broadcast_add_first":
        if not isinstance(shared, list):
            raise TypeError("shared must be a list")
        return data[0] + sum(shared) if data else None
    if operation == "accumulator_sum":
        return float(sum(data))
    if operation == "broadcast_lookup_first":
        if not isinstance(shared, dict):
            raise TypeError("shared must be a dict")
        key = data[0] if data else None
        return [key, shared.get(key, 0)]
    if operation == "accumulator_filter_sum_gt":
        return sum(item for item in data if item > shared)
    if operation == "broadcast_set_count":
        allowed = set(shared)
        return sum(1 for item in data if item in allowed)
    if operation == "accumulator_double_sum":
        return sum(item * 2 for item in data)
    if operation == "broadcast_add_sum":
        return sum(item + shared for item in data)
    if operation == "accumulator_count_lt":
        return sum(1 for item in data if item < shared)
    if operation == "accumulator_half_sum":
        return sum(item * 0.5 for item in data)
    return {"error": "unsupported_operation"}
