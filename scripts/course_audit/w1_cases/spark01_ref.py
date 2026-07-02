def parallelize_sum(values):
    if not isinstance(values, list):
        raise TypeError("values must be a list")
    total = 0
    for value in values:
        if not isinstance(value, (int, float)):
            raise TypeError("all values must be numeric")
        total += value
    return total
