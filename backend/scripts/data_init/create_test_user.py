#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在users表中创建测试用户
"""

import psycopg2
from config import settings

def create_test_user():
    """在users表中创建测试用户"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 检查users表结构
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("📋 users表结构:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # 检查是否已存在ID为1的用户
        cursor.execute("SELECT id, username FROM users WHERE id = 1")
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"⚠️  ID为1的用户已存在: {existing_user}")
        else:
            # 创建测试用户
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, full_name, email, created_at) 
                VALUES (1, 'teacher1', 'dummy_hash', '测试教师1', 'teacher1@example.com', NOW())
            """)
            print("✅ 创建测试用户成功")
        
        # 验证创建结果
        cursor.execute("SELECT id, username, email, full_name FROM users WHERE id = 1")
        user = cursor.fetchone()
        if user:
            print(f"📋 用户信息: ID={user[0]}, Username={user[1]}, Email={user[2]}, FullName={user[3]}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ 创建失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    create_test_user() 