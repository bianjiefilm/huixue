#!/usr/bin/env python3
"""SQLite → PostgreSQL migration v3: truncate-all-first, then insert"""
import sqlite3, psycopg2, os

SQLITE = os.environ.get('SQLITE_PATH', '/tmp/huixue_local.db')
PG = os.environ.get('PG_DSN', 'host=localhost port=5432 dbname=huixue user=huixue password=huixue123')
KEEP = {'api_users', 'user_profiles', 'schools', 'organizations'}

sq = sqlite3.connect(SQLITE)
sq.row_factory = sqlite3.Row
sc = sq.cursor()
pg = psycopg2.connect(PG)
pc = pg.cursor()

def pg_cols(t):
    pc.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s AND table_schema='public'", (t,))
    return {r[0] for r in pc.fetchall()}

def bool_cols(t):
    pc.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s AND table_schema='public' AND data_type='boolean'", (t,))
    return {r[0] for r in pc.fetchall()}

# Get sqlite tables
sc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [r[0] for r in sc.fetchall()]

# Disable FK, truncate ALL (no cascade)
pc.execute("SET session_replication_role = 'replica'")
pg.commit()

for t in tables:
    if not pg_cols(t) or t in KEEP:
        continue
    try:
        pc.execute('TRUNCATE TABLE "' + t + '"')
    except:
        pg.rollback()
        pc.execute("SET session_replication_role = 'replica'")
pg.commit()
print("All tables truncated")

# Insert all data
ok = 0
for t in sorted(tables):
    pcols = pg_cols(t)
    if not pcols or t in KEEP:
        continue
    sc.execute('SELECT COUNT(*) FROM "' + t + '"')
    if sc.fetchone()[0] == 0:
        continue

    sc.execute('SELECT * FROM "' + t + '"')
    rows = sc.fetchall()
    cols = [d[0] for d in sc.description]
    bc = bool_cols(t)
    valid = [c for c in cols if c in pcols]
    if not valid:
        continue
    idx = [cols.index(c) for c in valid]
    bset = {i for i, c in enumerate(valid) if c in bc}

    col_str = ", ".join(['"' + c + '"' for c in valid])
    ph = ", ".join(["%s"] * len(valid))
    sql = 'INSERT INTO "' + t + '" (' + col_str + ') VALUES (' + ph + ')'

    vals = []
    for row in rows:
        rv = []
        for vi, oi in enumerate(idx):
            v = row[oi]
            if vi in bset and isinstance(v, int):
                v = bool(v)
            rv.append(v)
        vals.append(tuple(rv))

    try:
        pc.executemany(sql, vals)
        pg.commit()
        ok += 1
        print("  " + t + ": " + str(len(vals)))
    except Exception as e:
        pg.rollback()
        pc.execute("SET session_replication_role = 'replica'")
        print("  FAIL " + t + ": " + str(e)[:80])

# Re-enable FK
pc.execute("SET session_replication_role = 'origin'")
pg.commit()

# Reset sequences
pc.execute("""SELECT c.relname,t.relname,a.attname FROM pg_class c
    JOIN pg_depend d ON d.objid=c.oid JOIN pg_class t ON t.oid=d.refobjid
    JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=d.refobjsubid
    WHERE c.relkind='S'""")
for seq, tbl, col in pc.fetchall():
    try:
        pc.execute('SELECT COALESCE(MAX("' + col + '"),0) FROM "' + tbl + '"')
        mx = pc.fetchone()[0]
        if mx and mx > 0:
            pc.execute("SELECT setval('" + seq + "'," + str(mx) + ")")
    except:
        pg.rollback()
pg.commit()

# Verify
print()
for t, exp in [("courses",15),("trainings",15),("classrooms",15),("chapters",60),
               ("resource_files",2049),("training_datasets",28),("training_environments",3),
               ("practices",9),("classroom_courses",15),("classroom_students",36),("resource_modules",26)]:
    pc.execute('SELECT count(*) FROM "' + t + '"')
    a = pc.fetchone()[0]
    mark = "OK" if a == exp else "!!"
    print("  " + mark + " " + t + ": " + str(a) + "/" + str(exp))

pg.close()
sq.close()
print("\nDone: " + str(ok) + " tables migrated")
