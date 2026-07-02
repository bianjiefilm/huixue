#!/usr/bin/env python3
"""
migrate_content_fields.py
一次性迁移脚本：从 SQLite 填充 PostgreSQL 的 courses.teaching_syllabus
和 trainings.handbook_content 字段。

使用方法（在 backend 容器内运行）：
    cd /app
    python migrate_content_fields.py

或本地运行（连接远程 PostgreSQL）：
    DATABASE_URL=postgresql://huixue:huixue123@<慧学内网IP-1>:5432/huixue \
    python migrate_content_fields.py
"""
import os
import sys

# ── 路径配置 ──────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(SCRIPT_DIR, "huixue_local.db")

# 从环境变量读取 PG URL，兼容容器内外
PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://huixue:huixue123@db:5432/huixue"
)

# ── 依赖检查 ──────────────────────────────────────────────────────────
try:
    import sqlite3
    import psycopg2
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install: pip install psycopg2-binary")
    sys.exit(1)


# ── 1. 从 SQLite 读取 syllabus ─────────────────────────────────────────
def read_sqlite_syllabi():
    print("\n=== Step 1: 从 SQLite 读取 courses.teaching_syllabus ===")
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, teaching_syllabus
        FROM courses
        WHERE teaching_syllabus IS NOT NULL
          AND length(teaching_syllabus) > 0
    """)
    rows = cur.fetchall()
    conn.close()
    data = {r["id"]: r["teaching_syllabus"] for r in rows}
    print(f"  ✓ 读取 {len(data)} 条 syllabus 记录")
    return data


# ── 2. 从 SQLite 读取 handbook ────────────────────────────────────────
def read_sqlite_handbooks():
    print("\n=== Step 2: 从 SQLite 读取 trainings.handbook_content ===")
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, handbook_content
        FROM trainings
        WHERE handbook_content IS NOT NULL
          AND length(handbook_content) > 0
    """)
    rows = cur.fetchall()
    conn.close()
    data = {r["id"]: r["handbook_content"] for r in rows}
    print(f"  ✓ 读取 {len(data)} 条 handbook 记录")
    return data


# ── 3. 检查 PostgreSQL 连接和列是否存在 ────────────────────────────────
def check_pg_schema(pg_conn):
    print("\n=== Step 3: 检查 PostgreSQL 表结构 ===")
    cur = pg_conn.cursor()

    # 检查 courses.teaching_syllabus 列
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'courses' AND column_name = 'teaching_syllabus'
    """)
    col = cur.fetchone()
    if col:
        print(f"  ✓ courses.teaching_syllabus 存在 (类型: {col[1]})")
    else:
        print("  ✗ courses.teaching_syllabus 列不存在，添加中...")
        cur.execute("ALTER TABLE courses ADD COLUMN teaching_syllabus TEXT")
        pg_conn.commit()
        print("  ✓ 已添加 courses.teaching_syllabus 列")

    # 检查 trainings.handbook_content 列
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'trainings' AND column_name = 'handbook_content'
    """)
    col = cur.fetchone()
    if col:
        print(f"  ✓ trainings.handbook_content 存在 (类型: {col[1]})")
    else:
        print("  ✗ trainings.handbook_content 列不存在，添加中...")
        cur.execute("ALTER TABLE trainings ADD COLUMN handbook_content TEXT")
        pg_conn.commit()
        print("  ✓ 已添加 trainings.handbook_content 列")

    # 当前数据统计
    cur.execute("SELECT COUNT(*) FROM courses WHERE teaching_syllabus IS NOT NULL AND length(teaching_syllabus) > 0")
    print(f"  → PostgreSQL courses 当前有 syllabus 的记录: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM trainings WHERE handbook_content IS NOT NULL AND length(handbook_content) > 0")
    print(f"  → PostgreSQL trainings 当前有 handbook 的记录: {cur.fetchone()[0]}")


