#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查枚举值
"""

from database import get_db, engine
from sqlalchemy import text

# 获取数据库连接
db = next(get_db())

try:
    print("✅ 数据库连接成功")
    
    # 检查task_type_enum
    result = db.execute(text("SELECT unnest(enum_range(NULL::task_type_enum))"))
    task_types = [row[0] for row in result]
    print(f"📋 task_type_enum的值: {task_types}")
    
    # 检查env_type_enum
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::env_type_enum))"))
        env_types = [row[0] for row in result]
        print(f"📋 env_type_enum的值: {env_types}")
    except Exception as e:
        print(f"❌ env_type_enum不存在或查询失败: {e}")
    
    # 检查difficulty_enum
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::difficulty_enum))"))
        difficulties = [row[0] for row in result]
        print(f"📋 difficulty_enum的值: {difficulties}")
    except Exception as e:
        print(f"❌ difficulty_enum不存在或查询失败: {e}")
        
    # 检查difficultylevel枚举
    try:
        result = db.execute(text("SELECT unnest(enum_range(NULL::difficultylevel))"))
        difficulty_levels = [row[0] for row in result]
        print(f"📋 difficultylevel的值: {difficulty_levels}")
    except Exception as e:
        print(f"❌ difficultylevel不存在或查询失败: {e}")
    
    # 检查submission_status_enum的值
    with engine.connect() as conn:
        result = conn.execute(text("SELECT unnest(enum_range(NULL::submission_status_enum))"))
        values = [row[0] for row in result]
        print('数据库中的submission_status_enum值:', values)
        
    # 检查grading_status_enum的值
    with engine.connect() as conn:
        result = conn.execute(text("SELECT unnest(enum_range(NULL::grading_status_enum))"))
        grading_enum_values = [row[0] for row in result]
        print('grading_status_enum 的实际值:', grading_enum_values)
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
finally:
    db.close()

if __name__ == "__main__":
    check_enum_values() 