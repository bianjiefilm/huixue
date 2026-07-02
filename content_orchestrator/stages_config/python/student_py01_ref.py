def add_numbers(a, b):
    """Return the sum of two numeric values."""
    if isinstance(a, bool) or isinstance(b, bool):
        raise TypeError("boolean values are not supported")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("a and b must be numbers")
    return a + b
