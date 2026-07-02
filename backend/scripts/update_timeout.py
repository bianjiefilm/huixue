#!/usr/bin/env python3
"""
更新所有任务的评测超时时间
将 evaluation_timeout_seconds 从 20/30/60 秒更新为 300 秒 (5分钟)
"""
import sqlite3
import sys
import os

# 连接数据库
db_path = "/mnt/d/Projects/huixue-yuanban/backend/huixue_local.db"

def update_timeouts():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 先查看当前的 timeout 设置
    print("=" * 60)
    print("📊 更新前 timeout 配置:")
    print("=" * 60)
    cursor.execute("SELECT id, title, evaluation_timeout_seconds FROM tasks WHERE evaluation_timeout_seconds IS NOT NULL LIMIT 20")
    for row in cursor.fetchall():
        print(f"  Task ID {row[0]}: {row[1][:30]}... | Timeout: {row[2]}s")

    # 更新所有任务的超时时间为 300 秒
    print("\n" + "=" * 60)
    print("🔧 更新所有任务超时时间为 300 秒 (5分钟)...")
    print("=" * 60)

    cursor.execute("UPDATE tasks SET evaluation_timeout_seconds = 300 WHERE evaluation_timeout_seconds IS NOT NULL")
    conn.commit()

    # 验证更新
    cursor.execute("SELECT COUNT(*), AVG(evaluation_timeout_seconds) FROM tasks WHERE evaluation_timeout_seconds = 300")
    result = cursor.fetchone()
    print(f"✅ 已更新 {result[0]} 个任务，平均超时时间: {result[1]}s")

    # 也更新默认值（未来新建的任务）
    # SQLite 不支持 ALTER COLUMN，所以我们需要重建表或者使用 trigger
    # 这里我们不做修改，默认值在代码中设置

    conn.close()
    print("\n✅ 超时配置更新完成！")

if __name__ == "__main__":
    update_timeouts()
