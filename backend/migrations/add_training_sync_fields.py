"""
迁移脚本：为训练同步系统添加必要的数据库字段

此脚本为trainings表添加以下字段以支持资源同步：
- handbook_content_url: 手册内容的URL
- cover_url: 封面图片的URL
- estimated_completion_time: 预计完成时间
- prerequisites: 先修要求（JSON数组）
- learning_objectives: 学习目标（JSON数组）
- tags: 标签（JSON数组）
- version: 版本号
- last_synced_at: 最后同步时间
"""

import logging
from sqlalchemy import MetaData, Column, String, Text, DateTime, create_engine, text
import os
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./huixue_local.db")

def add_training_sync_fields():
    """为trainings表添加同步相关的字段"""

    # 创建同步引擎
    engine = create_engine(DATABASE_URL, echo=True)

    with engine.connect() as conn:
        # 定义要添加的列SQL语句
        alter_statements = [
            "ALTER TABLE trainings ADD COLUMN handbook_content_url VARCHAR(500) NULL",
            "ALTER TABLE trainings ADD COLUMN cover_url VARCHAR(500) NULL",
            "ALTER TABLE trainings ADD COLUMN estimated_completion_time VARCHAR(100) NULL",
            "ALTER TABLE trainings ADD COLUMN prerequisites TEXT NULL",
            "ALTER TABLE trainings ADD COLUMN learning_objectives TEXT NULL",
            "ALTER TABLE trainings ADD COLUMN tags TEXT NULL",
            "ALTER TABLE trainings ADD COLUMN version VARCHAR(50) NULL",
            "ALTER TABLE trainings ADD COLUMN last_synced_at DATETIME NULL",
            "ALTER TABLE training_datasets ADD COLUMN access_path_in_env VARCHAR(500) NULL",
            "ALTER TABLE training_assets ADD COLUMN asset_type VARCHAR(100) NULL"
        ]

        # 执行每个ALTER语句
        for sql in alter_statements:
            try:
                logger.info(f"执行: {sql.split('ADD COLUMN')[1].strip() if 'ADD COLUMN' in sql else sql}")
                conn.execute(text(sql))
                logger.info("✅ 成功")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info("⚠️  列已存在，跳过")
                else:
                    logger.error(f"❌ 执行失败: {e}")

        conn.commit()
        logger.info("数据库schema更新完成")

def main():
    """主函数"""
    logger.info("开始更新数据库schema以支持训练资源同步...")

    try:
        add_training_sync_fields()
        logger.info("✅ 数据库schema更新成功完成")
    except Exception as e:
        logger.error(f"❌ 数据库schema更新失败: {e}")
        raise

if __name__ == "__main__":
    main()