# ── 4. 迁移 syllabus ─────────────────────────────────────────────────
def migrate_syllabi(pg_conn, syllabi):
    print(f"\n=== Step 4: 迁移 {len(syllabi)} 条 teaching_syllabus ===")
    cur = pg_conn.cursor()
    updated = 0
    for course_id, content in syllabi.items():
        cur.execute(
            """
            UPDATE courses
            SET teaching_syllabus = %s
            WHERE id = %s
              AND (teaching_syllabus IS NULL OR length(teaching_syllabus) = 0)
            """,
            (content, course_id)
        )
        if cur.rowcount > 0:
            updated += 1
            print(f"  ✓ course {course_id}: syllabus 已更新")
    pg_conn.commit()
    print(f"  → 共更新 {updated} 条 syllabus 记录")


# ── 5. 迁移 handbook ─────────────────────────────────────────────────
def migrate_handbooks(pg_conn, handbooks):
    print(f"\n=== Step 5: 迁移 {len(handbooks)} 条 handbook_content ===")
    cur = pg_conn.cursor()
    updated = 0
    for training_id, content in handbooks.items():
        cur.execute(
            """
            UPDATE trainings
            SET handbook_content = %s
            WHERE id = %s
              AND (handbook_content IS NULL OR length(handbook_content) = 0)
            """,
            (content, training_id)
        )
        if cur.rowcount > 0:
            updated += 1
            print(f"  ✓ training {training_id}: handbook 已更新")
    pg_conn.commit()
    print(f"  → 共更新 {updated} 条 handbook 记录")


# ── 6. 验证结果 ─────────────────────────────────────────────────────
def verify_results(pg_conn):
    print("\n=== Step 6: 验证结果 ===")
    cur = pg_conn.cursor()

    cur.execute("SELECT COUNT(*) FROM courses WHERE teaching_syllabus IS NOT NULL AND length(teaching_syllabus) > 0")
    count = cur.fetchone()[0]
    print(f"  courses with syllabus: {count}")

    cur.execute("SELECT id, title FROM courses WHERE teaching_syllabus IS NOT NULL AND length(teaching_syllabus) > 0 ORDER BY id")
    rows = cur.fetchall()
    if rows:
        print(f"  课程列表: {[r[0] for r in rows]}")
    else:
        print("  ⚠ 没有 syllabus 数据，请检查迁移结果")

    cur.execute("SELECT COUNT(*) FROM trainings WHERE handbook_content IS NOT NULL AND length(handbook_content) > 0")
    count = cur.fetchone()[0]
    print(f"  trainings with handbook: {count}")

    cur.execute("SELECT id, title FROM trainings WHERE handbook_content IS NOT NULL AND length(handbook_content) > 0 ORDER BY id")
    rows = cur.fetchall()
    if rows:
        print(f"  实训列表: {[r[0] for r in rows]}")


# ── 主流程 ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("慧学平台 — syllabus & handbook 迁移脚本")
    print(f"SQLite: {SQLITE_PATH}")
    print(f"PostgreSQL: {PG_URL}")
    print("=" * 60)

    # 读取 SQLite 数据
    syllabi = read_sqlite_syllabi()
    handbooks = read_sqlite_handbooks()

    if not syllabi and not handbooks:
        print("\n[ERROR] SQLite 中没有找到任何 syllabus 或 handbook 数据")
        sys.exit(1)

    # 连接 PostgreSQL
    print(f"\n连接 PostgreSQL: {PG_URL.split('@')[1] if '@' in PG_URL else PG_URL}")
    try:
        pg_conn = psycopg2.connect(PG_URL, connect_timeout=10)
        print("  ✓ PostgreSQL 连接成功")
    except Exception as e:
        print(f"\n[ERROR] 无法连接 PostgreSQL: {e}")
        print("\n请确认：")
        print("  1. Docker 容器正在运行（docker-compose up -d）")
        print("  2. 在容器内运行：docker exec huixue-backend python migrate_content_fields.py")
        sys.exit(1)

    try:
        check_pg_schema(pg_conn)
        migrate_syllabi(pg_conn, syllabi)
        migrate_handbooks(pg_conn, handbooks)
        verify_results(pg_conn)
        print("\n" + "=" * 60)
        print("✓ 迁移完成！请刷新浏览器验证课程大纲和实训手册页面。")
        print("=" * 60)
    finally:
        pg_conn.close()


if __name__ == "__main__":
    main()
