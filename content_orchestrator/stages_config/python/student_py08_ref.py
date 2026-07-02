def fahrenheit_to_celsius(fahrenheit):
    """Convert Fahrenheit temperature to Celsius."""
    if not isinstance(fahrenheit, (int, float)) or isinstance(fahrenheit, bool):
        raise TypeError("fahrenheit must be a number")
    return (fahrenheit - 32) * 5 / 9
