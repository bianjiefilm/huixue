import re


def check_data_quality(data, check_type):
    """Run a data quality check or cleanup action."""
    if not isinstance(check_type, str):
        raise TypeError("check_type must be a string")

    if check_type == "deduplicate":
        if not isinstance(data, list):
            raise TypeError("data must be a list")
        seen = set()
        result = []
        for row in data:
            row_id = row.get("id")
            if row_id in seen:
                continue
            seen.add(row_id)
            result.append(row)
        return result

    if check_type == "fill_missing":
        if not isinstance(data, list):
            raise TypeError("data must be a list")
        return [{key: ("" if value is None else value) for key, value in row.items()} for row in data]

    if check_type == "report":
        if not isinstance(data, list):
            raise TypeError("data must be a list")
        ids = [row.get("id") for row in data]
        duplicate_ids = sorted({row_id for row_id in ids if row_id is not None and ids.count(row_id) > 1})
        missing_fields = sorted({key for row in data for key, value in row.items() if value is None})
        return {"total": len(data), "duplicate_ids": duplicate_ids, "missing_fields": missing_fields}

    if check_type == "phone":
        if not isinstance(data, str):
            raise TypeError("phone must be a string")
        return bool(re.fullmatch(r"1[3-9]\d{9}", data))

    if check_type == "age":
        if not isinstance(data, int):
            raise TypeError("age must be an integer")
        return {"valid": 0 <= data <= 120, "reason": "" if 0 <= data <= 120 else "out_of_range"}

    if check_type == "email":
        if not isinstance(data, str):
            raise TypeError("email must be a string")
        return {"valid": bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", data)), "reason": "" if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", data) else "format_error"}

    return {"error": "unsupported_check"}
