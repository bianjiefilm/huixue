#!/usr/bin/env python3
"""
实训资源对象存储集成的数据库迁移脚本

功能：
1. 为trainings表添加对象存储支持字段
2. 改造training_datasets表支持对象存储路径
3. 创建training_assets表管理支持性素材
4. 创建相关索引和视图

使用方法：
python migrations/apply_training_storage_migration.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_path():
    """获取数据库文件路径"""
    # 尝试多个可能的路径
    possible_paths = [
        project_root / "huixue_local.db",
        project_root / "app" / "huixue_local.db",
        project_root / ".." / "huixue_local.db"
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # 如果没有找到，使用默认路径
    default_path = project_root / "huixue_local.db"
    logger.warning(f"数据库文件未找到，将使用默认路径: {default_path}")
    return str(default_path)

def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def check_column_exists(cursor, table_name, column_name):
    """检查表中是否存在指定列"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def backup_database(db_path):
    """备份数据库"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"备份数据库失败: {str(e)}")
        return None

def apply_migration():
    """应用数据库迁移"""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = backup_database(db_path)
    if not backup_path:
        logger.warning("数据库备份失败，继续执行迁移（风险自负）")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("开始执行数据库迁移...")
        
        # ============ 第一部分：修改 trainings 表 ============
        logger.info("1. 检查和修改 trainings 表...")
        
        if check_table_exists(cursor, "trainings"):
            # 添加新字段
            new_columns = [
                ("bi_template_path", "VARCHAR(500)"),
                ("ai_template_path", "VARCHAR(500)"),
                ("template_files_manifest", "TEXT")
            ]
            
            for column_name, column_type in new_columns:
                if not check_column_exists(cursor, "trainings", column_name):
                    try:
                        cursor.execute(f"ALTER TABLE trainings ADD COLUMN {column_name} {column_type}")
                        logger.info(f"  ✅ 添加字段 trainings.{column_name}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 添加字段 trainings.{column_name} 失败: {str(e)}")
                else:
                    logger.info(f"  ✅ 字段 trainings.{column_name} 已存在")
        else:
            logger.warning("  ⚠️ trainings 表不存在")
        
        # ============ 第二部分：修改 training_datasets 表 ============
        logger.info("2. 检查和修改 training_datasets 表...")
        
        if check_table_exists(cursor, "training_datasets"):
            # 添加新字段
            new_columns = [
                ("relative_path", "VARCHAR(500)"),
                ("file_size", "INTEGER"),
                ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
            ]
            
            for column_name, column_type in new_columns:
                if not check_column_exists(cursor, "training_datasets", column_name):
                    try:
                        cursor.execute(f"ALTER TABLE training_datasets ADD COLUMN {column_name} {column_type}")
                        logger.info(f"  ✅ 添加字段 training_datasets.{column_name}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 添加字段 training_datasets.{column_name} 失败: {str(e)}")
                else:
                    logger.info(f"  ✅ 字段 training_datasets.{column_name} 已存在")
                    
            # 修改file_size字段为可空
            try:
                # SQLite不支持直接修改列，需要重建表或使用默认值
                cursor.execute("UPDATE training_datasets SET file_size = 0 WHERE file_size IS NULL")
                logger.info("  ✅ 更新 training_datasets.file_size 默认值")
            except Exception as e:
                logger.warning(f"  ⚠️ 更新 training_datasets.file_size 失败: {str(e)}")
        else:
            logger.warning("  ⚠️ training_datasets 表不存在")
        
        # ============ 第三部分：创建 training_assets 表 ============
        logger.info("3. 创建 training_assets 表...")
        
        if not check_table_exists(cursor, "training_assets"):
            try:
                cursor.execute("""
                    CREATE TABLE training_assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        training_id INTEGER NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        relative_path VARCHAR(500) NOT NULL,
                        file_type VARCHAR(50) NOT NULL,
                        file_size INTEGER,
                        description TEXT,
                        uploader_id INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(training_id) REFERENCES trainings (id) ON DELETE CASCADE,
                        FOREIGN KEY(uploader_id) REFERENCES api_users (id)
                    )
                """)
                logger.info("  ✅ 创建 training_assets 表成功")
                
                # 创建索引
                indexes = [
                    ("idx_training_assets_training_id", "training_id"),
                    ("idx_training_assets_uploader_id", "uploader_id"),
                    ("idx_training_assets_file_type", "file_type")
                ]
                
                for index_name, column in indexes:
                    try:
                        cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON training_assets({column})")
                        logger.info(f"  ✅ 创建索引 {index_name}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ 创建索引 {index_name} 失败: {str(e)}")
                        
            except Exception as e:
                logger.error(f"  ❌ 创建 training_assets 表失败: {str(e)}")
        else:
            logger.info("  ✅ training_assets 表已存在")
        
        # ============ 第四部分：创建视图 ============
        logger.info("4. 创建实训完整信息视图...")
        
        try:
            # 删除现有视图（如果存在）
            cursor.execute("DROP VIEW IF EXISTS training_complete_info")
            
            # 创建新视图
            cursor.execute("""
                CREATE VIEW training_complete_info AS
                SELECT 
                    t.id,
                    t.title,
                    t.training_type,
                    t.intro,
                    t.industry,
                    t.difficulty,
                    t.course_hours,
                    t.handbook_content,
                    t.bi_template_path,
                    t.ai_template_path,
                    t.template_files_manifest,
                    t.publish_status,
                    t.created_at,
                    -- 统计关联文件数量
                    COALESCE((SELECT COUNT(*) FROM training_datasets td WHERE td.training_id = t.id), 0) as dataset_count,
                    COALESCE((SELECT COUNT(*) FROM training_jupyter_files tjf WHERE tjf.training_id = t.id), 0) as jupyter_file_count,
                    COALESCE((SELECT COUNT(*) FROM training_assets ta WHERE ta.training_id = t.id), 0) as asset_count
                FROM trainings t
            """)
            logger.info("  ✅ 创建 training_complete_info 视图成功")
        except Exception as e:
            logger.warning(f"  ⚠️ 创建视图失败: {str(e)}")
        
        # ============ 第五部分：数据初始化 ============
        logger.info("5. 初始化数据...")
        
        try:
            # 为现有trainings记录设置默认的模板文件清单
            cursor.execute("""
                UPDATE trainings 
                SET template_files_manifest = '{}' 
                WHERE template_files_manifest IS NULL
            """)
            updated_rows = cursor.rowcount
            logger.info(f"  ✅ 更新了 {updated_rows} 条 trainings 记录的模板文件清单")
            
            # 为现有training_datasets记录设置默认的relative_path
            if check_column_exists(cursor, "training_datasets", "relative_path"):
                cursor.execute("""
                    UPDATE training_datasets 
                    SET relative_path = CASE 
                        WHEN file_url IS NOT NULL AND file_url != '' THEN file_url
                        ELSE '/datasets/' || name
                    END
                    WHERE relative_path IS NULL OR relative_path = ''
                """)
                updated_rows = cursor.rowcount
                logger.info(f"  ✅ 更新了 {updated_rows} 条 training_datasets 记录的相对路径")
                
        except Exception as e:
            logger.warning(f"  ⚠️ 数据初始化失败: {str(e)}")
        
        # ============ 第六部分：验证迁移结果 ============
        logger.info("6. 验证迁移结果...")
        
        # 验证表结构
        tables_to_check = ["trainings", "training_datasets", "training_assets"]
        for table_name in tables_to_check:
            if check_table_exists(cursor, table_name):
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                logger.info(f"  ✅ {table_name} 表有 {len(columns)} 个字段")
            else:
                logger.warning(f"  ⚠️ {table_name} 表不存在")
        
        # 验证视图
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='training_complete_info'")
        if cursor.fetchone():
            logger.info("  ✅ training_complete_info 视图创建成功")
        else:
            logger.warning("  ⚠️ training_complete_info 视图不存在")
        
        # 提交事务
        conn.commit()
        logger.info("✅ 数据库迁移完成！")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("实训资源对象存储集成 - 数据库迁移")
    logger.info("=" * 60)
    
    try:
        success = apply_migration()
        
        if success:
            logger.info("\n🎉 迁移成功完成！")
            logger.info("\n新增功能:")
            logger.info("- trainings表支持BI/AI模板文件路径")
            logger.info("- training_datasets表支持对象存储路径")
            logger.info("- training_assets表管理支持性素材")
            logger.info("- training_complete_info视图提供完整信息")
        else:
            logger.error("\n❌ 迁移执行失败！")
            logger.error("请检查错误日志并手动修复")
            return 1
            
    except Exception as e:
        logger.error(f"\n💥 迁移过程中发生异常: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 