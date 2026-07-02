def run_dataframe_operation(rows, operation, extra=None):
    """Run an advanced DataFrame-style operation on Python row dictionaries."""
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "broadcast_join_count":
        right_ids = {row["id"] for row in extra}
        return sum(1 for row in rows if row.get("id") in right_ids)
    if operation == "count_by_year_first":
        counts = {}
        for row in rows:
            year = str(row["date"])[:4]
            counts[year] = counts.get(year, 0) + 1
        return list(list(sorted(counts.items()))[0]) if counts else []
    if operation == "regexp_replace_first":
        return rows[0]["text"].replace(extra[0], extra[1]) if rows else ""
    if operation == "explode_name_count":
        return sum(len(row["name"].split(extra)) for row in rows)
    if operation == "partition_write_summary":
        return sorted({str(row["date"])[:4] for row in rows})
    if operation == "window_rank":
        ordered = sorted(rows, key=lambda row: row["score"], reverse=True)
        return [{"name": row["name"], "rank": index + 1} for index, row in enumerate(ordered)]
    if operation == "drop_duplicates_count":
        return len({row[extra] for row in rows})
    if operation == "pivot_sum":
        totals = {}
        for row in rows:
            totals[row["category"]] = totals.get(row["category"], 0) + row["amount"]
        return dict(sorted(totals.items()))
    if operation == "nested_field_select":
        return [row["profile"][extra] for row in rows]
    if operation == "null_safe_join_count":
        right_ids = {row.get("id") for row in extra}
        return sum(1 for row in rows if row.get("id") is not None and row.get("id") in right_ids)
    return {"error": "unsupported_operation"}
