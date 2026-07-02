def count_words(text):
    """Return word frequency counts sorted by word."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    words = text.split()
    return {word: words.count(word) for word in sorted(set(words))}
