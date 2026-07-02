#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查外键约束
"""

import psycopg2
from config import settings
from database import get_db, engine
from sqlalchemy import inspect, text

def check_foreign_keys():
    """检查外键约束"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 检查classrooms表的外键约束
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name='classrooms'
                AND kcu.column_name = 'teacher_id'
        """)
        
        result = cursor.fetchall()
        print(f"📋 classrooms.teacher_id外键约束: {result}")
        
        # 检查是否存在users表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'api_users')
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 用户相关表: {tables}")
        
        # 检查tasks表的外键
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys('tasks')
        print('📋 tasks表的外键:')
        for fk in foreign_keys:
            print(f'  - {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')
        
        # 检查practice_id字段的详细信息
        columns = inspector.get_columns('tasks')
        for column in columns:
            if column['name'] == 'practice_id':
                print(f'📋 practice_id字段: {column}')
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")

if __name__ == "__main__":
    check_foreign_keys() 