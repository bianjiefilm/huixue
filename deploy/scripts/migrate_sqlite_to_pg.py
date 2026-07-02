#!/usr/bin/env python3
"""
慧学平台 — SQLite → PostgreSQL 迁移脚本 (v2)

修复: boolean 类型转换 + FK 约束处理 + 插入顺序
"""
import os
import sys
import sqlite3

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, BACKEND_DIR)

SQLITE_PATH = os.path.join(BACKEND_DIR, 'huixue_local.db')
PG_URL = os.environ.get('DATABASE_URL', 'postgresql://huixue:huixue123@192.168.109.42:5432/huixue')

# Tables with production data to preserve (don't overwrite)
PRESERVE_TABLES = {'api_users', 'user_profiles', 'schools', 'organizations'}


def get_pg_engine():
    from sqlalchemy import create_engine
    return create_engine(PG_URL, echo=False)


def step1_create_schema(pg_engine):
    print("\n=== Step 1: 确保 PostgreSQL 表结构 ===")
    from app.models.models import Base
    Base.metadata.create_all(bind=pg_engine)
    from sqlalchemy import inspect
    tables = inspect(pg_engine).get_table_names()
    print(f"  ✓ {len(tables)} 张表")
    return tables


def get_boolean_columns(pg_cur, table):
    """获取 PostgreSQL 表中的 boolean 列"""
    pg_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        AND data_type = 'boolean'
    """, (table,))
    return {r[0] for r in pg_cur.fetchall()}


def step2_migrate_data(pg_engine, pg_tables):
    print("\n=== Step 2: 迁移数据 ===")

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    sqlite_tables = [r[0] for r in sqlite_cur.fetchall()]

    pg_conn = pg_engine.raw_connection()
    pg_cur = pg_conn.cursor()

    # Disable FK constraints for the migration
    pg_cur.execute("SET session_replication_role = 'replica'")
    pg_conn.commit()

    migrated = 0
    skipped = 0
    errors = []

    for table in sorted(sqlite_tables):
        if table not in pg_tables:
            skipped += 1
            continue

        # Preserve production tables
        if table in PRESERVE_TABLES:
            pg_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            pg_count = pg_cur.fetchone()[0]
            if pg_count > 0:
                print(f"  🔒 {table}: 保留 ({pg_count} 行)")
                skipped += 1
                continue

        sqlite_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = sqlite_cur.fetchone()[0]
        if count == 0:
            continue

        sqlite_cur.execute(f'SELECT * FROM "{table}"')
        rows = sqlite_cur.fetchall()
        if not rows:
            continue

        columns = [desc[0] for desc in sqlite_cur.description]

        # Get PG column info
        pg_cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
        """, (table,))
        pg_columns = {r[0] for r in pg_cur.fetchall()}

        bool_cols = get_boolean_columns(pg_cur, table)

        valid_cols = [c for c in columns if c in pg_columns]
        if not valid_cols:
            skipped += 1
            continue

        col_indices = [columns.index(c) for c in valid_cols]
        bool_positions = {i for i, c in enumerate(valid_cols) if c in bool_cols}

        # Clear table — use DELETE (not TRUNCATE CASCADE) to avoid accidentally
        # deleting rows from parent tables when child FK has ON DELETE CASCADE.
        # CASCADE here means "if we truncates a child, also delete rows in this table
        # that the child references" — but for a table with no FK from children,
        # CASCADE is a no-op. The risk: a table X has FK from Y with CASCADE.
        # TRUNCATE X CASCADE first deletes Y.rows (if Y's FK has CASCADE to X),
        # then deletes X.rows. We INSERT X rows after, but Y is now empty.
        # FIX: use DELETE + TRUNCATE separately.
        try:
            # Delete all rows (FK constraints are already disabled by session_replication_role)
            pg_cur.execute(f'DELETE FROM "{table}"')
            pg_conn.commit()
        except Exception:
            pg_conn.rollback()

        # Build INSERT
        placeholders = ', '.join(['%s'] * len(valid_cols))
        col_names = ', '.join([f'"{c}"' for c in valid_cols])
        insert_sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})'

        batch_size = 500
        inserted = 0
        try:
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                values = []
                for row in batch:
                    row_values = []
                    for idx_in_valid, idx_in_orig in enumerate(col_indices):
                        val = row[idx_in_orig]
                        # Convert SQLite integer 0/1 to Python bool for PG boolean columns
                        if idx_in_valid in bool_positions and isinstance(val, int):
                            val = bool(val)
                        row_values.append(val)
                    values.append(tuple(row_values))

                pg_cur.executemany(insert_sql, values)
                inserted += len(batch)

            pg_conn.commit()
            # Verify rows landed in PG immediately (catch uncommitted transactions)
            pg_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            verified = pg_cur.fetchone()[0]
            migrated += 1
            status = "✓" if verified == inserted else "⚠"
            print(f"  {status} {table}: {inserted} 行 → PG({verified})")

        except Exception as e:
            pg_conn.rollback()
            errors.append((table, str(e)[:120]))
            print(f"  ✗ {table}: {str(e)[:100]}")

    # Re-enable FK constraints
    pg_cur.execute("SET session_replication_role = 'origin'")
    pg_conn.commit()

    sqlite_conn.close()
    pg_cur.close()
    pg_conn.close()

    print(f"\n  结果: {migrated} 成功, {skipped} 跳过, {len(errors)} 失败")
    if errors:
        print("\n  失败:")
        for t, e in errors:
            print(f"    {t}: {e}")
    return errors


