#!/usr/bin/env python3
"""
实践资源初始化脚本

该脚本用于扫描 ziyuan/实践资源/ 目录下的所有项目文件夹，
解析 course_data.json 或 metadata.json 元数据文件，并将实践信息存储到数据库中。
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db, engine
from app.models import models as db_models

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingResourceSeeder:
    """实训资源初始化器"""
    
    def __init__(self, db: Session, resource_base_path: str = "ziyuan/实训资源"):
        """
        初始化实训资源初始化器
        
        Args:
            db: 数据库会话
            resource_base_path: 实训资源目录的基础路径
        """
        self.db = db
        self.resource_base_path = Path(resource_base_path)
        if not self.resource_base_path.exists():
            raise ValueError(f"实训资源目录不存在: {self.resource_base_path}")
    
    def scan_training_projects(self) -> List[Path]:
        """
        扫描实训资源目录，获取所有项目文件夹
        
        Returns:
            项目文件夹路径列表
        """
        projects = []
        
        # 遍历实训资源目录下的所有子目录
        for item in self.resource_base_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 检查是否包含 course_data.json 或 metadata.json 文件
                if (item / "course_data.json").exists() or (item / "metadata.json").exists():
                    projects.append(item)
                    logger.info(f"发现实训项目: {item.name}")
                else:
                    logger.warning(f"目录 {item.name} 缺少元数据文件 (course_data.json/metadata.json)，跳过")
        
        logger.info(f"共发现 {len(projects)} 个实训项目")
        return projects
    
    def parse_course_data(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """
        解析项目的 course_data.json 或 metadata.json 文件
        
        Args:
            project_path: 项目路径
            
        Returns:
            解析后的元数据字典，如果解析失败返回 None
        """
        # 优先查找 course_data.json，其次 metadata.json
        metadata_file = project_path / "course_data.json"
        if not metadata_file.exists():
            metadata_file = project_path / "metadata.json"
        
        try:
            with open(metadata_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 尝试修复可能的编码问题
                if not content.strip().startswith('{'):
                    logger.warning(f"元数据文件格式无效: {metadata_file}")
                    return None
                
                data = json.loads(content)
                
            # 添加项目路径信息
            data['project_path'] = str(project_path)
            data['project_name'] = project_path.name
            
            # 检查必要字段
            required_fields = ['title'] # intro/description can be optional if we have handbook
            for field in required_fields:
                if field not in data:
                    logger.error(f"项目 {project_path.name} 的元数据缺少必要字段: {field}")
                    # 使用默认值
                    if field == 'title':
                        data['title'] = project_path.name
            
            # 兼容 intro/description
            if 'description' in data and 'intro' not in data:
                data['intro'] = data['description']
            if 'intro' not in data:
                data['intro'] = f"实训项目: {project_path.name}"
            
            # 自动读取同目录下的 handbook.md
            handbook_file = project_path / "handbook.md"
            if handbook_file.exists():
                try:
                    with open(handbook_file, 'r', encoding='utf-8') as hf:
                        data['handbook_content'] = hf.read()
                        logger.info(f"  已读取手册内容: {handbook_file.name}")
                except Exception as e:
                    logger.warning(f"  读取手册失败: {e}")
            else:
                logger.info(f"  未找到手册文件: {handbook_file.name}")

            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 {metadata_file} 时出错: {e}")
            return None
        except Exception as e:
            logger.error(f"读取 {metadata_file} 时出错: {e}")
            return None
    
    def scan_project_files(self, project_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        扫描项目文件夹，收集数据集、SQL脚本和Jupyter笔记本信息
        
        Args:
            project_path: 项目路径
            metadata: 项目元数据
            
        Returns:
            包含文件信息的元数据
        """
        # 初始化文件列表
        metadata['datasets'] = []
        metadata['sql_scripts'] = []
        metadata['notebooks'] = []
        metadata['other_files'] = []
        
        # 定义要扫描的子目录
        scan_dirs = [
            project_path,  # 根目录
            project_path / "export" / "dataSet",
            project_path / "export" / "files",
            project_path / "export" / "jupyter",
            # 支持新的目录结构
            project_path / "sql_scripts",
            project_path / "bi_templates",
        ]
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
                
            for root, dirs, files in os.walk(scan_dir):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    # 跳过隐藏文件和元数据文件
                    if file.startswith('.') or file in ['course_data.json', 'metadata.json', 'handbook.md']:
                        continue
                    
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(project_path)
                    
                    file_info = {
                        'name': file,
                        'path': str(relative_path),
                        'size': file_path.stat().st_size
                    }
                    
                    # 根据文件扩展名分类
                    ext = file_path.suffix.lower()
                    
                    if ext in ['.csv', '.xlsx', '.xls', '.json', '.txt']:
                        metadata['datasets'].append(file_info)
                        logger.debug(f"  数据集: {relative_path}")
                    elif ext == '.sql':
                        metadata['sql_scripts'].append(file_info)
                        logger.debug(f"  SQL脚本: {relative_path}")
                    elif ext == '.ipynb':
                        metadata['notebooks'].append(file_info)
                        logger.debug(f"  Jupyter笔记本: {relative_path}")
                    else:
                        metadata['other_files'].append(file_info)
                        logger.debug(f"  其他文件: {relative_path}")
        
        # 统计信息
        logger.info(f"项目 {project_path.name} 文件统计:")
        logger.info(f"  - 数据集: {len(metadata['datasets'])} 个")
        logger.info(f"  - SQL脚本: {len(metadata['sql_scripts'])} 个")
        logger.info(f"  - Jupyter笔记本: {len(metadata['notebooks'])} 个")
        logger.info(f"  - 其他文件: {len(metadata['other_files'])} 个")
        
        return metadata
    
    def determine_training_type(self, metadata: Dict[str, Any]) -> str:
        """
        根据项目内容确定实训类型
        
        Args:
            metadata: 项目元数据
            
        Returns:
            实训类型: 'CODING' 或 'DRAG_DROP'
        """
        # 如果有 Jupyter 笔记本，则为编程式
        if metadata.get('notebooks'):
            return 'CODING'
        
        # 从元数据中获取类型
        training_type = metadata.get('course_type', metadata.get('training_type', ''))
        if 'coding' in training_type.lower() or '编程' in training_type:
            return 'CODING'
        
        # 默认为拖拽式
        return 'DRAG_DROP'
    
    def parse_difficulty(self, difficulty: str) -> str:
        """
        解析难度级别
        
        Args:
            difficulty: 原始难度字符串
            
        Returns:
            标准化的难度级别
        """
        difficulty_map = {
            'beginner': 'beginner',
            'easy': 'beginner',
            '初级': 'beginner',
            'middle': 'intermediate',
            'intermediate': 'intermediate',
            '中级': 'intermediate',
            'hard': 'advanced',
            'advanced': 'advanced',
            '高级': 'advanced'
        }
        return difficulty_map.get(difficulty.lower(), 'intermediate')
    
    def create_or_update_training(self, metadata: Dict[str, Any]) -> Optional[int]:
        """
        在数据库中创建或更新实训记录
        
        Args:
            metadata: 实训元数据
            
        Returns:
            创建或更新的实训ID，失败返回 None
        """
        try:
            # 检查是否已存在
            title = metadata.get('title', metadata['project_name'])
            existing = self.db.query(db_models.Training).filter(
                db_models.Training.title == title
            ).first()
            
            if existing:
                # 更新现有记录
                logger.info(f"更新现有实训: {title}")
                existing.intro = metadata.get('intro', metadata.get('description', ''))
                existing.training_type = self.determine_training_type(metadata)
                existing.difficulty = self.parse_difficulty(metadata.get('difficulty', 'intermediate'))
                existing.course_hours = metadata.get('course_hours', metadata.get('duration_time', 4))
                existing.tags = json.dumps(metadata.get('tags', []), ensure_ascii=False)
                existing.project_path = metadata['project_path']
                existing.handbook_content = metadata.get('handbook_content') # 更新手册内容
                existing.metadata = json.dumps({
                    'datasets': metadata.get('datasets', []),
                    'sql_scripts': metadata.get('sql_scripts', []),
                    'notebooks': metadata.get('notebooks', []),
                    'other_files': metadata.get('other_files', []),
                    'requirements': metadata.get('requirements', []),
                    'learning_objectives': metadata.get('learning_objectives', []),
                    'industry': metadata.get('industry', '通用')
                }, ensure_ascii=False)
                existing.updated_at = datetime.utcnow()
                
                self.db.commit()
                return existing.id
                
            else:
                # 创建新记录
                logger.info(f"创建新实训: {title}")
                new_training = db_models.Training(
                    title=title,
                    intro=metadata.get('intro', metadata.get('description', '')),
                    training_type=self.determine_training_type(metadata),
                    difficulty=self.parse_difficulty(metadata.get('difficulty', 'intermediate')),
                    course_hours=metadata.get('course_hours', metadata.get('duration_time', 4)),
                    tags=json.dumps(metadata.get('tags', []), ensure_ascii=False),
                    project_path=metadata['project_path'],
                    handbook_content=metadata.get('handbook_content'), # 设置手册内容
                    creator_id=1,  # 默认管理员ID
                    is_active=True,
                    is_preset=True,  # 平台预设实训
                    publish_status='PUBLISHED',
                    is_published=True,
                    published_at=datetime.utcnow(),
                    metadata=json.dumps({
                        'datasets': metadata.get('datasets', []),
                        'sql_scripts': metadata.get('sql_scripts', []),
                        'notebooks': metadata.get('notebooks', []),
                        'other_files': metadata.get('other_files', []),
                        'requirements': metadata.get('requirements', []),
                        'learning_objectives': metadata.get('learning_objectives', []),
                        'industry': metadata.get('industry', '通用')
                    }, ensure_ascii=False),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(new_training)
                self.db.commit()
                self.db.refresh(new_training)
                
                # 复制相关文件到上传目录
                self.copy_training_files(new_training.id, metadata)
                
                return new_training.id
                
        except Exception as e:
            logger.error(f"创建/更新实训时出错: {e}")
            self.db.rollback()
            return None
    
    def copy_training_files(self, training_id: int, metadata: Dict[str, Any]):
        """
        复制实训相关文件到上传目录
        
        Args:
            training_id: 实训ID
            metadata: 实训元数据
        """
        project_path = Path(metadata['project_path'])
        
        # 创建上传目录
        upload_base = Path("uploads/trainings") / str(training_id)
        upload_base.mkdir(parents=True, exist_ok=True)
        
        # 复制数据集文件
        datasets_dir = upload_base / "datasets"
        datasets_dir.mkdir(exist_ok=True)
        
        for dataset in metadata.get('datasets', []):
            src_file = project_path / dataset['path']
            if src_file.exists():
                dst_file = datasets_dir / dataset['name']
                shutil.copy2(src_file, dst_file)
                logger.debug(f"复制数据集: {dataset['name']}")
        
        # 复制SQL脚本
        sql_dir = upload_base / "sql"
        sql_dir.mkdir(exist_ok=True)
        
        for sql_script in metadata.get('sql_scripts', []):
            src_file = project_path / sql_script['path']
            if src_file.exists():
                dst_file = sql_dir / sql_script['name']
                shutil.copy2(src_file, dst_file)
                logger.debug(f"复制SQL脚本: {sql_script['name']}")
        
        # 复制Jupyter笔记本
        notebook_dir = upload_base / "notebooks"
        notebook_dir.mkdir(exist_ok=True)
        
        for notebook in metadata.get('notebooks', []):
            src_file = project_path / notebook['path']
            if src_file.exists():
                dst_file = notebook_dir / notebook['name']
                shutil.copy2(src_file, dst_file)
                logger.debug(f"复制Jupyter笔记本: {notebook['name']}")
    
    def seed_all(self) -> Dict[str, Any]:
        """
        执行完整的实训资源初始化流程
        
        Returns:
            初始化结果统计
        """
        stats = {
            'total_projects': 0,
            'successful': 0,
            'failed': 0,
            'updated': 0,
            'created': 0,
            'errors': []
        }
        
        # 扫描所有项目
        projects = self.scan_training_projects()
        stats['total_projects'] = len(projects)
        
        for project_path in projects:
            logger.info(f"\n处理项目: {project_path.name}")
            
            try:
                # 解析元数据
                metadata = self.parse_course_data(project_path)
                if not metadata:
                    stats['failed'] += 1
                    stats['errors'].append(f"{project_path.name}: 无法解析元数据文件")
                    continue
                
                # 扫描项目文件
                metadata = self.scan_project_files(project_path, metadata)
                
                # 创建或更新数据库记录
                training_id = self.create_or_update_training(metadata)
                if training_id:
                    stats['successful'] += 1
                    # 判断是创建还是更新
                    training = self.db.query(db_models.Training).filter(
                        db_models.Training.id == training_id
                    ).first()
                    if training and training.created_at == training.updated_at:
                        stats['created'] += 1
                    else:
                        stats['updated'] += 1
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"{project_path.name}: 数据库操作失败")
                    
            except Exception as e:
                logger.error(f"处理项目 {project_path.name} 时出错: {e}")
                stats['failed'] += 1
                stats['errors'].append(f"{project_path.name}: {str(e)}")
        
        return stats


