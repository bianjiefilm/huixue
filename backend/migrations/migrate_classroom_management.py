#!/usr/bin/env python3
"""
课堂管理功能数据库迁移脚本

添加课堂章节表和相关字段，支持课堂管理功能
"""

import sys
from sqlalchemy import text
from database import engine, get_db
from models import Base
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_classroom_chapters_table():
    """创建课堂章节表"""
    sql = """
    CREATE TABLE IF NOT EXISTS classroom_chapters (
        id SERIAL PRIMARY KEY,
        classroom_id INTEGER REFERENCES classrooms(id) NOT NULL,
        title VARCHAR(255) NOT NULL,
        order_index INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_classroom_chapters_classroom_id ON classroom_chapters(classroom_id);
    CREATE INDEX IF NOT EXISTS idx_classroom_chapters_order ON classroom_chapters(classroom_id, order_index);
    """
    
    with engine.begin() as conn:
        conn.execute(text(sql))
    
    logger.info("✅ 课堂章节表创建成功")

def add_classroom_chapter_id_to_courses():
    """为课堂课程表添加章节ID字段"""
    sql = """
    -- 添加章节ID字段（如果不存在）
    DO $$ 
    BEGIN 
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'classroom_courses' 
            AND column_name = 'classroom_chapter_id'
        ) THEN
            ALTER TABLE classroom_courses 
            ADD COLUMN classroom_chapter_id INTEGER REFERENCES classroom_chapters(id);
            
            -- 创建索引
            CREATE INDEX idx_classroom_courses_chapter_id ON classroom_courses(classroom_chapter_id);
        END IF;
    END $$;
    """
    
    with engine.begin() as conn:
        conn.execute(text(sql))
    
    logger.info("✅ 课堂课程表章节ID字段添加成功")

def migrate_existing_data():
    """迁移现有数据，为现有课程创建章节"""
    sql = """
    -- 为每个课堂的现有课程创建默认章节
    INSERT INTO classroom_chapters (classroom_id, title, order_index)
    SELECT DISTINCT 
        cc.classroom_id,
        COALESCE(cc.classroom_chapter_title, '默认章节') as title,
        1 as order_index
    FROM classroom_courses cc
    LEFT JOIN classroom_chapters ch ON ch.classroom_id = cc.classroom_id 
        AND ch.title = COALESCE(cc.classroom_chapter_title, '默认章节')
    WHERE ch.id IS NULL 
        AND cc.classroom_chapter_title IS NOT NULL
        AND cc.classroom_chapter_title != '';
    
    -- 更新课程的章节关联
    UPDATE classroom_courses cc
    SET classroom_chapter_id = ch.id
    FROM classroom_chapters ch
    WHERE ch.classroom_id = cc.classroom_id
        AND ch.title = COALESCE(cc.classroom_chapter_title, '默认章节')
        AND cc.classroom_chapter_id IS NULL;
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(sql))
    
    logger.info("✅ 现有数据迁移完成")

def verify_migration():
    """验证迁移结果"""
    sql = """
    SELECT 
        COUNT(*) as total_chapters,
        COUNT(DISTINCT classroom_id) as classrooms_with_chapters
    FROM classroom_chapters;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        row = result.fetchone()
        
        if row:
            logger.info(f"📊 迁移验证: 共创建 {row[0]} 个章节，涉及 {row[1]} 个课堂")
        
        # 检查课程关联
        sql2 = """
        SELECT 
            COUNT(*) as total_courses,
            COUNT(classroom_chapter_id) as courses_with_chapters
        FROM classroom_courses;
        """
        
        result2 = conn.execute(text(sql2))
        row2 = result2.fetchone()
        
        if row2:
            logger.info(f"📊 课程关联: 共 {row2[0]} 个课程，其中 {row2[1]} 个已关联章节")

def rollback_migration():
    """回滚迁移（仅用于测试）"""
    sql = """
    -- 移除课程表的章节ID字段
    ALTER TABLE classroom_courses DROP COLUMN IF EXISTS classroom_chapter_id;
    
    -- 删除章节表
    DROP TABLE IF EXISTS classroom_chapters;
    """
    
    with engine.begin() as conn:
        conn.execute(text(sql))
    
    logger.info("⚠️ 迁移已回滚")

def main():
    """主迁移函数"""
    logger.info("🚀 开始课堂管理功能数据库迁移")
    
    try:
        # 检查数据库连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ 数据库连接正常")
        
        # 执行迁移步骤
        logger.info("1️⃣ 创建课堂章节表...")
        create_classroom_chapters_table()
        
        logger.info("2️⃣ 添加课程表章节ID字段...")
        add_classroom_chapter_id_to_courses()
        
        logger.info("3️⃣ 迁移现有数据...")
        migrate_existing_data()
        
        logger.info("4️⃣ 验证迁移结果...")
        verify_migration()
        
        logger.info("🎉 课堂管理功能数据库迁移完成！")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {str(e)}")
        logger.error("请检查数据库连接和权限设置")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="课堂管理功能数据库迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移（仅用于测试）")
    
    args = parser.parse_args()
    
    if args.rollback:
        logger.warning("⚠️ 执行回滚操作...")
        rollback_migration()
    else:
        main() 