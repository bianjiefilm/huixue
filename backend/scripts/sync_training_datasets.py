#!/usr/bin/env python3
"""
同步实训数据集到数据库
从本地资源目录读取数据集文件信息并添加到数据库
"""
import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import SessionLocal
from app.models.models import Training, TrainingDataset, User

# 资源目录
RESOURCE_BASE = Path("/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/实训资源")

# 实训名称到目录的映射
TRAINING_DIR_MAP = {
    "某零售企业经营分析": "01-某零售企业经营分析",
    "设备重过载精准预测": "12-设备重过载精准预测",
    "轮胎质量相关性分析(AI版)": "09-轮胎质量相关性分析",
    "风电设备健康预警模型": "07-风电齿轮箱预警分析",
}


def get_admin_user(db) -> int:
    """获取管理员用户ID"""
    # 直接使用第一个用户作为上传者
    user = db.query(User).first()
    return user.id if user else 1


def sync_datasets():
    """同步数据集到数据库"""
    db = SessionLocal()

    try:
        admin_id = get_admin_user(db)
        print(f"使用上传者ID: {admin_id}\n")

        # 获取所有实训
        trainings = db.query(Training).all()
        print(f"共找到 {len(trainings)} 个实训\n")

        total_added = 0

        for training in trainings:
            # 尝试找到对应的本地目录
            training_dir = None

            # 1. 尝试使用映射
            if training.title in TRAINING_DIR_MAP:
                training_dir = RESOURCE_BASE / TRAINING_DIR_MAP[training.title]

            # 2. 尝试遍历目录查找
            if not training_dir or not training_dir.exists():
                for dir_path in RESOURCE_BASE.iterdir():
                    if dir_path.is_dir() and training.title in dir_path.name:
                        training_dir = dir_path
                        break

            if not training_dir or not training_dir.exists():
                print(f"[跳过] {training.title} - 未找到本地目录")
                continue

            # 检查datasets子目录
            datasets_dir = training_dir / "datasets"
            if not datasets_dir.exists():
                print(f"[跳过] {training.title} - 无datasets目录")
                continue

            # 获取现有数据集
            existing_datasets = db.query(TrainingDataset).filter(
                TrainingDataset.training_id == training.id
            ).all()
            existing_names = {d.name for d in existing_datasets}

            print(f"\n[处理] {training.title}")
            print(f"  目录: {training_dir.name}")
            print(f"  已有数据集: {len(existing_datasets)} 个")

            added = 0
            for file_path in datasets_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    if file_path.name in existing_names:
                        print(f"  [已存在] {file_path.name}")
                        continue

                    # 判断文件类型
                    ext = file_path.suffix.lower()
                    file_type_map = {
                        '.csv': 'csv',
                        '.xlsx': 'excel',
                        '.xls': 'excel',
                        '.json': 'json',
                        '.sql': 'sql_data',
                        '.txt': 'text',
                        '.parquet': 'parquet'
                    }
                    file_type = file_type_map.get(ext, 'other')

                    # 计算文件大小
                    file_size = file_path.stat().st_size

                    # 创建数据集记录
                    dataset = TrainingDataset(
                        training_id=training.id,
                        name=file_path.name,
                        file_url=f"/api/v1/files/training-resources/{training_dir.name}/datasets/{file_path.name}",
                        relative_path=f"实训资源/{training_dir.name}/datasets/{file_path.name}",
                        file_type=file_type,
                        file_size=file_size,
                        description=f"{training.title} 数据集 - {file_path.name}",
                        uploader_id=admin_id
                    )
                    db.add(dataset)
                    print(f"  [添加] {file_path.name} ({file_size / 1024:.1f} KB)")
                    added += 1

            if added > 0:
                db.commit()
                total_added += added
                print(f"  新增 {added} 个数据集")
            else:
                print(f"  无需添加")

        print(f"\n同步完成: 共添加 {total_added} 个数据集")

    except Exception as e:
        db.rollback()
        print(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("同步实训数据集到数据库")
    print("=" * 60)
    sync_datasets()
