"""
关卡创建前准备功能的CRUD操作
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from app.models import models
from app.crud.crud import get_custom_practice_detail
from app.utils.canvas_helpers import format_file_size as _format_file_size


def get_repository_files_list(
    db: Session,
    practice_id: int,
    creator_id: int,
    path: str = ""
):
    """获取代码仓库文件列表"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 检查代码仓库是否存在
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if not repo or not repo.is_enabled:
        return None
    
    # 模拟文件树结构（实际项目中应该调用Git API）
    base_files = [
        {
            "path": "README.md",
            "name": "README.md",
            "type": "file",
            "is_directory": False,
            "size": 1024,
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        {
            "path": "src",
            "name": "src",
            "type": "directory",
            "is_directory": True,
            "size": None,
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        {
            "path": "tests",
            "name": "tests",
            "type": "directory",
            "is_directory": True,
            "size": None,
            "last_modified": datetime.now(timezone.utc).isoformat()
        },
        {
            "path": "requirements.txt",
            "name": "requirements.txt",
            "type": "file",
            "is_directory": False,
            "size": 256,
            "last_modified": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # 如果指定了路径，返回该路径下的文件
    if path:
        # 模拟子目录文件
        if path == "src":
            return [
                {
                    "path": "src/main.py",
                    "name": "main.py",
                    "type": "file",
                    "is_directory": False,
                    "size": 512,
                    "last_modified": datetime.now(timezone.utc).isoformat()
                },
                {
                    "path": "src/utils.py",
                    "name": "utils.py",
                    "type": "file",
                    "is_directory": False,
                    "size": 256,
                    "last_modified": datetime.now(timezone.utc).isoformat()
                }
            ]
        elif path == "tests":
            return [
                {
                    "path": "tests/test_main.py",
                    "name": "test_main.py",
                    "type": "file",
                    "is_directory": False,
                    "size": 384,
                    "last_modified": datetime.now(timezone.utc).isoformat()
                }
            ]
    
    return base_files


def get_repository_file_content(
    db: Session,
    practice_id: int,
    creator_id: int,
    file_path: str
):
    """获取代码仓库文件内容"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 检查代码仓库是否存在
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if not repo or not repo.is_enabled:
        return None
    
    # 模拟获取文件内容（实际项目中应该调用Git API）
    content = f"# {file_path}\n\n这是文件 {file_path} 的内容"
    
    return {
        "path": file_path,
        "content": content,
        "encoding": "utf-8",
        "size": len(content),
        "last_modified": datetime.now(timezone.utc).isoformat()
    }


def save_repository_file_content(
    db: Session,
    practice_id: int,
    creator_id: int,
    file_path: str,
    content: str
):
    """保存代码仓库文件内容"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 检查代码仓库是否存在
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if not repo or not repo.is_enabled:
        return None
    
    # 模拟保存文件内容（实际项目中应该调用Git API）
    return {
        "path": file_path,
        "size": len(content),
        "saved_at": datetime.now(timezone.utc).isoformat()
    }


def create_repository_file(
    db: Session,
    practice_id: int,
    creator_id: int,
    file_path: str,
    content: Optional[str] = None,
    is_directory: bool = False
):
    """创建代码仓库文件或目录"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 检查代码仓库是否存在
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if not repo or not repo.is_enabled:
        return None
    
    # 验证文件路径
    if not file_path or file_path.startswith('/') or '..' in file_path:
        return None
    
    # 模拟文件创建（实际项目中应该调用Git API）
    file_info = {
        "path": file_path,
        "name": file_path.split('/')[-1],
        "type": "directory" if is_directory else "file",
        "is_directory": is_directory,
        "size": len(content) if content else 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return file_info


def commit_repository_changes(
    db: Session,
    practice_id: int,
    creator_id: int,
    commit_type: str,
    file_paths: Optional[List[str]] = None,
    commit_message: str = "保存修改"
):
    """提交代码仓库修改"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 检查代码仓库是否存在
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id
    ).first()
    
    if not repo or not repo.is_enabled:
        return None
    
    # 验证提交类型
    if commit_type not in ["all", "current"]:
        return None
    
    # 模拟Git提交（实际项目中应该调用Git API）
    commit_hash = f"commit_{int(datetime.now().timestamp())}"
    
    return {
        "commit_hash": commit_hash,
        "commit_message": commit_message,
        "commit_type": commit_type,
        "committed_files": file_paths if commit_type == "current" else ["all"],
        "committed_at": datetime.now(timezone.utc).isoformat()
    }


def get_practice_datasets_list(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """获取实践数据集列表"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 获取数据集列表
    datasets = db.query(models.PracticeDataset).filter(
        models.PracticeDataset.practice_id == practice_id
    ).order_by(models.PracticeDataset.created_at.desc()).all()
    
    dataset_list = []
    for dataset in datasets:
        dataset_list.append({
            "id": dataset.id,
            "name": dataset.name,
            "file_type": dataset.file_type,
            "file_size": dataset.file_size,
            "file_size_display": format_file_size(dataset.file_size),
            "description": dataset.description,
            "file_url": dataset.file_url,
            "access_url": dataset.access_url or dataset.file_url,
            "created_at": dataset.created_at.isoformat(),
            "uploader_id": dataset.uploader_id
        })
    
    return {
        "datasets": dataset_list,
        "total": len(dataset_list)
    }


def upload_practice_dataset_file(
    db: Session,
    practice_id: int,
    dataset_data: dict,
    creator_id: int
):
    """上传实践数据集文件"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 验证文件大小（最大500MB）
    max_size = 500 * 1024 * 1024  # 500MB
    if dataset_data.get("file_size", 0) > max_size:
        raise ValueError("文件大小超过限制（最大500MB）")
    
    # 验证文件类型
    allowed_types = ['csv', 'json', 'txt', 'xlsx', 'zip', 'tar.gz', 'sql', 'xml']
    if dataset_data.get("file_type", "").lower() not in allowed_types:
        raise ValueError(f"不支持的文件类型，支持的类型：{', '.join(allowed_types)}")
    
    # 检查同名文件
    existing_dataset = db.query(models.PracticeDataset).filter(
        models.PracticeDataset.practice_id == practice_id,
        models.PracticeDataset.name == dataset_data["name"]
    ).first()
    
    if existing_dataset:
        raise ValueError("同名数据集已存在")
    
    # 生成访问地址
    access_url = f"/api/v1/practices/{practice_id}/datasets/files/{dataset_data['name']}"
    
    # 创建数据集记录
    new_dataset = models.PracticeDataset(
        practice_id=practice_id,
        name=dataset_data["name"],
        file_url=dataset_data["file_url"],
        file_type=dataset_data["file_type"],
        file_size=dataset_data["file_size"],
        description=dataset_data.get("description"),
        access_url=access_url,
        uploader_id=creator_id
    )
    
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    return new_dataset


def get_practice_dataset_by_id(
    db: Session,
    practice_id: int,
    dataset_id: int,
    creator_id: int
):
    """根据ID获取实践数据集"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return None
    
    # 获取数据集
    dataset = db.query(models.PracticeDataset).filter(
        models.PracticeDataset.id == dataset_id,
        models.PracticeDataset.practice_id == practice_id
    ).first()
    
    return dataset


def delete_practice_dataset_by_id(
    db: Session,
    practice_id: int,
    dataset_id: int,
    creator_id: int
):
    """删除实践数据集"""
    # 检查权限
    practice = get_custom_practice_detail(db, practice_id, creator_id)
    if not practice:
        return False
    
    # 删除数据集
    dataset = db.query(models.PracticeDataset).filter(
        models.PracticeDataset.id == dataset_id,
        models.PracticeDataset.practice_id == practice_id
    ).first()
    
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    
    return False


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示 — delegates to pure function"""
    return _format_file_size(size_bytes) 