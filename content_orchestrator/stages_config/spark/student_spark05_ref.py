def run_sql_query(rows, operation, param=None):
    """Run a Spark SQL-style query on Python row dictionaries."""
    if not isinstance(rows, list):
        raise TypeError("rows must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "department_salary_sum_first":
        totals = {}
        for row in rows:
            totals[row["department"]] = totals.get(row["department"], 0) + row.get("salary", 0)
        return list(list(sorted(totals.items()))[0]) if totals else []
    if operation == "uppercase_names":
        return [row["name"].upper() for row in rows]
    if operation == "order_by_salary_desc_names":
        return [row["name"] for row in sorted(rows, key=lambda row: row.get("salary", 0), reverse=True)]
    if operation == "filter_department_salary_count":
        department, minimum = param
        return sum(1 for row in rows if row.get("department") == department and row.get("salary", 0) > minimum)
    if operation == "fill_missing_salary":
        return [{**row, "salary": row.get("salary") or 0} for row in rows]
    if operation == "avg_salary_by_department":
        department = param
        salaries = [row["salary"] for row in rows if row.get("department") == department and row.get("salary") is not None]
        return round(sum(salaries) / len(salaries), 2) if salaries else 0
    if operation == "select_names_by_department":
        return [row["name"] for row in rows if row.get("department") == param]
    if operation == "top_salary":
        return max((row.get("salary") or 0 for row in rows), default=0)
    if operation == "count_null_salary":
        return sum(1 for row in rows if row.get("salary") is None)
    if operation == "project_name_salary":
        return [{"name": row["name"], "salary": row.get("salary") or 0} for row in rows]
    return {"error": "unsupported_operation"}
