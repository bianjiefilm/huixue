def merge_records(base, updates):
    """Merge two key-value dictionaries with updates taking priority."""
    if not isinstance(base, dict) or not isinstance(updates, dict):
        raise TypeError("base and updates must be dictionaries")
    if any(not isinstance(key, str) or not isinstance(value, int) for key, value in base.items()):
        raise TypeError("base must map strings to integers")
    if any(not isinstance(key, str) or not isinstance(value, int) for key, value in updates.items()):
        raise TypeError("updates must map strings to integers")
    merged = {**base, **updates}
    return {key: merged[key] for key in sorted(merged)}
