#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查courses表结构
"""

import psycopg2
from config import settings

def check_courses_table():
    """检查courses表的结构"""
    try:
        # 连接数据库
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # 检查courses表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'courses'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        print(f"📋 courses表存在: {table_exists}")
        
        if table_exists:
            # 获取courses表的列信息
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'courses'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("\n📊 courses表的列结构:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # 查看表中的数据
            cursor.execute("SELECT COUNT(*) FROM courses;")
            count = cursor.fetchone()[0]
            print(f"\n📈 courses表中的记录数: {count}")
            
            if count > 0:
                cursor.execute("SELECT * FROM courses LIMIT 3;")
                rows = cursor.fetchall()
                print("\n📝 前3条记录:")
                for i, row in enumerate(rows, 1):
                    print(f"  记录{i}: {row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")

if __name__ == "__main__":
    check_courses_table() 