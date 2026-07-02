def parallelize_sum(values):
    """Return the sum of values in a Spark-like parallelized collection."""
    if values is None:
        raise TypeError("values must be an iterable of numbers")
    if isinstance(values, dict) or isinstance(values, str):
        raise TypeError("values must be an iterable of numbers")
    total = 0
    for value in values:
        if not isinstance(value, (int, float)):
            raise TypeError("all values must be numeric")
        total += value
    return total