def step3_reset_sequences(pg_engine):
    print("\n=== Step 3: 重置序列 ===")
    conn = pg_engine.raw_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.relname, t.relname, a.attname
        FROM pg_class c
        JOIN pg_depend d ON d.objid = c.oid
        JOIN pg_class t ON t.oid = d.refobjid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
        WHERE c.relkind = 'S'
    """)
    n = 0
    for seq, tbl, col in cur.fetchall():
        try:
            cur.execute(f'SELECT COALESCE(MAX("{col}"), 0) FROM "{tbl}"')
            mx = cur.fetchone()[0]
            if mx and mx > 0:
                cur.execute(f"SELECT setval('{seq}', {mx})")
                n += 1
        except Exception:
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print(f"  ✓ {n} 个序列重置")


def step4_verify(pg_url):
    print("\n=== Step 4: 验证 ===")
    from sqlalchemy import create_engine
    # Always create a fresh engine for verification to avoid stale pooled connections
    verify_engine = create_engine(pg_url, echo=False, pool_pre_ping=True)
    conn = verify_engine.raw_connection()
    cur = conn.cursor()

    checks = [
        ("courses", 15),
        ("trainings", 15),
        ("classrooms", 15),
        ("chapters", 60),
        ("resource_files", 2049),
        ("training_datasets", 28),
        ("training_environments", 3),
        ("api_users", None),
        ("practices", 9),
    ]

    ok = True
    for table, expected in checks:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            actual = cur.fetchone()[0]
            if expected is None:
                print(f"  ℹ️  {table}: {actual} (保留)")
            elif actual == expected:
                print(f"  ✅ {table}: {actual}")
            else:
                print(f"  ❌ {table}: {actual} (期望 {expected})")
                ok = False
        except Exception as e:
            print(f"  ❌ {table}: {e}")
            ok = False

    cur.close()
    conn.close()
    verify_engine.dispose()
    return ok


def main():
    print("╔══════════════════════════════════════════╗")
    print("║  SQLite → PostgreSQL 迁移 v2             ║")
    print("╚══════════════════════════════════════════╝")

    if not os.path.exists(SQLITE_PATH):
        print(f"❌ {SQLITE_PATH} 不存在"); sys.exit(1)

    pg = get_pg_engine()
    try:
        pg.raw_connection().close()
        print("✓ PG 连接成功")
    except Exception as e:
        print(f"❌ PG 连接失败: {e}"); sys.exit(1)

    pg_tables = step1_create_schema(pg)
    errors = step2_migrate_data(pg, pg_tables)
    step3_reset_sequences(pg)
    ok = step4_verify(PG_URL)

    print(f"\n{'✅ 迁移完成' if ok and not errors else '⚠️ 部分失败' if ok else '❌ 验证未通过'}")
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
