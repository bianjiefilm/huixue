#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查classroom_status_enum的值
"""

import psycopg2
from config import settings

def check_classroom_enum():
    """检查classroom_status_enum的值"""
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 检查classroom_status_enum的值
        cursor.execute("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'classroom_status_enum'
            )
            ORDER BY enumsortorder
        """)
        
        values = [row[0] for row in cursor.fetchall()]
        print(f"📋 classroom_status_enum的值: {values}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")

if __name__ == "__main__":
    check_classroom_enum() 