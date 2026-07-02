#!/usr/bin/env python3
"""
环境镜像数据播种脚本
Seeds environment configurations for practice environments
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.models import PracticeEnvironmentConfig


def seed_environments():
    """播种环境配置数据"""
    db = SessionLocal()

    try:
        # 定义要播种的环境配置
        environments = [
            {
                "name": "大数据综合环境 (Hadoop+Spark)",
                "environment_type": "webide",
                "description": "包含Hadoop 3.x、Spark 3.x、Hive 3.x的大数据综合开发环境",
                "docker_image": "huixue/bigdata-env:latest",
                "docker_port": 8888,
                # 存储配置 (MB)
                "storage_min": 5120,      # 5GB
                "storage_max": 20480,     # 20GB
                "storage_default": 10240, # 10GB
                # 内存配置 (MB)
                "memory_min": 2048,       # 2GB
                "memory_max": 8192,       # 8GB
                "memory_default": 4096,   # 4GB
                # CPU配置 (核心数)
                "cpu_min": 1,
                "cpu_max": 4,
                "cpu_default": 2,
                "is_active": True,
            },
            {
                "name": "Jupyter数据分析环境",
                "environment_type": "jupyter",
                "description": "基于JupyterLab的Python数据分析环境，预装pandas、numpy、sklearn等库",
                "docker_image": "huixue/jupyter-datascience:latest",
                "docker_port": 8888,
                # 存储配置 (MB)
                "storage_min": 2048,      # 2GB
                "storage_max": 10240,     # 10GB
                "storage_default": 5120,  # 5GB
                # 内存配置 (MB)
                "memory_min": 1024,       # 1GB
                "memory_max": 4096,       # 4GB
                "memory_default": 2048,   # 2GB
                # CPU配置 (核心数)
                "cpu_min": 1,
                "cpu_max": 2,
                "cpu_default": 1,
                "is_active": True,
            },
            {
                "name": "Python开发环境",
                "environment_type": "webide",
                "description": "轻量级Python开发环境，适合基础编程学习",
                "docker_image": "huixue/python-dev:latest",
                "docker_port": 8080,
                # 存储配置 (MB)
                "storage_min": 1024,      # 1GB
                "storage_max": 5120,      # 5GB
                "storage_default": 2048,  # 2GB
                # 内存配置 (MB)
                "memory_min": 512,        # 512MB
                "memory_max": 2048,       # 2GB
                "memory_default": 1024,   # 1GB
                # CPU配置 (核心数)
                "cpu_min": 1,
                "cpu_max": 2,
                "cpu_default": 1,
                "is_active": True,
            },
            {
                "name": "深度学习环境 (GPU)",
                "environment_type": "jupyter",
                "description": "支持GPU加速的深度学习环境，预装TensorFlow、PyTorch",
                "docker_image": "huixue/deeplearning-gpu:latest",
                "docker_port": 8888,
                # 存储配置 (MB)
                "storage_min": 10240,     # 10GB
                "storage_max": 51200,     # 50GB
                "storage_default": 20480, # 20GB
                # 内存配置 (MB)
                "memory_min": 4096,       # 4GB
                "memory_max": 16384,      # 16GB
                "memory_default": 8192,   # 8GB
                # CPU配置 (核心数)
                "cpu_min": 2,
                "cpu_max": 8,
                "cpu_default": 4,
                "is_active": True,
            },
            {
                "name": "Flink流处理环境",
                "environment_type": "webide",
                "description": "Apache Flink实时流处理开发环境",
                "docker_image": "huixue/flink-env:latest",
                "docker_port": 8081,
                # 存储配置 (MB)
                "storage_min": 5120,      # 5GB
                "storage_max": 20480,     # 20GB
                "storage_default": 10240, # 10GB
                # 内存配置 (MB)
                "memory_min": 2048,       # 2GB
                "memory_max": 8192,       # 8GB
                "memory_default": 4096,   # 4GB
                # CPU配置 (核心数)
                "cpu_min": 2,
                "cpu_max": 4,
                "cpu_default": 2,
                "is_active": True,
            },
        ]

        created_count = 0
        updated_count = 0

        for env_data in environments:
            # 检查是否已存在
            existing = db.query(PracticeEnvironmentConfig).filter(
                PracticeEnvironmentConfig.name == env_data["name"]
            ).first()

            if existing:
                # 更新现有记录
                for key, value in env_data.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"✅ 更新环境配置: {env_data['name']}")
            else:
                # 创建新记录
                new_env = PracticeEnvironmentConfig(**env_data)
                db.add(new_env)
                created_count += 1
                print(f"✅ 创建环境配置: {env_data['name']}")

        db.commit()

        print(f"\n📊 播种完成: 创建 {created_count} 条, 更新 {updated_count} 条")

        # 显示所有环境配置
        print("\n📋 当前所有环境配置:")
        all_envs = db.query(PracticeEnvironmentConfig).all()
        for env in all_envs:
            print(f"  - {env.name} ({env.environment_type})")
            print(f"    CPU: {env.cpu_default}核 | 内存: {env.memory_default}MB | 存储: {env.storage_default}MB")
            print(f"    镜像: {env.docker_image}")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ 播种失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 开始播种环境配置数据...\n")
    success = seed_environments()
    sys.exit(0 if success else 1)
