#!/usr/bin/env python3
"""
实训数据库映射器
负责将AI生成的实训数据持久化到数据库，并集成对象存储
"""

import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.models import (
    Training, TrainingDataset, TrainingJupyterFile, TrainingAsset,
    TrainingTypeEnum, TrainingPublishStatusEnum, TrainingVisibilityEnum,
    DifficultyLevelEnum
)
from app.schemas.generation import (
    FullTrainingPackageResponse, FullTrainingManifest,
    TrainingDatabasePersistResult
)
from app.utils.object_storage import object_storage

logger = logging.getLogger(__name__)

def persist_training_package_to_db(
    db: Session,
    training_data: FullTrainingPackageResponse,
    manifest: FullTrainingManifest,
    parsed_files: Dict[str, Any],
    user_id: int
) -> TrainingDatabasePersistResult:
    """
    将AI生成的实训包数据持久化到数据库，并保存文件到对象存储
    
    Args:
        db: 数据库会话
        training_data: AI生成的实训数据
        manifest: 原始清单
        parsed_files: 解析后的文件数据
        user_id: 创建者用户ID
        
    Returns:
        数据库持久化结果
    """
    
    try:
        # 开始数据库事务
        metadata = training_data.metadata
        
        # 1. 映射实训类型
        training_type_map = {
            "拖拽式": TrainingTypeEnum.DRAG_DROP,
            "编码式": TrainingTypeEnum.CODING
        }
        training_type = training_type_map.get(metadata.training_type, TrainingTypeEnum.DRAG_DROP)
        
        # 2. 映射难度等级
        difficulty_map = {
            "初级": DifficultyLevelEnum.beginner,
            "中级": DifficultyLevelEnum.intermediate,
            "高级": DifficultyLevelEnum.advanced
        }
        difficulty = difficulty_map.get(metadata.difficulty, DifficultyLevelEnum.intermediate)
        
        # 3. 创建实训记录
        training = Training(
            title=metadata.training_name,
            training_type=training_type,
            intro=metadata.introduction,
            industry=metadata.industry,
            difficulty=difficulty,
            course_hours=metadata.duration_hours,
            handbook_content=training_data.handbook_markdown,
            assignment_nodes=json.dumps(metadata.homework_nodes, ensure_ascii=False),
            require_design_files=any(
                node.get("require_design_file", False) 
                for node in metadata.homework_nodes
            ),
            require_experiment_report=metadata.require_report,
            environment_id="python-3.9-standard" if training_type == TrainingTypeEnum.CODING else None,
            # 初始化对象存储字段
            bi_template_path=None,
            ai_template_path=None,
            template_files_manifest='{}',
            publish_status=TrainingPublishStatusEnum.EDITING,
            visibility=TrainingVisibilityEnum.PRIVATE,
            is_published=False,
            creator_id=user_id
        )
        
        db.add(training)
        db.flush()  # 获取training.id
        
        logger.info(f"创建实训记录，ID: {training.id}")
        
        # 4. 处理数据集文件（SQL文件）
        dataset_ids = []
        for form_field_name, file_info in parsed_files.items():
            if file_info['type'] in ['sql_schema', 'sql_data']:
                # 创建数据集记录
                dataset = TrainingDataset(
                    training_id=training.id,
                    name=file_info['filename'],
                    file_url=f"/api/v1/files/training-dataset/{training.id}/{file_info['filename']}",
                    file_type=file_info['type'],
                    file_size=len(file_info['content'].encode('utf-8')),
                    description=f"实训 {metadata.training_name} 的 {file_info['type']} 文件",
                    access_path=f"/datasets/{file_info['filename']}",
                    uploader_id=user_id
                )
                
                db.add(dataset)
                db.flush()
                dataset_ids.append(dataset.id)
                
                logger.info(f"创建数据集记录，ID: {dataset.id}")
        
        # 5. 处理Jupyter文件
        jupyter_file_ids = []
        # 检查是否有training_jupyter_files表（如果不存在则跳过）
        try:
            from app.models.models import TrainingJupyterFile
            
            for form_field_name, file_info in parsed_files.items():
                if file_info['type'] == 'jupyter_notebook':
                    jupyter_file = TrainingJupyterFile(
                        training_id=training.id,
                        file_name=file_info['filename'],
                        file_content=file_info['content']
                    )
                    
                    db.add(jupyter_file)
                    db.flush()
                    jupyter_file_ids.append(jupyter_file.id)
                    
                    logger.info(f"创建Jupyter文件记录，ID: {jupyter_file.id}")
                    
        except ImportError:
            logger.warning("TrainingJupyterFile模型不存在，跳过Jupyter文件持久化")
        
        # 6. 处理模板文件和支持性素材到对象存储
        storage_result = None
        asset_ids = []
        try:
            storage_result = object_storage.save_training_files(parsed_files, training.id)
            logger.info(f"对象存储保存完成: {storage_result['total_count']} 个文件")
            
            # 7. 处理保存到对象存储的文件，更新数据库记录
            if storage_result:
                all_stored_files = storage_result.get('assets', []) + storage_result.get('bi_templates', []) + storage_result.get('ai_templates', [])
                
                for stored_file in all_stored_files:
                    try:
                        original_filename = stored_file['original_filename']
                        if original_filename.endswith('.tpo'):
                            # 更新training表的bi_template_path
                            training.bi_template_path = stored_file['relative_path']
                            logger.info(f"更新BI模板路径: {stored_file['relative_path']}")
                        elif original_filename.endswith('.tapp'):
                            # 更新training表的ai_template_path
                            training.ai_template_path = stored_file['relative_path']
                            logger.info(f"更新AI模板路径: {stored_file['relative_path']}")
                        elif stored_file['category'] == 'assets':
                            # 创建支持性素材记录
                            asset = TrainingAsset(
                                training_id=training.id,
                                name=stored_file['original_filename'],
                                relative_path=stored_file['relative_path'],
                                file_type=stored_file.get('file_extension', 'application/octet-stream'),
                                file_size=stored_file['file_size'],
                                description=f"实训 {metadata.training_name} 的支持性素材",
                                uploader_id=user_id
                            )
                            
                            db.add(asset)
                            db.flush()
                            asset_ids.append(asset.id)
                            
                            logger.info(f"创建支持性素材记录，ID: {asset.id}")
                            
                    except Exception as e:
                        logger.warning(f"处理存储文件失败: {stored_file}, 错误: {str(e)}")
                
                # 8. 更新模板文件清单
                template_manifest = {}
                if training.bi_template_path:
                    template_manifest['bi_template'] = training.bi_template_path
                if training.ai_template_path:
                    template_manifest['ai_template'] = training.ai_template_path
                
                training.template_files_manifest = json.dumps(template_manifest, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"对象存储保存失败: {str(e)}")
            # 不影响主流程，继续执行
        
        # 提交事务
        db.commit()
        
        # 9. 构建返回结果
        result = TrainingDatabasePersistResult(
            success=True,
            message=f"实训包持久化成功：实训ID={training.id}, 数据集数量={len(dataset_ids)}, Jupyter文件数量={len(jupyter_file_ids)}, 素材数量={len(asset_ids)}",
            training_id=training.id,
            dataset_ids=dataset_ids,
            jupyter_file_ids=jupyter_file_ids,
            details={
                "training": {
                    "id": training.id,
                    "title": training.title,
                    "type": training.training_type.value,
                    "difficulty": training.difficulty.value,
                    "bi_template_path": training.bi_template_path,
                    "ai_template_path": training.ai_template_path
                },
                "datasets": [{"id": dataset_id} for dataset_id in dataset_ids],
                "jupyter_files": [{"id": file_id} for file_id in jupyter_file_ids],
                "assets": [{"id": asset_id} for asset_id in asset_ids],
                "storage": storage_result if storage_result else {
                    "total_count": 0,
                    "total_size": 0,
                    "message": "对象存储保存失败或无相关文件"
                }
            }
        )
        
        logger.info(f"实训包持久化成功: {result.message}")
        return result
        
    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败: {str(e)}")
        db.rollback()
        return TrainingDatabasePersistResult(
            success=False,
            message=f"数据库操作失败: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"实训包持久化失败: {str(e)}")
        db.rollback()
        return TrainingDatabasePersistResult(
            success=False,
            message=f"持久化失败: {str(e)}"
        )

def create_training_with_storage_urls(
    db: Session,
    training_id: int
) -> Dict[str, Any]:
    """
    为已创建的实训添加对象存储URL引用
    
    Args:
        db: 数据库会话
        training_id: 实训ID
        
    Returns:
        更新结果
    """
    try:
        training = db.query(Training).filter(Training.id == training_id).first()
        if not training:
            return {"success": False, "message": "实训不存在"}
        
        # 获取实训的对象存储文件
        storage_files = object_storage.list_training_files(training_id)
        
        if storage_files["total_count"] > 0:
            # 构建文件URL清单
            file_urls = {
                "templates": [],
                "assets": []
            }
            
            for file_info in storage_files["files"]:
                file_path = file_info["relative_path"]
                if "templates" in file_path:
                    file_urls["templates"].append(file_info["access_url"])
                elif "assets" in file_path:
                    file_urls["assets"].append(file_info["access_url"])
            
            # 这里可以扩展Training模型，添加storage_urls字段来存储这些URL
            # 由于当前模型没有这个字段，我们先返回统计信息
            
            logger.info(f"实训 {training_id} 的存储文件统计: {storage_files['total_count']} 个文件")
            
        return {
            "success": True,
            "message": f"实训存储信息更新完成",
            "storage_stats": storage_files
        }
        
    except Exception as e:
        logger.error(f"更新实训存储信息失败: training_id={training_id}, 错误: {str(e)}")
        return {"success": False, "message": f"更新失败: {str(e)}"}

def map_training_type(ai_type: str) -> TrainingTypeEnum:
    """映射AI生成的实训类型到数据库枚举"""
    type_map = {
        "拖拽式": TrainingTypeEnum.DRAG_DROP,
        "编码式": TrainingTypeEnum.CODING
    }
    return type_map.get(ai_type, TrainingTypeEnum.DRAG_DROP)

def map_difficulty_level(ai_difficulty: str) -> DifficultyLevelEnum:
    """映射AI生成的难度等级到数据库枚举"""
    difficulty_map = {
        "初级": DifficultyLevelEnum.beginner,
        "中级": DifficultyLevelEnum.intermediate,
        "高级": DifficultyLevelEnum.advanced
    }
    return difficulty_map.get(ai_difficulty, DifficultyLevelEnum.intermediate) 