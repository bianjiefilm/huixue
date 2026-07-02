#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库迁移结果
"""

import psycopg2
from config import settings

def check_migration():
    """检查迁移结果"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 检查practices表的列
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'practices' 
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 practices表的列: {columns}")
        
        # 检查新字段是否存在
        new_fields = ['summary', 'coin', 'task_count']
        for field in new_fields:
            if field in columns:
                print(f"✅ {field} 字段已存在")
            else:
                print(f"❌ {field} 字段不存在")
        
        # 检查新表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('tasks', 'practice_skills', 'classroom_practices')
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 新表: {tables}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")

if __name__ == "__main__":
    check_migration() 