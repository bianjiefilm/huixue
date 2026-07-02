"""
事务性执行器 - 实际执行数据库操作
"""
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import models
from app.core.database import get_db
from app.crud import crud

from .models import (
    SyncPlan, SyncAction, SyncResult, ResourceManifest,
    PracticeMetadata, TrainingMetadata, ResourceType, TrainingType, Difficulty
)


class TransactionalExecutor:
    """事务性执行器 - 简化版本"""

    def __init__(self, static_dir: str = "static/resources", logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.static_dir = Path(static_dir)
        self.file_manager = FileManager(static_dir, logger=self.logger)

    async def execute_plan(self, plan: SyncPlan) -> SyncResult:
        """执行同步计划 - 实际执行数据库操作"""
        result = SyncResult()
        result.total_actions = len(plan.actions)

        self.logger.info(f"开始执行同步计划，共 {len(plan.actions)} 个操作")

        db = None
        try:
            db = next(get_db())

            # 执行每个操作
            for action in plan.actions:
                try:
                    await self._execute_action(db, action)
                    result.add_success(action)
                    self.logger.debug(f"执行成功: {action.action_type} {action.resource_id}")

                except Exception as e:
                    result.add_error(action, str(e))
                    self.logger.error(f"执行失败 {action.action_type} {action.resource_id}: {e}")

            # 提交事务
            db.commit()
            result.success = True
            result.complete()
            self.logger.info(f"同步执行成功: {result.successful_actions}/{result.total_actions}")

        except Exception as e:
            # 回滚事务
            if db:
                db.rollback()
            result.success = False
            result.complete()
            self.logger.error(f"同步执行失败: {e}")

        finally:
            if db:
                db.close()

        return result

    async def _execute_action(self, db: Session, action: SyncAction):
        """执行单个操作"""
        self.logger.debug(f"执行: {action.action_type} 操作 for {action.resource_id}")

        if action.action_type == 'create':
            await self._create_resource(db, action)
        elif action.action_type == 'update':
            await self._update_resource(db, action)
        elif action.action_type == 'delete':
            await self._delete_resource(db, action)
        elif action.action_type == 'soft_delete':
            await self._soft_delete_resource(db, action)
        else:
            raise ValueError(f"不支持的操作类型: {action.action_type}")

    async def _create_resource(self, db: Session, action: SyncAction):
        """创建资源"""
        manifest = action.manifest

        if manifest.metadata.resource_type == ResourceType.PRACTICE:
            # 获取或创建课程记录
            course_obj = self._get_or_create_course_from_manifest(db, manifest)
            if not course_obj:
                self.logger.error(f"获取课程失败，跳过practices处理: {action.resource_id}")
                return

            course_id = course_obj.id
            self.logger.info(f"课程处理完成: {course_obj.title} (ID: {course_id})")

            # 处理课程中的practices
            self.logger.info(f"检查manifest.practices: {bool(manifest.practices)}")
            if manifest.practices:
                self.logger.info(f"发现 {len(manifest.practices)} 个practices")
                for practice_data in manifest.practices:
                    self.logger.info(f"处理practice: {practice_data.get('title')}")
                    # 设置父课程ID
                    practice_data['parent_course_id'] = course_id

                    # 创建Practice
                    practice_obj = self._create_practice(db, practice_data)
                    if practice_obj:
                        # 创建该practice的tasks
                        tasks_data = practice_data.get('tasks', [])
                        self.logger.info(f"practice {practice_obj.title} 有 {len(tasks_data)} 个tasks")
                        for task_data in tasks_data:
                            self._create_task(db, practice_obj.id, task_data)
            else:
                self.logger.warning(f"manifest.practices 为空")

            # 处理课程中的resources
            self._create_course_resources(db, course_obj, manifest.metadata.resources)

        elif manifest.metadata.resource_type == ResourceType.TRAINING:
            # 创建Training
            self.logger.info(f"创建实训资源: {action.resource_id}")
            training_obj = await self._create_training(db, manifest)
            if training_obj:
                self.logger.info(f"实训创建成功: {training_obj.title} (ID: {training_obj.id})")

        # 处理考试资源（题库和考试配置）
        if hasattr(manifest.metadata, 'question_bank') and manifest.metadata.question_bank:
            self._import_question_bank(db, manifest.metadata.question_bank, action.resource_id)

        if hasattr(manifest.metadata, 'exam_configurations') and manifest.metadata.exam_configurations:
            self._import_exam_configurations(db, manifest.metadata.exam_configurations, action.resource_id)

        # 处理文件
        await self.file_manager.process_files(action.resource_id, manifest)

    async def _update_resource(self, db: Session, action: SyncAction):
        """更新资源"""
        # 暂时实现为删除后重建
        await self._delete_resource(db, action)
        await self._create_resource(db, action)

    async def _delete_resource(self, db: Session, action: SyncAction):
        """删除资源"""
        manifest = action.manifest

        if manifest.metadata.resource_type == ResourceType.PRACTICE:
            # 删除Practice及其Tasks
            practice = db.query(models.Practice).filter(
                models.Practice.id == manifest.metadata.id
            ).first()
            if practice:
                db.delete(practice)

        # 删除文件
        await self.file_manager.delete_resource_files(action.resource_id)

    async def _soft_delete_resource(self, db: Session, action: SyncAction):
        """软删除资源"""
        # 暂时实现为硬删除
        await self._delete_resource(db, action)

    def _get_or_create_course_from_manifest(self, db: Session, manifest) -> Optional[models.Course]:
        """从manifest创建课程"""
        try:
            metadata = manifest.metadata

            # 检查是否已存在相同标题的课程
            existing_course = db.query(models.Course).filter(
                models.Course.title == metadata.title
            ).first()

            if existing_course:
                self.logger.info(f"课程已存在: {metadata.title} (ID: {existing_course.id})")
                # 返回已存在的课程，但仍然会继续处理practices
                return existing_course

            # 处理教学大纲：解析Markdown文件，替换相对链接为API URL
            teaching_syllabus_url = None
            if hasattr(metadata, 'handbook_content_path') and metadata.handbook_content_path:
                teaching_syllabus_url = self._process_teaching_syllabus(manifest, metadata)

            # 创建新课程
            course_data = {
                'title': metadata.title,
                'course_type': models.CourseTypeEnum.COURSE_MATERIAL,
                'description': metadata.intro,
                'difficulty': getattr(metadata, 'difficulty', 'INTERMEDIATE').upper(),
                'direction': getattr(metadata, 'direction', '编程'),
                'categories': json.dumps(getattr(metadata, 'tags', [])) if getattr(metadata, 'tags', []) else None,
                'practice_task_count': getattr(metadata, 'practice_task_count', 0),
                'outline_url': getattr(metadata, 'handbook_content_path', None),
                'teaching_syllabus': teaching_syllabus_url,  # 存储处理后的URL而不是内容
                'material_resources_count': getattr(metadata, 'material_resources_count', 0),
                'material_assessments_count': getattr(metadata, 'material_assessments_count', 0),
                'visibility': models.CourseVisibilityEnum.PUBLIC_PLATFORM,
            }

            course = models.Course(**course_data)
            db.add(course)
            db.flush()  # 获取ID

            self.logger.info(f"创建课程成功: {course.title} (ID: {course.id})")
            return course

        except Exception as e:
            self.logger.error(f"创建课程失败 {manifest.metadata.title}: {e}")
            return None

    def _create_practice(self, db: Session, practice_data: Dict[str, Any]) -> Optional[models.Practice]:
        """创建实践"""
        try:
            practice_obj = models.Practice(
                title=practice_data.get('title'),
                description=practice_data.get('description'),
                direction=practice_data.get('direction', '编程'),
                category=practice_data.get('category', '基础编程'),
                difficulty=practice_data.get('difficulty', 'beginner').lower(),
                parent_course_id=practice_data.get('parent_course_id'),
                summary=practice_data.get('summary'),
                coin=practice_data.get('coin', 0),
                task_count=practice_data.get('task_count', 0),
                intro=practice_data.get('intro'),
                practice_type='online_coding',
                visibility=models.PracticeVisibilityEnum.PUBLIC,
                publish_status=models.PracticePublishStatusEnum.PUBLISHED,
                is_published=True
            )

            db.add(practice_obj)
            db.flush()  # 获取ID
            self.logger.info(f"创建实践成功: {practice_obj.title} (ID: {practice_obj.id})")
            return practice_obj

        except Exception as e:
            self.logger.error(f"创建实践失败 {practice_data.get('title')}: {e}")
            return None

    def _create_task(self, db: Session, practice_id: int, task_data: Dict[str, Any]):
        """创建关卡"""
        try:
            # 创建Task对象
            task_obj = models.Task(
                id=task_data.get('id'),  # 使用metadata中的stage_id作为主键
                practice_id=practice_id,
                title=task_data.get('title'),
                task_type=models.TaskTypeEnum.PRACTICE,  # 使用枚举值
                order_in_practice=task_data.get('order_index', 0),
                coin=task_data.get('coin', 10),
                difficulty=task_data.get('difficulty', 'beginner'),
                handbook_markdown=task_data.get('handbook_markdown'),
                answer_content_markdown=task_data.get('answer_content_markdown'),
                evaluation_script_path=task_data.get('evaluation_script_path'),
                student_task_file_paths=task_data.get('student_task_file_paths'),
            )

            db.add(task_obj)
            db.flush()  # 获取task_id用于关联测试用例
            self.logger.debug(f"创建关卡成功: {task_obj.title} (ID: {task_obj.id}, 实践ID: {practice_id})")

            # 导入测试用例
            self._import_test_cases_for_task(db, task_obj, task_data)

        except Exception as e:
            self.logger.error(f"创建关卡失败 {task_data.get('title')}: {e}")
            raise

    def _import_test_cases_for_task(self, db: Session, task_obj: models.Task, task_data: Dict[str, Any]):
        """为任务导入测试用例"""
        try:
            # 优先从task_data中的test_cases导入（来自practice_metadata.json）
            test_cases = task_data.get('test_cases', [])
            
            if test_cases:
                # 从practice_metadata.json的test_cases导入
                for idx, test_case in enumerate(test_cases, start=1):
                    test_obj = models.TaskTest(
                        task_id=task_obj.id,
                        case_id=f"case_{task_obj.id}_{idx}",
                        input_data=test_case.get('input_data', ''),
                        expected_output=test_case.get('expected_output', ''),
                        is_hidden=test_case.get('is_hidden', False),
                        description=test_case.get('description', ''),
                        match_rule=test_case.get('match_rule', 'EXACT_MATCH'),
                        test_order=test_case.get('order_index', idx)
                    )
                    db.add(test_obj)
                
                self.logger.info(f"为关卡 {task_obj.title} 从metadata导入了 {len(test_cases)} 个测试用例")
                return
            
            # 如果没有test_cases，尝试从test_data.json文件导入
            stage_dir_path = task_data.get('stage_dir_path')
            if not stage_dir_path:
                # 从folder信息推断路径
                practice_dir = Path(task_obj.practice.parent_course.repo_template_path or "")
                if practice_dir.exists():
                    stage_dir = practice_dir / task_data.get('folder', '')
                    if stage_dir.exists():
                        stage_dir_path = str(stage_dir)

            if not stage_dir_path:
                self.logger.warning(f"无法找到关卡目录，跳过测试用例导入: {task_obj.title}")
                return

            test_data_file = Path(stage_dir_path) / "test_data.json"
            if not test_data_file.exists():
                self.logger.warning(f"测试数据文件不存在: {test_data_file}")
                return

            # 读取测试数据
            with open(test_data_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)

            # 导入公开测试用例
            visible_tests = test_data.get('visible_test_cases', [])
            for test_case in visible_tests:
                test_obj = models.TaskTest(
                    task_id=task_obj.id,
                    case_id=test_case.get('name', f"test_{len(visible_tests)}"),
                    input_data=json.dumps(test_case.get('input', {})),
                    expected_output=json.dumps(test_case.get('expected_output', {})),
                    is_hidden=False,
                    description=test_case.get('description', ''),
                    test_order=0  # 暂时设为0
                )
                db.add(test_obj)

            # 导入隐藏测试用例
            hidden_tests = test_data.get('hidden_test_cases', [])
            for test_case in hidden_tests:
                test_obj = models.TaskTest(
                    task_id=task_obj.id,
                    case_id=test_case.get('name', f"hidden_test_{len(hidden_tests)}"),
                    input_data=json.dumps(test_case.get('input', {})),
                    expected_output=json.dumps(test_case.get('expected_output', {})),
                    is_hidden=True,
                    description=test_case.get('description', ''),
                    test_order=0  # 暂时设为0
                )
                db.add(test_obj)

            total_tests = len(visible_tests) + len(hidden_tests)
            self.logger.info(f"为关卡 {task_obj.title} 导入了 {total_tests} 个测试用例 ({len(visible_tests)} 个公开, {len(hidden_tests)} 个隐藏)")

        except Exception as e:
            self.logger.error(f"导入测试用例失败 {task_obj.title}: {e}")
            # 不抛出异常，避免影响整个同步过程

    def _create_course_resources(self, db: Session, course_obj: models.Course, resources_data: List[Dict[str, Any]]):
        """为课程创建教学资源"""
        try:
            if not resources_data:
                self.logger.debug(f"课程 {course_obj.title} 没有教学资源")
                return

            self.logger.info(f"为课程 {course_obj.title} 创建 {len(resources_data)} 个教学资源")

            for resource_info in resources_data:
                try:
                    # 处理资源文件路径
                    resource_path = resource_info.get('path', '')
                    if not resource_path:
                        self.logger.warning(f"资源缺少路径信息: {resource_info}")
                        continue

                    # 构建完整的文件路径
                    full_resource_path = Path(course_obj.repo_template_path or "") / resource_path
                    if not full_resource_path.exists():
                        self.logger.warning(f"资源文件不存在: {full_resource_path}")
                        # 仍然创建记录，但标记为不可用
                        resource_url = None
                    else:
                        # 复制文件到静态资源目录并生成URL
                        resource_url = self._copy_resource_file(course_obj.id, full_resource_path)

                    # 创建CourseResource记录
                    resource_obj = models.CourseResource(
                        course_id=course_obj.id,
                        title=resource_info.get('title', '未命名资源'),
                        resource_type=resource_info.get('resource_type', 'UNKNOWN'),
                        url=resource_url or ''
                    )

                    db.add(resource_obj)
                    self.logger.debug(f"创建教学资源: {resource_obj.title}")

                except Exception as e:
                    self.logger.error(f"创建资源失败 {resource_info.get('title', 'unknown')}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"创建课程资源失败 {course_obj.title}: {e}")

    def _process_teaching_syllabus(self, manifest, metadata) -> Optional[str]:
        """处理教学大纲：解析Markdown文件，替换相对链接为API URL"""
        try:
            from pathlib import Path
            import re

            # 读取原始Markdown文件
            handbook_path = Path(manifest.base_path) / metadata.handbook_content_path
            if not handbook_path.exists():
                self.logger.warning(f"教学大纲文件不存在: {handbook_path}")
                return None

            with open(handbook_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 解析并替换相对链接
            processed_content = self._process_markdown_links(original_content, manifest, metadata)

            # 创建教学大纲目录
            syllabus_dir = Path(self.static_dir) / "syllabus"
            syllabus_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            syllabus_filename = f"{metadata.id}_teaching_syllabus.md"
            dest_path = syllabus_dir / syllabus_filename

            # 写入处理后的内容
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)

            # 生成API URL
            api_url = f"/api/v1/files/syllabus/{syllabus_filename}"

            self.logger.info(f"教学大纲处理完成: {handbook_path} -> {api_url}")
            return api_url

        except Exception as e:
            self.logger.error(f"处理教学大纲失败 {metadata.title}: {e}")
            return None

    def _process_markdown_links(self, content: str, manifest, metadata) -> str:
        """处理Markdown内容中的相对链接，替换为API URL"""
        import re

        def replace_link(match):
            """替换单个链接"""
            link_text = match.group(1)
            relative_path = match.group(2)

            try:
                # 处理教学大纲中的相对链接
                # relative_path现在是类似 "02-理论课件/xxx.pdf" 的格式
                resource_path = relative_path

                # 在metadata.resources中查找对应的资源配置
                resources = getattr(metadata, 'resources', [])

                for resource_info in resources:
                    resource_config_path = resource_info.get('path', '')

                    # 检查资源路径是否匹配（忽略扩展名差异）
                    resource_path_normalized = resource_path.replace('.pdf', '').replace('.docx', '').replace('.pptx', '')
                    resource_config_normalized = resource_config_path.replace('.pdf', '').replace('.docx', '').replace('.pptx', '')

                    if resource_path_normalized == resource_config_normalized:

                        # 找到匹配的资源，返回对应的API URL
                        # 使用ziyuan目录下的相对路径构建API URL
                        api_path = f"课程资源/{metadata.title}/{resource_config_path}"
                        return f"[{link_text}](/api/v1/files/teaching-resources/{api_path})"

                # 如果找不到匹配的资源，记录警告但保留原始链接
                self.logger.warning(f"无法解析教学大纲中的相对链接: {relative_path}")
                return match.group(0)

            except Exception as e:
                self.logger.warning(f"解析教学大纲链接失败 {relative_path}: {e}")
                return match.group(0)

        # 使用正则表达式替换Markdown链接
        # 匹配格式: [链接文本](../相对路径)
        pattern = r'\[([^\]]+)\]\(\.\./([^)]+)\)'
        processed_content = re.sub(pattern, replace_link, content)

        return processed_content

    def _copy_resource_file(self, course_id: int, source_path: Path) -> str:
        """复制资源文件到静态目录并返回URL"""
        try:
            # 创建课程资源目录
            course_resource_dir = self.static_dir / f"courses/{course_id}/resources"
            course_resource_dir.mkdir(parents=True, exist_ok=True)

            # 目标文件路径
            dest_path = course_resource_dir / source_path.name

            # 复制文件
            self._copy_file(source_path, dest_path)

            # 生成URL路径
            url_path = f"/static/resources/courses/{course_id}/resources/{source_path.name}"

            return url_path

        except Exception as e:
            self.logger.error(f"复制资源文件失败 {source_path}: {e}")
            raise

    def _import_question_bank(self, db: Session, question_bank_data: Dict[str, Any], course_id: str):
        """导入题库数据"""
        try:
            if not question_bank_data:
                return

            self.logger.info(f"为课程 {course_id} 导入题库数据")

            # 导入单选题
            single_choice_questions = question_bank_data.get('single_choice', [])
            for question_data in single_choice_questions:
                self._create_or_update_question(db, question_data, 'single_choice', course_id)

            # 导入多选题
            multiple_choice_questions = question_bank_data.get('multiple_choice', [])
            for question_data in multiple_choice_questions:
                self._create_or_update_question(db, question_data, 'multiple_choice', course_id)

            # 导入判断题
            true_false_questions = question_bank_data.get('true_false', [])
            for question_data in true_false_questions:
                self._create_or_update_question(db, question_data, 'true_false', course_id)

            self.logger.info(f"题库导入完成: {len(single_choice_questions)} 单选, {len(multiple_choice_questions)} 多选, {len(true_false_questions)} 判断")

        except Exception as e:
            self.logger.error(f"导入题库失败 {course_id}: {e}")

    def _import_exam_configurations(self, db: Session, exam_config_data: Dict[str, Any], course_id: str):
        """导入考试配置"""
        try:
            if not exam_config_data:
                return

            self.logger.info(f"为课程 {course_id} 导入考试配置")

            # 这里可以创建TestPaper记录，但暂时只记录日志
            # 实际的考试生成可以由教师端工具完成
            exam_types = exam_config_data.get('exam_types', {})
            for exam_type, config in exam_types.items():
                self.logger.info(f"考试类型 {exam_type}: {config.get('name')} - {config.get('question_count', {}).get('total', 0)} 题")

        except Exception as e:
            self.logger.error(f"导入考试配置失败 {course_id}: {e}")

    def _create_or_update_question(self, db: Session, question_data: Dict[str, Any], question_type: str, course_id: str):
        """创建或更新题目"""
        try:
            question_id = question_data.get('id')
            if not question_id:
                return

            # 检查题目是否已存在
            existing_question = db.query(models.Question).filter(
                models.Question.id == question_id
            ).first()

            if existing_question:
                # 更新现有题目
                existing_question.content = question_data.get('question', '')
                existing_question.options = json.dumps(question_data.get('options', {}))
                existing_question.correct_answers = json.dumps([question_data.get('correct_answer', '')])
                existing_question.explanation = question_data.get('explanation', '')
                existing_question.difficulty = getattr(models.DifficultyEnum, question_data.get('difficulty', '基础').upper(), models.DifficultyEnum.INTERMEDIATE)
                existing_question.direction = question_data.get('knowledge_point', '')
                existing_question.category = question_data.get('chapter', '')
            else:
                # 创建新题目
                question_obj = models.Question(
                    id=question_id,
                    content=question_data.get('question', ''),
                    question_type=getattr(models.QuestionTypeEnum, question_type.upper()),
                    options=json.dumps(question_data.get('options', {})),
                    correct_answers=json.dumps([question_data.get('correct_answer', '')]),
                    explanation=question_data.get('explanation', ''),
                    difficulty=getattr(models.DifficultyEnum, question_data.get('difficulty', '基础').upper(), models.DifficultyEnum.INTERMEDIATE),
                    direction=question_data.get('knowledge_point', ''),
                    category=question_data.get('chapter', ''),
                    is_shared=True
                )
                db.add(question_obj)

        except Exception as e:
            self.logger.error(f"创建/更新题目失败 {question_id}: {e}")

    async def _create_training(self, db: Session, manifest) -> Optional[models.Training]:
        """创建训练资源"""
        self.logger.info("_create_training method called")
        return None

    async def _create_training_datasets(self, db: Session, training_id: int, datasets: List[Dict], base_path: Path):
        """创建训练数据集"""
        for dataset in datasets:
            try:
                file_path = dataset.get('file_path')
                if not file_path:
                    continue

                full_path = base_path / file_path
                if not full_path.exists():
                    self.logger.warning(f"数据集文件不存在: {full_path}")
                    continue

                # 上传文件并获取URL
                file_url = await self._process_and_upload_file(
                    full_path, f"trainings/{training_id}/datasets/{full_path.name}"
                )

                # 创建数据集记录
                dataset_data = {
                    'training_id': training_id,
                    'name': dataset.get('name', full_path.name),
                    'file_url': file_url,
                    'relative_path': f"trainings/{training_id}/datasets/{full_path.name}",
                    'file_type': self._guess_file_type(full_path),
                    'file_size': full_path.stat().st_size if full_path.exists() else None,
                    'description': dataset.get('description'),
                    'access_path_in_env': dataset.get('access_path_in_env'),
                    'uploader_id': 1  # 默认用户
                }

                dataset_obj = models.TrainingDataset(**dataset_data)
                db.add(dataset_obj)

            except Exception as e:
                self.logger.error(f"创建数据集失败: {dataset}: {e}")

    async def _create_training_assets(self, db: Session, training_id: int, assets: List[Dict], base_path: Path):
        """创建训练资源文件"""
        for asset in assets:
            try:
                file_path = asset.get('file_path')
                if not file_path:
                    continue

                full_path = base_path / file_path
                if not full_path.exists():
                    self.logger.warning(f"资源文件不存在: {full_path}")
                    continue

                # 上传文件并获取URL
                relative_path = f"trainings/{training_id}/assets/{full_path.name}"
                file_url = await self._process_and_upload_file(full_path, relative_path)

                # 创建资源记录
                asset_data = {
                    'training_id': training_id,
                    'name': asset.get('name', full_path.name),
                    'relative_path': relative_path,
                    'file_type': self._guess_file_type(full_path),
                    'file_size': full_path.stat().st_size if full_path.exists() else None,
                    'description': asset.get('description'),
                    'asset_type': asset.get('type'),
                    'uploader_id': 1  # 默认用户
                }

                asset_obj = models.TrainingAsset(**asset_data)
                db.add(asset_obj)

            except Exception as e:
                self.logger.error(f"创建资源文件失败: {asset}: {e}")

    async def _process_and_upload_file(self, file_path: Path, relative_path: str) -> str:
        """处理并上传文件，返回URL"""
        # 暂时使用本地文件系统存储
        static_dir = Path(self.static_dir)
        target_path = static_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 复制文件
        import shutil
        shutil.copy2(file_path, target_path)

        # 返回本地URL路径
        return f"/static/{relative_path}"

    def _guess_file_type(self, file_path: Path) -> str:
        """根据文件扩展名猜测文件类型"""
        ext = file_path.suffix.lower()
        if ext in ['.sql']:
            return 'sql_schema'
        elif ext in ['.csv']:
            return 'csv'
        elif ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'image'
        elif ext in ['.pdf']:
            return 'pdf'
        elif ext in ['.tpo']:
            return 'bi_template'
        elif ext in ['.tapp']:
            return 'ai_model'
        else:
            return 'unknown'


class FileManager:
    """文件管理器"""

    def __init__(self, static_dir: str = "static/resources", logger: Optional[logging.Logger] = None):
        self.static_dir = Path(static_dir)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)

    async def process_files(self, resource_id: str, manifest: ResourceManifest):
        """处理资源文件"""
        try:
            resource_dir = self.static_dir / resource_id
            resource_dir.mkdir(exist_ok=True)

            # 复制必需的文件
            for file_dep in manifest.files.values():
                if file_dep.type == 'required':
                    await self._copy_file(
                        Path(manifest.base_path) / file_dep.path,
                        resource_dir / Path(file_dep.path).name
                    )

        except Exception as e:
            self.logger.error(f"处理资源文件失败 {resource_id}: {e}")
            raise

    async def _copy_file(self, src: Path, dst: Path):
        """异步复制文件"""
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        # 简单实现，使用线程池执行IO操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_copy_file, src, dst)

    def _sync_copy_file(self, src: Path, dst: Path):
        """同步复制文件"""
        import shutil
        shutil.copy2(src, dst)

    async def delete_resource_files(self, resource_id: str):
        """删除资源文件"""
        try:
            resource_dir = self.static_dir / resource_id
            if resource_dir.exists():
                import shutil
                # 使用线程池执行删除操作
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, shutil.rmtree, resource_dir)
        except Exception as e:
            self.logger.error(f"删除资源文件失败 {resource_id}: {e}")