def main():
    """主函数"""
    logger.info("开始初始化实训资源...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 确定资源路径
        # 假设当前脚本在 backend/app/utils/，资源在 backend/ziyuan/实训资源
        current_dir = Path(__file__).resolve().parent.parent.parent
        resource_path = current_dir / "ziyuan" / "实训资源"
        
        if not resource_path.exists():
             # 尝试相对路径 (如果是在 backend 根目录运行)
             resource_path = Path("ziyuan/实训资源")
        
        logger.info(f"资源路径: {resource_path.absolute()}")
        
        # 创建初始化器
        seeder = TrainingResourceSeeder(db, str(resource_path))
        
        # 执行初始化
        stats = seeder.seed_all()
        
        # 打印结果
        logger.info("\n初始化完成!")
        logger.info(f"总项目数: {stats['total_projects']}")
        logger.info(f"成功处理: {stats['successful']}")
        logger.info(f"  - 新创建: {stats['created']}")
        logger.info(f"  - 已更新: {stats['updated']}")
        logger.info(f"处理失败: {stats['failed']}")
        
        if stats['errors']:
            logger.error("\n错误详情:")
            for error in stats['errors']:
                logger.error(f"  - {error}")
        
        return stats
        
    except Exception as e:
        logger.error(f"初始化过程中出错: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 直接运行脚本
    results = main()
    print(f"\nSeeding results: {json.dumps(results, ensure_ascii=False, indent=2)}")
