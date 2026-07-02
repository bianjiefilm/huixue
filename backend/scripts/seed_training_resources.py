#!/usr/bin/env python3
"""
实训资源批量导入脚本
将 backend/ziyuan/实训资源/ 目录下的项目批量导入到数据库和对象存储中
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import mimetypes
from tqdm import tqdm

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import (
    Training, TrainingDataset, TrainingAsset,
    TrainingTypeEnum, TrainingPublishStatusEnum, 
    TrainingVisibilityEnum, DifficultyLevelEnum,
    User
)
from app.utils.object_storage import ObjectStorage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('seed_training_resources.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class TrainingResourceSeeder:
    """实训资源导入器"""
    
    def __init__(self, base_path: str = None):
        """
        初始化导入器
        
        Args:
            base_path: 实训资源根目录路径
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent / "ziyuan" / "实训资源"
        
        self.base_path = Path(base_path)
        self.storage = ObjectStorage()
        self.db = SessionLocal()
        self.default_user_id = self._get_default_user_id()
        
        # 行业映射（从course_data.json的category1字段）
        self.industry_mapping = {
            "e_commerce": "电子商务",
            "finance": "金融",
            "education": "教育",
            "healthcare": "医疗健康",
            "manufacturing": "制造业",
            "retail": "零售",
            "energy": "能源",
            "transportation": "交通运输",
        }
        
        # 难度映射
        self.difficulty_mapping = {
            "beginner": DifficultyLevelEnum.beginner,
            "middle": DifficultyLevelEnum.intermediate,
            "intermediate": DifficultyLevelEnum.intermediate,
            "advanced": DifficultyLevelEnum.advanced,
        }
        
        logger.info(f"初始化完成，资源目录: {self.base_path}")
    
    def _get_default_user_id(self) -> int:
        """获取默认用户ID（管理员用户）"""
        try:
            admin = self.db.query(User).filter(
                (User.username == "admin") | (User.is_superuser == True)
            ).first()
            
            if admin:
                return admin.id
            
            # 如果没有admin用户，获取第一个用户
            first_user = self.db.query(User).first()
            if first_user:
                return first_user.id
            
            # 创建默认管理员用户
            logger.warning("未找到用户，创建默认管理员用户")
            admin = User(
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
                is_active=True,
                is_superuser=True
            )
            self.db.add(admin)
            self.db.commit()
            return admin.id
            
        except Exception as e:
            logger.error(f"获取默认用户失败: {e}")
            return 1  # 返回默认ID
    
    def scan_projects(self) -> List[Path]:
        """扫描所有项目目录"""
        projects = []
        
        # 忽略的目录
        ignore_dirs = {"ai_generated", "templates", "datasets", "notebooks", "assets"}
        
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name not in ignore_dirs:
                # 检查是否包含course_data.json
                if (item / "course_data.json").exists():
                    projects.append(item)
                    logger.info(f"发现项目: {item.name}")
        
        logger.info(f"共发现 {len(projects)} 个项目")
        return sorted(projects)
    
    def parse_course_data(self, project_path: Path) -> Dict[str, Any]:
        """解析course_data.json文件"""
        course_data_path = project_path / "course_data.json"
        
        try:
            with open(course_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            project_info = data.get('project', {})
            
            # 提取关键信息
            result = {
                'title': project_info.get('name', project_path.name),
                'description': project_info.get('description', ''),
                'intro': project_info.get('description', ''),  # 简介使用description
                'industry': self.industry_mapping.get(
                    project_info.get('category1', ''), 
                    '其他'
                ),
                'difficulty': self.difficulty_mapping.get(
                    project_info.get('difficult', 'beginner'),
                    DifficultyLevelEnum.beginner
                ),
                'course_hours': project_info.get('durationTime', 8),
                'handbook': project_info.get('handbook', ''),  # 原始HTML内容
                'platform': project_info.get('platform', 'BI_design'),
                'course_type': project_info.get('courseType', 'training'),
                'data_supermarkets': data.get('dataSupermarkets', []),
                'data_source_list': data.get('dataSourceList', []),
            }
            
            logger.info(f"解析 {project_path.name} 的course_data.json成功")
            return result
            
        except Exception as e:
            logger.error(f"解析 {project_path.name} 的course_data.json失败: {e}")
            return {
                'title': project_path.name,
                'description': '',
                'intro': '',
                'industry': '其他',
                'difficulty': DifficultyLevelEnum.beginner,
                'course_hours': 8,
                'handbook': '',
                'platform': 'BI_design',
            }
    
    def upload_file_to_storage(self, file_path: Path, category: str, training_id: int) -> Optional[str]:
        """
        上传文件到对象存储
        
        Returns:
            相对路径
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            result = self.storage.save_file(
                file_content=file_content,
                filename=file_path.name,
                category=category,
                training_id=training_id
            )
            
            return result.get('relative_path')
            
        except Exception as e:
            logger.error(f"上传文件 {file_path} 失败: {e}")
            return None
    
    def process_datasets(self, project_path: Path, training: Training) -> List[TrainingDataset]:
        """处理数据集文件"""
        datasets = []
        
        # 检查dataSet目录
        dataset_dir = project_path / "export" / "dataSet"
        if dataset_dir.exists():
            for file_path in dataset_dir.glob("*"):
                if file_path.is_file():
                    logger.info(f"处理数据集文件: {file_path.name}")
                    
                    # 上传到对象存储
                    relative_path = self.upload_file_to_storage(
                        file_path, "datasets", training.id
                    )
                    
                    if relative_path:
                        # 确定文件类型
                        file_ext = file_path.suffix.lower()
                        file_type_map = {
                            '.csv': 'csv',
                            '.xlsx': 'excel',
                            '.xls': 'excel',
                            '.json': 'json',
                            '.sql': 'sql_data',
                        }
                        file_type = file_type_map.get(file_ext, 'other')
                        
                        dataset = TrainingDataset(
                            training_id=training.id,
                            name=file_path.stem,
                            file_url=f"/api/v1/storage/trainings/{training.id}/datasets/{file_path.name}",
                            relative_path=relative_path,
                            file_type=file_type,
                            file_size=file_path.stat().st_size,
                            description=f"数据集文件: {file_path.name}",
                            access_path=f"datasets/{file_path.name}",
                            uploader_id=self.default_user_id
                        )
                        datasets.append(dataset)
        
        # 检查SQL文件
        for sql_file in ['create.sql', 'insert.sql']:
            sql_path = project_path / sql_file
            if sql_path.exists():
                logger.info(f"处理SQL文件: {sql_file}")
                
                relative_path = self.upload_file_to_storage(
                    sql_path, "datasets", training.id
                )
                
                if relative_path:
                    file_type = 'sql_schema' if sql_file == 'create.sql' else 'sql_data'
                    
                    dataset = TrainingDataset(
                        training_id=training.id,
                        name=sql_path.stem,
                        file_url=f"/api/v1/storage/trainings/{training.id}/datasets/{sql_file}",
                        relative_path=relative_path,
                        file_type=file_type,
                        file_size=sql_path.stat().st_size,
                        description=f"SQL文件: {sql_file}",
                        access_path=f"sql/{sql_file}",
                        uploader_id=self.default_user_id
                    )
                    datasets.append(dataset)
        
        logger.info(f"共处理 {len(datasets)} 个数据集文件")
        return datasets
    
    def process_assets(self, project_path: Path, training: Training) -> List[TrainingAsset]:
        """处理素材文件（图片、视频等）"""
        assets = []
        
        # 检查files目录
        files_dir = project_path / "export" / "files"
        if files_dir.exists():
            for file_path in files_dir.glob("*"):
                if file_path.is_file():
                    # 获取MIME类型
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    if not mime_type:
                        mime_type = 'application/octet-stream'
                    
                    # 只处理图片和视频文件
                    if mime_type.startswith(('image/', 'video/')):
                        logger.info(f"处理素材文件: {file_path.name}")
                        
                        # 上传到对象存储
                        relative_path = self.upload_file_to_storage(
                            file_path, "assets", training.id
                        )
                        
                        if relative_path:
                            asset = TrainingAsset(
                                training_id=training.id,
                                name=file_path.stem,
                                relative_path=relative_path,
                                file_type=mime_type,
                                file_size=file_path.stat().st_size,
                                description=f"素材文件: {file_path.name}",
                                uploader_id=self.default_user_id
                            )
                            assets.append(asset)
        
        logger.info(f"共处理 {len(assets)} 个素材文件")
        return assets
    
    def import_project(self, project_path: Path) -> bool:
        """导入单个项目"""
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始导入项目: {project_path.name}")
            
            # 1. 解析course_data.json
            course_data = self.parse_course_data(project_path)
            
            # 2. 检查是否已存在同名实训
            existing = self.db.query(Training).filter(
                Training.title == course_data['title']
            ).first()
            
            if existing:
                logger.warning(f"实训 '{course_data['title']}' 已存在，跳过")
                return False
            
            # 3. 创建Training记录
            training = Training(
                title=course_data['title'],
                training_type=TrainingTypeEnum.DRAG_DROP if course_data['platform'] == 'BI_design' else TrainingTypeEnum.CODING,
                intro=course_data['intro'],
                industry=course_data['industry'],
                difficulty=course_data['difficulty'],
                course_hours=course_data['course_hours'],
                handbook_content=course_data['handbook'],  # 保存原始HTML内容
                assignment_nodes=json.dumps([]),  # 初始化为空数组
                require_design_files=False,
                require_experiment_report=False,
                publish_status=TrainingPublishStatusEnum.EDITING,  # 默认为编辑中状态
                visibility=TrainingVisibilityEnum.PRIVATE,  # 默认为私有
                creator_id=self.default_user_id
            )
            
            self.db.add(training)
            self.db.flush()  # 获取training.id但不提交事务
            
            logger.info(f"创建实训记录: ID={training.id}, 标题={training.title}")
            
            # 4. 处理数据集文件
            datasets = self.process_datasets(project_path, training)
            for dataset in datasets:
                self.db.add(dataset)
            
            # 5. 处理素材文件
            assets = self.process_assets(project_path, training)
            for asset in assets:
                self.db.add(asset)
            
            # 6. 提交事务
            self.db.commit()
            
            logger.info(f"✅ 成功导入项目: {project_path.name}")
            logger.info(f"   - 数据集: {len(datasets)} 个")
            logger.info(f"   - 素材: {len(assets)} 个")
            
            return True
            
        except Exception as e:
            logger.error(f"导入项目 {project_path.name} 失败: {e}")
            self.db.rollback()
            return False
    
    def run(self, specific_project: Optional[str] = None):
        """
        执行导入
        
        Args:
            specific_project: 指定要导入的项目名称，为None则导入所有项目
        """
        try:
            # 扫描项目
            projects = self.scan_projects()
            
            if specific_project:
                # 只导入指定项目
                projects = [p for p in projects if p.name == specific_project]
                if not projects:
                    logger.error(f"未找到项目: {specific_project}")
                    return
            
            # 统计信息
            total = len(projects)
            success = 0
            failed = 0
            
            # 使用进度条
            with tqdm(total=total, desc="导入进度") as pbar:
                for project_path in projects:
                    if self.import_project(project_path):
                        success += 1
                    else:
                        failed += 1
                    pbar.update(1)
            
            # 输出统计
            logger.info(f"\n{'='*50}")
            logger.info("导入完成！")
            logger.info(f"总计: {total} 个项目")
            logger.info(f"成功: {success} 个")
            logger.info(f"失败/跳过: {failed} 个")
            
        except Exception as e:
            logger.error(f"导入过程出错: {e}")
        finally:
            self.db.close()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='实训资源批量导入脚本')
    parser.add_argument(
        '--project',
        type=str,
        help='指定要导入的项目名称（目录名）'
    )
    parser.add_argument(
        '--path',
        type=str,
        help='指定实训资源目录路径'
    )
    
    args = parser.parse_args()
    
    # 创建导入器并执行
    seeder = TrainingResourceSeeder(base_path=args.path)
    seeder.run(specific_project=args.project)

if __name__ == "__main__":
    main()