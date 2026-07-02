"""
资源发现器和解析器
"""
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    ResourceManifest, PracticeMetadata, TrainingMetadata,
    ResourceType, FileDependency, ValidationError
)


class ResourceDiscoveryService:
    """资源发现服务"""

    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        self.base_path = Path(base_path)
        self.logger = logger or logging.getLogger(__name__)

        # 并发控制
        self.max_workers = 4
        self.discovery_timeout = 300  # 5分钟超时

    async def discover_resources(self) -> Dict[str, ResourceManifest]:
        """异步并发发现所有资源"""
        self.logger.info(f"开始发现资源，基础路径: {self.base_path}")

        # 验证基础路径
        if not self.base_path.exists():
            raise ValueError(f"基础路径不存在: {self.base_path}")

        tasks = []

        # 为不同类型的资源创建发现任务
        for resource_type_name, resource_type in [
            ("课程资源", ResourceType.PRACTICE),
            ("实训资源", ResourceType.TRAINING)
        ]:
            resource_path = self.base_path / resource_type_name
            if resource_path.exists() and resource_path.is_dir():
                tasks.append(self._discover_resource_type(resource_path, resource_type))

        # 并发执行发现任务
        self.logger.info(f"创建了 {len(tasks)} 个发现任务")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果和异常
        all_resources = {}
        for i, result in enumerate(results):
            resource_type_name = ["课程资源", "实训资源"][i]
            if isinstance(result, Exception):
                self.logger.error(f"发现 {resource_type_name} 时出错: {result}")
                continue

            all_resources.update(result)
            self.logger.info(f"发现 {resource_type_name}: {len(result)} 个资源")

        self.logger.info(f"资源发现完成，共发现 {len(all_resources)} 个资源")
        return all_resources

    async def _discover_resource_type(self, resource_path: Path,
                                    resource_type: ResourceType) -> Dict[str, ResourceManifest]:
        """发现特定类型的资源"""
        self.logger.debug(f"扫描目录: {resource_path}")

        resources = {}
        loop = asyncio.get_event_loop()

        # 使用线程池执行IO密集型操作
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 收集所有子目录
            subdirs = [item for item in resource_path.iterdir() if item.is_dir()]

            # 创建并发任务
            tasks = [
                loop.run_in_executor(executor, self._process_resource_dir, subdir, resource_type)
                for subdir in subdirs
            ]

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for subdir, result in zip(subdirs, results):
                if isinstance(result, Exception):
                    self.logger.warning(f"处理目录 {subdir.name} 失败: {result}")
                    continue

                if result:
                    resource_id = result.metadata.id
                    resources[resource_id] = result
                    self.logger.debug(f"发现资源: {resource_id} ({resource_type.value})")

        return resources

    def _process_resource_dir(self, resource_dir: Path,
                            resource_type: ResourceType) -> Optional[ResourceManifest]:
        """处理单个资源目录"""
        try:
            # 检查是否存在metadata.json
            metadata_file = resource_dir / "metadata.json"
            if not metadata_file.exists():
                return None

            # 解析metadata.json
            metadata = self._parse_metadata_file(metadata_file, resource_type)
            if not metadata:
                return None

            # 发现文件依赖
            files = self._discover_file_dependencies(resource_dir, metadata)

            # 获取最后修改时间
            last_modified = self._get_last_modified_time(resource_dir)

            # 创建资源清单
            manifest = ResourceManifest(
                metadata=metadata,
                base_path=str(resource_dir),
                files=files,
                last_modified=last_modified,
                discovered_at=datetime.now()
            )

            # 对于课程资源，根据metadata.json中的practices数组发现实践资源
            if resource_type == ResourceType.PRACTICE:
                self.logger.info(f"开始发现课程 {resource_dir.name} 的practices")
                practices = self._discover_practices_from_metadata(resource_dir, metadata)
                self.logger.info(f"发现 {len(practices) if practices else 0} 个practices")
                if practices:
                    # 将实践信息添加到manifest中
                    manifest.practices = practices
                    self.logger.info(f"已将 {len(practices)} 个practices添加到manifest")
                else:
                    self.logger.warning(f"未发现任何practices")

            return manifest

        except Exception as e:
            self.logger.error(f"处理资源目录 {resource_dir.name} 出错: {e}")
            return None

    def _discover_practices_from_metadata(self, course_dir: Path, course_metadata) -> List[Dict[str, Any]]:
        """根据课程metadata.json中的practices数组发现实践资源"""
        practices = []
        try:
            # 从课程metadata中获取practices路径列表
            practices_paths = getattr(course_metadata, 'practices', [])
            if not practices_paths:
                self.logger.warning(f"课程 {course_dir.name} 的metadata中没有practices数组")
                return practices

            self.logger.info(f"课程 {course_dir.name} 定义了 {len(practices_paths)} 个practices")

            for practice_path in practices_paths:
                try:
                    # 解析相对路径
                    practice_dir = course_dir / practice_path
                    if not practice_dir.exists() or not practice_dir.is_dir():
                        self.logger.warning(f"实践目录不存在: {practice_path}")
                        continue

                    self.logger.info(f"处理实践目录: {practice_dir.name}")
                    practice_data = self._process_practice_dir(practice_dir)
                    if practice_data:
                        practices.append(practice_data)
                        self.logger.info(f"成功处理实践: {practice_data.get('title')}")
                    else:
                        self.logger.warning(f"处理实践目录失败: {practice_dir.name}")

                except Exception as e:
                    self.logger.error(f"处理实践路径 {practice_path} 出错: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"发现课程 {course_dir.name} 中的实践出错: {e}")

        return practices

    def _process_practice_dir(self, practice_dir: Path) -> Optional[Dict[str, Any]]:
        """处理单个实践目录"""
        try:
            # 检查是否存在practice_metadata.json
            practice_metadata_file = practice_dir / "practice_metadata.json"
            if not practice_metadata_file.exists():
                self.logger.debug(f"实践目录 {practice_dir.name} 中没有practice_metadata.json，跳过")
                return None

            # 解析practice_metadata.json
            practice_data = self._parse_practice_metadata(practice_metadata_file)
            if not practice_data:
                return None

            # 设置父课程ID（稍后在同步时设置）
            practice_data['parent_course_id'] = None  # 占位符

            # 发现关卡（stages）- 从practice_metadata.json的stages数组获取
            tasks = self._discover_tasks_from_metadata(practice_dir, practice_data['stages'], practice_data)
            practice_data['tasks'] = tasks if tasks else []

            return practice_data

        except Exception as e:
            self.logger.error(f"处理实践目录 {practice_dir.name} 出错: {e}")
            return None

    def _parse_practice_metadata(self, metadata_file: Path) -> Optional[Dict[str, Any]]:
        """解析practice_metadata.json文件"""
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            practice_info = data.get('practice', {})
            gamification = data.get('gamification', {})
            structure = data.get('structure', {})

            # 提取实践基本信息
            practice_data = {
                'id': practice_info.get('id'),
                'title': practice_info.get('title'),
                'description': practice_info.get('description'),
                'summary': practice_info.get('summary'),
                'difficulty': practice_info.get('difficulty'),
                'direction': practice_info.get('direction'),
                'category': practice_info.get('category'),
                'coin': gamification.get('coin', 0),
                'task_count': gamification.get('task_count', 0),
                'stages': structure.get('stages', [])
            }

            return practice_data

        except Exception as e:
            self.logger.error(f"解析practice_metadata文件 {metadata_file} 出错: {e}")
            return None

    def _discover_tasks_from_metadata(self, practice_dir: Path, stages_metadata: List[Dict], practice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从practice_metadata.json的stages数组发现关卡"""
        tasks = []

        try:
            if not stages_metadata:
                self.logger.warning(f"实践 {practice_dir.name} 没有stages信息")
                return tasks

            self.logger.info(f"实践 {practice_dir.name} 定义了 {len(stages_metadata)} 个stages")

            for stage_info in stages_metadata:
                task_data = self._process_stage_from_metadata(practice_dir, stage_info, practice_data)
                if task_data:
                    tasks.append(task_data)
                    self.logger.debug(f"成功处理关卡: {task_data.get('title')}")

        except Exception as e:
            self.logger.error(f"发现实践关卡出错: {e}")

        return tasks

    def _process_stage_from_metadata(self, practice_dir: Path, stage_info: Dict, practice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从practice_metadata.json的stage信息处理关卡"""
        try:
            # 从stage信息中提取关卡数据
            stage_id = stage_info.get('stage_id')
            if not stage_id:
                self.logger.warning(f"关卡信息缺少stage_id: {stage_info}")
                return None

            # 检查对应的关卡目录是否存在
            folder_name = stage_info.get('folder', f"关卡{stage_info.get('order_index', 1)}")
            stage_dir = practice_dir / folder_name

            # 如果目录不存在，记录警告但仍创建关卡记录
            if not stage_dir.exists():
                self.logger.warning(f"关卡目录不存在: {folder_name}，将创建不完整的关卡记录")

            # 生成唯一的关卡ID：practice_id + stage_id
            practice_id = practice_data.get('id', 'unknown')
            unique_task_id = f"{practice_id}_{stage_id}"

            task_data = {
                'id': unique_task_id,  # 使用组合ID确保唯一性
                'title': stage_info.get('title', f'关卡{stage_info.get("order_index", 1)}'),
                'folder': folder_name,
                'order_index': stage_info.get('order_index', 0),
                'coin': stage_info.get('coin', 10),
                'estimated_time': stage_info.get('estimated_time', '15分钟'),
                'description': stage_info.get('description', ''),
                'difficulty': 'beginner',  # 从practice_metadata.json获取，或默认为beginner
                'task_type': 'PRACTICE',  # 枚举值
                'stage_dir_exists': stage_dir.exists() if stage_dir else False,
                'test_cases': stage_info.get('test_cases', []),  # 添加test_cases
                'evaluation_config': stage_info.get('evaluation_config', {})  # 添加evaluation_config
            }

            # 如果关卡目录存在，尝试读取额外的配置信息
            if stage_dir and stage_dir.exists():
                task_data['stage_dir_path'] = str(stage_dir)  # 添加目录路径用于测试用例导入
                
                # 从evaluation_config中提取路径信息
                eval_config = task_data.get('evaluation_config', {})
                if eval_config:
                    task_data['evaluation_script_path'] = str(stage_dir / eval_config.get('evaluation_script_path', ''))
                    task_data['student_task_file_paths'] = json.dumps(eval_config.get('student_task_file_paths', []))
                
                # 尝试读取handbook和answer文件
                handbook_path = stage_info.get('handbook_markdown_path')
                if handbook_path:
                    handbook_file = stage_dir / handbook_path
                    if handbook_file.exists():
                        try:
                            with open(handbook_file, 'r', encoding='utf-8') as f:
                                task_data['handbook_markdown'] = f.read()
                        except Exception as e:
                            self.logger.warning(f"读取handbook文件失败: {e}")

                task_config_file = stage_dir / "task_config.json"
                if task_config_file.exists():
                    try:
                        with open(task_config_file, 'r', encoding='utf-8') as f:
                            task_config = json.load(f)
                            # 可以合并task_config中的信息
                            task_data.update({
                                'evaluation_script_path': str(stage_dir / "test_evaluator.py"),
                                'student_task_file_paths': str(stage_dir / "student.py"),
                                'handbook_markdown': task_config.get('task', {}).get('description', '')
                            })
                    except Exception as e:
                        self.logger.warning(f"读取task_config.json失败: {e}")

            return task_data

        except Exception as e:
            self.logger.error(f"处理关卡metadata出错: {e}")
            return None

    def _parse_exam_files_sync(self, resource_dir: Path, metadata):
        """解析考试相关文件"""
        try:
            # 查找考试目录
            exam_dir = resource_dir / "04-考试评测"
            if not exam_dir.exists():
                return

            # 解析题库文件
            question_bank_file = exam_dir / "Python程序设计题库.json"
            if question_bank_file.exists():
                try:
                    with open(question_bank_file, 'r', encoding='utf-8') as f:
                        question_bank_data = json.load(f)
                        metadata.question_bank = question_bank_data.get('question_bank')
                        self.logger.info("成功解析题库文件")
                except Exception as e:
                    self.logger.warning(f"解析题库文件失败: {e}")

            # 解析考试配置
            exam_config_file = exam_dir / "考试配置.json"
            if exam_config_file.exists():
                try:
                    with open(exam_config_file, 'r', encoding='utf-8') as f:
                        exam_config_data = json.load(f)
                        metadata.exam_configurations = exam_config_data.get('exam_configurations')
                        self.logger.info("成功解析考试配置文件")
                except Exception as e:
                    self.logger.warning(f"解析考试配置文件失败: {e}")

        except Exception as e:
            self.logger.error(f"解析考试文件出错: {e}")

    def _parse_metadata_file(self, metadata_file: Path,
                           resource_type: ResourceType) -> Optional[Any]:
        """解析metadata.json文件"""
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 根据资源类型选择合适的模型
            if resource_type == ResourceType.PRACTICE:
                metadata = PracticeMetadata(**data)
            elif resource_type == ResourceType.TRAINING:
                metadata = TrainingMetadata(**data)
            else:
                raise ValueError(f"不支持的资源类型: {resource_type}")

            # 验证数据完整性
            self._validate_metadata(metadata, metadata_file.parent)

            # 计算并验证校验和
            if not metadata.validate_checksum():
                self.logger.warning(f"校验和验证失败: {metadata_file}")
                # 重新计算校验和
                metadata.checksum = metadata.calculate_checksum()

            # 尝试解析题库和考试配置（如果存在）
            self._parse_exam_files_sync(metadata_file.parent, metadata)

            return metadata

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误 {metadata_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析metadata文件出错 {metadata_file}: {e}")
            return None

    def _validate_metadata(self, metadata: Any, base_path: Path):
        """验证metadata的完整性"""
        # 检查必需的文件依赖
        missing_files = metadata.validate_file_dependencies(base_path)
        if missing_files:
            raise ValidationError(f"缺少必需的文件: {missing_files}")

        # 检查ID唯一性（在更高层级处理）
        # 这里可以添加其他业务规则验证

    def _discover_file_dependencies(self, resource_dir: Path, metadata: Any) -> Dict[str, FileDependency]:
        """发现文件依赖"""
        files = {}

        # 标准化文件路径映射
        path_mappings = {
            'handbook': metadata.handbook_content_path,
            'cover': metadata.cover_url_path,
        }

        # 添加类型特定的路径
        if hasattr(metadata, 'repo_template_path') and metadata.repo_template_path:
            path_mappings['repo'] = metadata.repo_template_path

        if hasattr(metadata, 'jupyter_notebooks_path') and metadata.jupyter_notebooks_path:
            path_mappings['jupyter'] = metadata.jupyter_notebooks_path

        if hasattr(metadata, 'datasets_path') and metadata.datasets_path:
            path_mappings['datasets'] = metadata.datasets_path

        # 检查每个路径
        for file_type, relative_path in path_mappings.items():
            if relative_path:
                full_path = resource_dir / relative_path
                file_type_enum = 'required' if file_type in ['handbook', 'cover'] else 'optional'

                files[relative_path] = FileDependency(
                    path=relative_path,
                    type=file_type_enum,
                    description=f"{file_type} file for {metadata.title}"
                )

        return files

    def _get_last_modified_time(self, resource_dir: Path) -> datetime:
        """获取目录的最后修改时间"""
        # 检查metadata.json的修改时间
        metadata_file = resource_dir / "metadata.json"
        if metadata_file.exists():
            return datetime.fromtimestamp(metadata_file.stat().st_mtime)

        # 如果没有metadata.json，使用目录的修改时间
        return datetime.fromtimestamp(resource_dir.stat().st_mtime)


class MetadataParser:
    """元数据解析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def parse_practice_metadata(self, data: Dict[str, Any]) -> PracticeMetadata:
        """解析实践元数据"""
        try:
            # 数据预处理和兼容性处理
            processed_data = self._preprocess_practice_data(data)
            metadata = PracticeMetadata(**processed_data)
            return metadata
        except Exception as e:
            self.logger.error(f"解析实践元数据失败: {e}")
            raise

    def parse_training_metadata(self, data: Dict[str, Any]) -> TrainingMetadata:
        """解析实训元数据"""
        try:
            # 数据预处理和兼容性处理
            processed_data = self._preprocess_training_data(data)
            metadata = TrainingMetadata(**processed_data)
            return metadata
        except Exception as e:
            self.logger.error(f"解析实训元数据失败: {e}")
            raise

    def _preprocess_practice_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理实践数据，确保兼容性"""
        processed = data.copy()

        # 处理旧版本字段映射
        if 'description' in processed and 'intro' not in processed:
            processed['intro'] = processed.pop('description')

        # 确保数组字段是列表
        array_fields = ['prerequisites', 'learning_objectives', 'tags']
        for field in array_fields:
            if field in processed and not isinstance(processed[field], list):
                processed[field] = [processed[field]] if processed[field] else []

        # 设置默认值
        defaults = {
            'schema_version': '1.0.0',
            'resource_type': 'practice',
            'require_experiment_report': True
        }

        for key, value in defaults.items():
            if key not in processed:
                processed[key] = value

        return processed

    def _preprocess_training_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理实训数据，确保兼容性"""
        processed = data.copy()

        # 处理旧版本字段映射
        if 'description' in processed and 'intro' not in processed:
            processed['intro'] = processed.pop('description')

        # 处理training_type字段
        if 'training_type' in processed:
            if processed['training_type'] == 'drag_and_drop':
                processed['training_type'] = 'drag_and_drop'
            elif processed['training_type'] == 'coding':
                processed['training_type'] = 'coding'
            else:
                # 尝试推断类型
                processed['training_type'] = self._infer_training_type(processed)

        # 确保数组字段是列表
        array_fields = ['prerequisites', 'learning_objectives', 'tags', 'assignment_nodes']
        for field in array_fields:
            if field in processed and not isinstance(processed[field], list):
                processed[field] = [processed[field]] if processed[field] else []

        # 设置默认值
        defaults = {
            'schema_version': '1.0.0',
            'resource_type': 'training',
            'require_experiment_report': True,
            'training_type': 'drag_and_drop'
        }

        for key, value in defaults.items():
            if key not in processed:
                processed[key] = value

        return processed

    def _infer_training_type(self, data: Dict[str, Any]) -> str:
        """推断实训类型"""
        # 基于文件路径或其他字段推断
        if 'jupyter_notebooks_path' in data or 'repo_template_path' in data:
            return 'coding'
        else:
            return 'drag_and_drop'
