def filter_even_numbers(numbers):
    """Return even integers from a list of numbers."""
    if not isinstance(numbers, list):
        raise TypeError("numbers must be a list")
    if any(not isinstance(value, int) or isinstance(value, bool) for value in numbers):
        raise TypeError("all items must be integers")
    return [value for value in numbers if value % 2 == 0]
