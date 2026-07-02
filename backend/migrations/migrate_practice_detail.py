#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实践详情功能数据库迁移脚本
添加新的字段和表结构
"""

import psycopg2
from config import settings

def run_migration():
    """执行数据库迁移"""
    print("🚀 开始执行实践详情功能数据库迁移")
    print("=" * 50)
    
    try:
        # 连接数据库
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        print("✅ 数据库连接成功")
        
        # 1. 为practices表添加新字段
        print("\n📝 为practices表添加新字段...")
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'practices' AND column_name IN ('summary', 'coin', 'task_count')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # 添加summary字段
        if 'summary' not in existing_columns:
            cursor.execute("ALTER TABLE practices ADD COLUMN summary TEXT")
            print("  ✅ 添加summary字段")
        else:
            print("  ⚠️  summary字段已存在")
        
        # 添加coin字段
        if 'coin' not in existing_columns:
            cursor.execute("ALTER TABLE practices ADD COLUMN coin INTEGER DEFAULT 0")
            print("  ✅ 添加coin字段")
        else:
            print("  ⚠️  coin字段已存在")
        
        # 添加task_count字段
        if 'task_count' not in existing_columns:
            cursor.execute("ALTER TABLE practices ADD COLUMN task_count INTEGER DEFAULT 0")
            print("  ✅ 添加task_count字段")
        else:
            print("  ⚠️  task_count字段已存在")
        
        # 2. 创建任务类型枚举
        print("\n📝 创建任务类型枚举...")
        try:
            cursor.execute("""
                CREATE TYPE task_type_enum AS ENUM ('practice', 'choice', 'judge')
            """)
            print("  ✅ 创建task_type_enum枚举")
        except psycopg2.errors.DuplicateObject:
            print("  ⚠️  task_type_enum枚举已存在")
            conn.rollback()
        
        # 3. 创建任务状态枚举
        print("\n📝 创建任务状态枚举...")
        try:
            cursor.execute("""
                CREATE TYPE task_status_enum AS ENUM ('未开始', '进行中', '已完成')
            """)
            print("  ✅ 创建task_status_enum枚举")
        except psycopg2.errors.DuplicateObject:
            print("  ⚠️  task_status_enum枚举已存在")
            conn.rollback()
        
        # 4. 创建tasks表
        print("\n📝 创建tasks表...")
        try:
            cursor.execute("""
                CREATE TABLE tasks (
                    id SERIAL PRIMARY KEY,
                    practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    coin INTEGER DEFAULT 0,
                    type task_type_enum NOT NULL,
                    "order" INTEGER NOT NULL DEFAULT 1,
                    status task_status_enum DEFAULT '未开始',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            print("  ✅ 创建tasks表")
        except psycopg2.errors.DuplicateTable:
            print("  ⚠️  tasks表已存在")
            conn.rollback()
        
        # 5. 创建practice_skills表
        print("\n📝 创建practice_skills表...")
        try:
            cursor.execute("""
                CREATE TABLE practice_skills (
                    id SERIAL PRIMARY KEY,
                    practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
                    skill_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            print("  ✅ 创建practice_skills表")
        except psycopg2.errors.DuplicateTable:
            print("  ⚠️  practice_skills表已存在")
            conn.rollback()
        
        # 6. 创建classroom_practices表
        print("\n📝 创建classroom_practices表...")
        try:
            cursor.execute("""
                CREATE TABLE classroom_practices (
                    id SERIAL PRIMARY KEY,
                    classroom_id INTEGER NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
                    practice_id INTEGER NOT NULL REFERENCES practices(id) ON DELETE CASCADE,
                    sync_doc BOOLEAN DEFAULT FALSE,
                    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(classroom_id, practice_id)
                )
            """)
            print("  ✅ 创建classroom_practices表")
        except psycopg2.errors.DuplicateTable:
            print("  ⚠️  classroom_practices表已存在")
            conn.rollback()
        
        # 7. 创建索引
        print("\n📝 创建索引...")
        
        indexes = [
            ("idx_tasks_practice_id", "CREATE INDEX IF NOT EXISTS idx_tasks_practice_id ON tasks(practice_id)"),
            ("idx_tasks_order", "CREATE INDEX IF NOT EXISTS idx_tasks_order ON tasks(practice_id, \"order\")"),
            ("idx_practice_skills_practice_id", "CREATE INDEX IF NOT EXISTS idx_practice_skills_practice_id ON practice_skills(practice_id)"),
            ("idx_classroom_practices_classroom_id", "CREATE INDEX IF NOT EXISTS idx_classroom_practices_classroom_id ON classroom_practices(classroom_id)"),
            ("idx_classroom_practices_practice_id", "CREATE INDEX IF NOT EXISTS idx_classroom_practices_practice_id ON classroom_practices(practice_id)")
        ]
        
        for index_name, sql in indexes:
            try:
                cursor.execute(sql)
                print(f"  ✅ 创建索引 {index_name}")
            except Exception as e:
                print(f"  ⚠️  索引 {index_name} 创建失败或已存在: {str(e)}")
        
        # 提交所有更改
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        
        # 验证迁移结果
        print("\n📋 验证迁移结果...")
        
        # 检查practices表的新字段
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'practices' AND column_name IN ('summary', 'coin', 'task_count')
            ORDER BY column_name
        """)
        
        practice_columns = cursor.fetchall()
        if practice_columns:
            print("  ✅ practices表新字段:")
            for col in practice_columns:
                print(f"    - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # 检查新表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('tasks', 'practice_skills', 'classroom_practices')
            ORDER BY table_name
        """)
        
        new_tables = cursor.fetchall()
        if new_tables:
            print("  ✅ 新创建的表:")
            for table in new_tables:
                print(f"    - {table[0]}")
        
        # 检查枚举类型
        cursor.execute("""
            SELECT typname 
            FROM pg_type 
            WHERE typname IN ('task_type_enum', 'task_status_enum')
            ORDER BY typname
        """)
        
        enums = cursor.fetchall()
        if enums:
            print("  ✅ 新创建的枚举类型:")
            for enum in enums:
                print(f"    - {enum[0]}")
        
        print("\n🎉 迁移验证完成！现在可以运行测试数据初始化脚本。")
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def rollback_migration():
    """回滚迁移（仅用于开发测试）"""
    print("⚠️  开始回滚迁移...")
    
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor()
        
        # 删除表（注意顺序，先删除有外键依赖的表）
        tables_to_drop = ['classroom_practices', 'practice_skills', 'tasks']
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"  ✅ 删除表 {table}")
            except Exception as e:
                print(f"  ⚠️  删除表 {table} 失败: {str(e)}")
        
        # 删除枚举类型
        enums_to_drop = ['task_status_enum', 'task_type_enum']
        for enum in enums_to_drop:
            try:
                cursor.execute(f"DROP TYPE IF EXISTS {enum} CASCADE")
                print(f"  ✅ 删除枚举 {enum}")
            except Exception as e:
                print(f"  ⚠️  删除枚举 {enum} 失败: {str(e)}")
        
        # 删除practices表的新字段
        columns_to_drop = ['task_count', 'coin', 'summary']
        for column in columns_to_drop:
            try:
                cursor.execute(f"ALTER TABLE practices DROP COLUMN IF EXISTS {column}")
                print(f"  ✅ 删除字段 practices.{column}")
            except Exception as e:
                print(f"  ⚠️  删除字段 practices.{column} 失败: {str(e)}")
        
        conn.commit()
        print("✅ 回滚完成")
        
    except Exception as e:
        print(f"❌ 回滚失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        run_migration()

if __name__ == "__main__":
    main() 