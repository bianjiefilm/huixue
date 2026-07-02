#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查tasks表的结构
"""

import psycopg2
from config import settings

def check_tasks_table():
    """检查tasks表的结构"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 检查tasks表是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'tasks'
        """)
        
        table_exists = cursor.fetchone()
        if table_exists:
            print("✅ tasks表存在")
            
            # 检查tasks表结构
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'tasks' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("📋 tasks表结构:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        else:
            print("❌ tasks表不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")

if __name__ == "__main__":
    check_tasks_table() 