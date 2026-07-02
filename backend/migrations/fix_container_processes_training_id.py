"""
迁移脚本：为container_processes表添加training_id列

此脚本修复container_processes表缺少training_id列的问题
"""

import logging
from sqlalchemy import create_engine, text
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./huixue_local.db")

def fix_container_processes():
    """为container_processes表添加training_id列"""

    # 创建同步引擎
    engine = create_engine(DATABASE_URL, echo=True)

    with engine.connect() as conn:
        # 定义要添加的列SQL语句
        alter_statements = [
            "ALTER TABLE container_processes ADD COLUMN training_id INTEGER NULL REFERENCES trainings(id)",
        ]

        # 执行每个ALTER语句
        for sql in alter_statements:
            try:
                logger.info(f"执行: {sql}")
                conn.execute(text(sql))
                logger.info("✅ 成功")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column name" in error_msg or "already exists" in error_msg:
                    logger.info("⚠️  列已存在，跳过")
                else:
                    logger.error(f"❌ 执行失败: {e}")

        conn.commit()
        logger.info("数据库schema更新完成")

def main():
    """主函数"""
    logger.info("开始修复container_processes表...")
    logger.info(f"数据库URL: {DATABASE_URL}")

    try:
        fix_container_processes()
        logger.info("✅ container_processes表修复成功")
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}")
        raise

if __name__ == "__main__":
    main()
