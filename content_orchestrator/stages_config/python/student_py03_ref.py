def factorial(n):
    """Return n! for a non-negative integer n."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    result = 1
    for value in range(2, n + 1):
        result *= value
    return result
