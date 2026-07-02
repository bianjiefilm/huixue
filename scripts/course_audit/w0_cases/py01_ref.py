def sum_to_n(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be int")
    if n <= 0:
        raise ValueError("n must be positive")
    return n * (n + 1) // 2
