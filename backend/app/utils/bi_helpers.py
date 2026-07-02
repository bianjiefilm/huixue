"""
BI数据加载纯函数

从 bi_data_loader.py 提取的无副作用函数，
覆盖 SQL sanitization、文件排序、CSV 类型转换等关键逻辑。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─── SQL Sanitization ───────────────────────────────────────────────

def sanitize_mysql_to_sqlite(content: str) -> str:
    """
    将 MySQL SQL 脚本转换为 SQLite 兼容格式。

    处理:
    - ENGINE/CHARSET/COLLATE 子句
    - COMMENT 注释
    - LOCK/UNLOCK TABLES
    - 反引号 → 双引号
    """
    # Remove MySQL engine/charset clauses
    content = re.sub(r'ENGINE=InnoDB.*?;', ';', content, flags=re.IGNORECASE)
    content = re.sub(r'DEFAULT CHARSET=.*?;', ';', content, flags=re.IGNORECASE)
    content = re.sub(r'CHARACTER SET\s+[\w_]+', '', content, flags=re.IGNORECASE)
    content = re.sub(r'COLLATE=.*?;', ';', content, flags=re.IGNORECASE)
    content = re.sub(r'COLLATE\s+[\w_]+', '', content, flags=re.IGNORECASE)

    # Remove COMMENT clauses
    content = re.sub(r"COMMENT\s+'[^']*'", "", content, flags=re.IGNORECASE)
    content = re.sub(r'COMMENT\s+"[^"]*"', "", content, flags=re.IGNORECASE)

    # Remove LOCK/UNLOCK
    content = re.sub(r'LOCK TABLES.*?;', '', content, flags=re.IGNORECASE)
    content = re.sub(r'UNLOCK TABLES;', '', content, flags=re.IGNORECASE)

    # Backticks → double quotes
    content = content.replace('`', '"')

    return content


# ─── SQL File Sorting ────────────────────────────────────────────────

def classify_sql_files(
    filenames: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """
    将 SQL 文件名分为 schema、insert、other 三组，按字母序排列。

    Returns:
        (schema_files, other_files, insert_files)
        合并后即为正确的执行顺序。
    """
    schema = []
    insert = []
    other = []

    for name in filenames:
        lower = name.lower()
        if "create" in lower or "schema" in lower:
            schema.append(name)
        elif "insert" in lower:
            insert.append(name)
        else:
            other.append(name)

    schema.sort()
    other.sort()
    insert.sort()

    return schema, other, insert


def classify_dataset_sql_files(
    filenames: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """
    datasets 目录下的 SQL 文件分类。
    与 classify_sql_files 区别: "data" 关键字(不含 insert)归入 schema。
    """
    schema = []
    insert = []
    other = []

    for name in filenames:
        lower = name.lower()
        if "create" in lower or "schema" in lower or ("data" in lower and "insert" not in lower):
            schema.append(name)
        elif "insert" in lower:
            insert.append(name)
        else:
            other.append(name)

    schema.sort()
    other.sort()
    insert.sort()

    return schema, other, insert


# ─── CSV Value Conversion ────────────────────────────────────────────

def convert_csv_value(value: Optional[str]) -> Any:
    """
    将 CSV 字符串值转换为合适的 Python 类型。
    空值/None 保持原样。
    """
    if not value:
        return value
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def clean_csv_row(row: Dict[str, Optional[str]], column_count: int = 0) -> Dict[str, Any]:
    """
    清理 CSV 行：修剪键名、转换值类型。
    """
    cleaned = {}
    for key, value in row.items():
        clean_key = key.strip() if key else f"column_{len(cleaned)}"
        cleaned[clean_key] = convert_csv_value(value)
    return cleaned


# ─── Permission Helpers ──────────────────────────────────────────────

def check_role_access(user_role: str, allowed_roles: List[str]) -> bool:
    """检查用户角色是否在允许列表中。"""
    return user_role in allowed_roles


def can_view_grades(
    user_role: str,
    user_id: int,
    target_student_id: Optional[int] = None,
) -> Optional[bool]:
    """
    纯角色层面的成绩查看权限判断。

    Returns:
        True  = 无条件允许 (admin)
        False = 无条件拒绝 (student 看他人)
        None  = 需要进一步 DB 查询 (teacher/student 本人)
    """
    if user_role == "admin":
        return True

    if user_role == "student":
        if target_student_id and target_student_id != user_id:
            return False
        return None  # 需要查 DB 确认是否在班级中

    if user_role == "teacher":
        return None  # 需要查 DB 确认是否拥有该班级

    return False  # 未知角色
