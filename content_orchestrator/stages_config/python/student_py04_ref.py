def count_letters(text):
    """Return lowercase letter frequencies for the given text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    counts = {}
    for char in text.lower():
        if char.isalpha():
            counts[char] = counts.get(char, 0) + 1
    return counts
