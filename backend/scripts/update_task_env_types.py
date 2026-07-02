#!/usr/bin/env python3
"""
更新任务的环境类型，让不同的任务使用不同的环境
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Task
from sqlalchemy.orm import Session


def update_task_env_types():
    """为不同的任务设置不同的环境类型"""
    db = SessionLocal()
    
    try:
        # 获取所有任务
        tasks = db.query(Task).all()
        
        for task in tasks:
            print(f"=== 更新任务环境类型: {task.title} (ID: {task.id}) ===")
            
            # 根据任务内容设置不同的环境类型
            if "Hadoop" in task.title or "HDFS" in task.title or "MapReduce" in task.title:
                # Hadoop相关任务使用命令行环境
                task.env_type = "COMMAND_LINE"
                env_desc = "命令行"
            elif "HTML" in task.title.upper() or "前端" in task.title:
                # HTML相关任务使用HTML预览环境
                task.env_type = "HTML_PREVIEW"
                env_desc = "HTML预览"
            elif "Docker" in task.title or "深度学习" in task.title:
                # Docker和深度学习任务使用云桌面环境
                task.env_type = "CLOUD_DESKTOP"
                env_desc = "云桌面"
            else:
                # 其他任务使用在线编码环境
                task.env_type = "CODING_ONLINE"
                env_desc = "在线编码"
            
            print(f"✅ 设置环境类型为: {env_desc} ({task.env_type})")
        
        # 提交所有更改
        db.commit()
        print("\n🎉 所有任务环境类型更新完成！")
        
        # 显示汇总
        print("\n=== 环境类型分布 ===")
        env_counts = {}
        for task in tasks:
            env_type = task.env_type or "未设置"
            env_counts[env_type] = env_counts.get(env_type, 0) + 1
        
        for env_type, count in env_counts.items():
            print(f"{env_type}: {count} 个任务")
        
    except Exception as e:
        print(f"❌ 更新环境类型时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_task_env_types()