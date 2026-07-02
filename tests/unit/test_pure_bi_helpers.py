"""
bi_helpers.py 纯函数单元测试

覆盖: SQL sanitization, SQL文件排序, CSV类型转换, 权限判断
"""
import pytest
from app.utils.bi_helpers import (
    sanitize_mysql_to_sqlite,
    classify_sql_files,
    classify_dataset_sql_files,
    convert_csv_value,
    clean_csv_row,
    check_role_access,
    can_view_grades,
)


# ==================== SQL Sanitization ====================

class TestSanitizeMySQLToSQLite:

    def test_removes_engine_clause(self):
        sql = "CREATE TABLE t (id INT) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
        result = sanitize_mysql_to_sqlite(sql)
        assert "ENGINE" not in result
        assert "CHARSET" not in result

    def test_removes_collate(self):
        sql = "name VARCHAR(100) COLLATE utf8mb4_unicode_ci"
        result = sanitize_mysql_to_sqlite(sql)
        assert "COLLATE" not in result
        assert "utf8mb4_unicode_ci" not in result

    def test_removes_collate_equals(self):
        sql = "CREATE TABLE t (id INT) COLLATE=utf8_general_ci;"
        result = sanitize_mysql_to_sqlite(sql)
        assert "COLLATE" not in result

    def test_removes_character_set(self):
        sql = "name VARCHAR(100) CHARACTER SET utf8mb4"
        result = sanitize_mysql_to_sqlite(sql)
        assert "CHARACTER SET" not in result

    def test_removes_single_quote_comment(self):
        sql = "name VARCHAR(100) COMMENT '用户名'"
        result = sanitize_mysql_to_sqlite(sql)
        assert "COMMENT" not in result
        assert "用户名" not in result

    def test_removes_double_quote_comment(self):
        sql = 'age INT COMMENT "年龄"'
        result = sanitize_mysql_to_sqlite(sql)
        assert "COMMENT" not in result
        assert "年龄" not in result

    def test_removes_lock_unlock(self):
        sql = "LOCK TABLES users WRITE;\nINSERT INTO users VALUES (1);\nUNLOCK TABLES;"
        result = sanitize_mysql_to_sqlite(sql)
        assert "LOCK TABLES" not in result
        assert "UNLOCK TABLES" not in result
        assert "INSERT INTO" in result

    def test_replaces_backticks(self):
        sql = "SELECT `id`, `name` FROM `users`"
        result = sanitize_mysql_to_sqlite(sql)
        assert '`' not in result
        assert '"id"' in result
        assert '"name"' in result
        assert '"users"' in result

    def test_preserves_data_content(self):
        sql = "INSERT INTO t VALUES (1, 'hello world', 3.14);"
        result = sanitize_mysql_to_sqlite(sql)
        assert "hello world" in result
        assert "3.14" in result

    def test_handles_empty_string(self):
        assert sanitize_mysql_to_sqlite("") == ""

    def test_complex_create_table(self):
        sql = """CREATE TABLE `sales` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `amount` DECIMAL(10,2) COMMENT '销售额',
  `region` VARCHAR(50) CHARACTER SET utf8 COLLATE utf8_general_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""
        result = sanitize_mysql_to_sqlite(sql)
        assert "ENGINE" not in result
        assert "COMMENT" not in result
        assert "CHARACTER SET" not in result
        assert '"sales"' in result
        assert '"id"' in result

    def test_case_insensitive(self):
        sql = "engine=innodb; default charset=UTF8; collate=UTF8_BIN;"
        result = sanitize_mysql_to_sqlite(sql)
        assert "engine" not in result.lower() or result.strip() == ";"


# ==================== SQL File Sorting ====================

class TestClassifySQLFiles:

    def test_schema_first_insert_last(self):
        files = ["insert_data.sql", "create_table.sql", "query.sql"]
        schema, other, insert = classify_sql_files(files)
        assert schema == ["create_table.sql"]
        assert other == ["query.sql"]
        assert insert == ["insert_data.sql"]

    def test_execution_order(self):
        files = ["insert_rows.sql", "schema_v2.sql", "create_users.sql", "analytics.sql"]
        schema, other, insert = classify_sql_files(files)
        ordered = schema + other + insert
        assert ordered == ["create_users.sql", "schema_v2.sql", "analytics.sql", "insert_rows.sql"]

    def test_empty_list(self):
        schema, other, insert = classify_sql_files([])
        assert schema == other == insert == []

    def test_all_schema(self):
        files = ["create_a.sql", "schema_b.sql"]
        schema, other, insert = classify_sql_files(files)
        assert len(schema) == 2
        assert len(other) == 0
        assert len(insert) == 0

    def test_alphabetical_within_groups(self):
        files = ["insert_b.sql", "insert_a.sql", "create_b.sql", "create_a.sql"]
        schema, other, insert = classify_sql_files(files)
        assert schema == ["create_a.sql", "create_b.sql"]
        assert insert == ["insert_a.sql", "insert_b.sql"]


class TestClassifyDatasetSQLFiles:

    def test_data_keyword_in_schema(self):
        """datasets目录中 'data' 关键字文件归入schema"""
        files = ["retail_data.sql", "insert_products.sql", "utils.sql"]
        schema, other, insert = classify_dataset_sql_files(files)
        assert "retail_data.sql" in schema
        assert "insert_products.sql" in insert
        assert "utils.sql" in other

    def test_data_insert_excluded_from_schema(self):
        """'data_insert' 应归入 insert，不是 schema"""
        files = ["data_insert.sql"]
        schema, other, insert = classify_dataset_sql_files(files)
        assert "data_insert.sql" in insert
        assert schema == []

    def test_mixed(self):
        files = ["create_tables.sql", "sales_data.sql", "insert_records.sql", "views.sql"]
        schema, other, insert = classify_dataset_sql_files(files)
        ordered = schema + other + insert
        assert ordered[0] == "create_tables.sql"  # schema first
        assert ordered[-1] == "insert_records.sql"  # insert last


# ==================== CSV Value Conversion ====================

class TestConvertCSVValue:

    def test_integer(self):
        assert convert_csv_value("42") == 42

    def test_float(self):
        assert convert_csv_value("3.14") == pytest.approx(3.14)

    def test_string(self):
        assert convert_csv_value("hello") == "hello"

    def test_empty_string(self):
        assert convert_csv_value("") == ""

    def test_none(self):
        assert convert_csv_value(None) is None

    def test_numeric_string_with_leading_zero(self):
        # "007" should be int 7
        assert convert_csv_value("007") == 7

    def test_negative_int(self):
        assert convert_csv_value("-5") == -5

    def test_negative_float(self):
        assert convert_csv_value("-2.5") == pytest.approx(-2.5)

    def test_non_numeric_with_dot(self):
        """含点但不是数字的字符串"""
        assert convert_csv_value("v1.2.3") == "v1.2.3"

    def test_chinese_text(self):
        assert convert_csv_value("北京市") == "北京市"


class TestCleanCSVRow:

    def test_basic_cleaning(self):
        row = {" name ": "Alice", " age ": "30"}
        result = clean_csv_row(row)
        assert result == {"name": "Alice", "age": 30}

    def test_none_key(self):
        row = {None: "value1", "col2": "value2"}
        result = clean_csv_row(row)
        assert "column_0" in result

    def test_empty_values(self):
        row = {"a": "", "b": None}
        result = clean_csv_row(row)
        assert result["a"] == ""
        assert result["b"] is None

    def test_mixed_types(self):
        row = {"id": "1", "price": "9.99", "name": "Widget"}
        result = clean_csv_row(row)
        assert result == {"id": 1, "price": pytest.approx(9.99), "name": "Widget"}


# ==================== Permission Helpers ====================

class TestCheckRoleAccess:

    def test_admin_in_allowed(self):
        assert check_role_access("admin", ["admin", "teacher"]) is True

    def test_student_not_in_allowed(self):
        assert check_role_access("student", ["admin", "teacher"]) is False

    def test_empty_allowed(self):
        assert check_role_access("admin", []) is False


class TestCanViewGrades:

    def test_admin_always_allowed(self):
        assert can_view_grades("admin", 1) is True

    def test_admin_with_target(self):
        assert can_view_grades("admin", 1, target_student_id=999) is True

    def test_student_own_grades_needs_db(self):
        """学生查自己成绩需要 DB 验证是否在班级中"""
        assert can_view_grades("student", 10, target_student_id=10) is None

    def test_student_other_grades_denied(self):
        """学生不能看其他人成绩"""
        assert can_view_grades("student", 10, target_student_id=20) is False

    def test_student_no_target_needs_db(self):
        assert can_view_grades("student", 10) is None

    def test_teacher_needs_db(self):
        assert can_view_grades("teacher", 5) is None

    def test_unknown_role_denied(self):
        assert can_view_grades("guest", 1) is False

    def test_empty_role_denied(self):
        assert can_view_grades("", 1) is False
