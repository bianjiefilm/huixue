"""
健康检查端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text  # 添加text导入
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="",
    tags=['health']
)

@router.get("/")
async def root():
    return {"message": "欢迎使用慧学 API", "status": "运行中"}

# 健康检查

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # 测试数据库连接 - 使用text()包装SQL字符串，兼容SQLite
        result = db.execute(text("SELECT 1 as test_connection"))
        connection_test = result.fetchone()
        
        if connection_test:
            # 如果连接成功，尝试创建数据库表
            try:
                Base.metadata.create_all(bind=engine)
                
                # 获取数据库版本信息 - 兼容SQLite和PostgreSQL
                try:
                    # 尝试SQLite的版本查询
                    version_result = db.execute(text("SELECT sqlite_version()"))
                    db_version = f"SQLite {version_result.fetchone()[0]}"
                except:
                    try:
                        # 如果是PostgreSQL
                        version_result = db.execute(text("SELECT version()"))
                        db_version = version_result.fetchone()[0] if version_result else "未知版本"
                    except:
                        db_version = "未知数据库版本"
                
                return {
                    "status": "健康", 
                    "database": "已连接", 
                    "tables": "已创建",
                    "db_version": db_version[:50] + "..." if len(db_version) > 50 else db_version,
                    "connection_test": "通过"
                }
            except Exception as table_error:
                return {
                    "status": "健康", 
                    "database": "已连接", 
                    "tables": f"创建失败: {str(table_error)}",
                    "connection_test": "通过"
                }
        else:
            raise Exception("数据库连接测试失败")
            
    except Exception as e:
        # 记录详细错误信息
        logger.error(f"数据库连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"数据库连接失败: {str(e)}"
        )

# ==================== 课程实践相关API ====================

# 4.1 课程资源库

