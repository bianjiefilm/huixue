#!/usr/bin/env python3
"""
数据库迁移脚本：为course_resources表添加can_download字段
"""

import sqlite3
from pathlib import Path

def add_can_download_column():
    """为course_resources表添加can_download字段"""

    # 数据库路径
    db_path = Path("huixue_local.db")

    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(course_resources)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'can_download' in column_names:
            print("can_download字段已存在，无需迁移")
            conn.close()
            return True

        # 添加can_download字段，默认值为1（允许下载）
        cursor.execute("""
            ALTER TABLE course_resources
            ADD COLUMN can_download BOOLEAN DEFAULT 1 NOT NULL
        """)

        conn.commit()
        print("✅ 成功添加can_download字段到course_resources表")

        # 验证字段添加成功
        cursor.execute("PRAGMA table_info(course_resources)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"course_resources表当前字段: {column_names}")

        # 更新现有记录的can_download字段
        # 教师可以下载，学生不能下载的逻辑可以通过应用层控制
        cursor.execute("""
            UPDATE course_resources
            SET can_download = 1
            WHERE can_download IS NULL
        """)

        conn.commit()
        print("✅ 成功更新现有记录的can_download字段")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False

if __name__ == "__main__":
    print("开始数据库迁移：添加can_download字段到course_resources表")
    success = add_can_download_column()
    if success:
        print("数据库迁移完成")
    else:
        print("数据库迁移失败")
        exit(1)
