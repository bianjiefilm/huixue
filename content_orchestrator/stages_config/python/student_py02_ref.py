def sum_to_n(n):
    """Return 1 + 2 + ... + n for a positive integer n."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 1:
        raise ValueError("n must be positive")
    return n * (n + 1) // 2
