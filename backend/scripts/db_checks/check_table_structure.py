#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

from database import engine
from sqlalchemy import text, inspect

def check_table_structure():
    print("🔍 检查数据库表结构...")
    print("=" * 50)
    
    # 检查tasks表结构
    inspector = inspect(engine)
    
    if 'tasks' in inspector.get_table_names():
        print("📋 tasks表字段:")
        columns = inspector.get_columns('tasks')
        for col in columns:
            print(f"  {col['name']:25} {col['type']}")
    else:
        print("❌ tasks表不存在")
    
    print()
    
    # 检查task_tests表结构
    if 'task_tests' in inspector.get_table_names():
        print("📋 task_tests表字段:")
        columns = inspector.get_columns('task_tests')
        for col in columns:
            print(f"  {col['name']:25} {col['type']}")
    else:
        print("❌ task_tests表不存在")

if __name__ == "__main__":
    check_table_structure() 