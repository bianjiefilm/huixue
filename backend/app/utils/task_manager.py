#!/usr/bin/env python3
"""
简单的内存任务管理器
在生产环境中，建议使用Redis或数据库来持久化任务状态
"""

import uuid
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

class Task:
    """任务类"""
    def __init__(self, task_id: str, task_type: str):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result: Optional[Any] = None
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def update_status(self, status: TaskStatus, progress: int = None, result: Any = None, error_message: str = None):
        """更新任务状态"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if result is not None:
            self.result = result
        if error_message is not None:
            self.error_message = error_message
        self.updated_at = datetime.now()

class TaskManager:
    """简单的内存任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
        # 启动清理线程，定期清理过期任务
        self._start_cleanup_thread()
    
    def create_task(self, task_type: str = "full_course_generation") -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tasks[task_id] = Task(task_id, task_type)
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, status: TaskStatus, progress: int = None, result: Any = None, error_message: str = None):
        """更新任务状态"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                task.update_status(status, progress, result, error_message)
    
    def delete_task(self, task_id: str):
        """删除任务"""
        with self.lock:
            self.tasks.pop(task_id, None)
    
    def _cleanup_expired_tasks(self):
        """清理过期任务（24小时后）"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        with self.lock:
            expired_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.updated_at < cutoff_time
            ]
            for task_id in expired_tasks:
                del self.tasks[task_id]
        
        if expired_tasks:
            print(f"清理了 {len(expired_tasks)} 个过期任务")
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_worker():
            while True:
                time.sleep(3600)  # 每小时运行一次
                try:
                    self._cleanup_expired_tasks()
                except Exception as e:
                    print(f"清理任务时出错: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

# 全局任务管理器实例
task_manager = TaskManager() 