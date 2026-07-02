"""
任务关卡编辑相关的CRUD操作
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
import app.models.models as models
import app.schemas.schemas as schemas
from datetime import datetime, timezone
import json
from app.utils.stage_validators import (
    validate_stage_fields as _validate_stage_fields,
    check_duplicate_skills as _check_duplicate_skills,
    STAGE_TEMPLATES as _STAGE_TEMPLATES,
    get_template_by_id as _get_template_by_id,
)
from app.utils.eval_helpers import normalize_test_case

def get_practice_stages(
    db: Session,
    practice_id: int,
    creator_id: int,
    skip: int = 0,
    limit: int = 20
):
    """获取实践的关卡列表"""
    # 验证权限
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None, 0
    
    query = db.query(models.Task).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).order_by(models.Task.order_in_practice)
    
    total = query.count()
    stages = query.offset(skip).limit(limit).all()
    
    return stages, total

def create_practice_stage_step1(
    db: Session,
    practice_id: int,
    stage_data: dict,
    creator_id: int
):
    """创建关卡 - 第一步：基本信息"""
    # 验证权限
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 验证技能标签在课程内唯一性
    existing_skills = db.query(models.Task).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).all()
    
    used_skills = set()
    for task in existing_skills:
        if task.skills:
            try:
                task_skills = json.loads(task.skills) if isinstance(task.skills, str) else task.skills
                used_skills.update(task_skills)
            except:
                pass
    
    new_skills = stage_data.get('skills', [])
    duplicate_skills = set(new_skills) & used_skills
    if duplicate_skills:
        raise ValueError(f"技能标签已存在：{', '.join(duplicate_skills)}")
    
    # 获取下一个排序号
    max_order = db.query(func.max(models.Task.order_in_practice)).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).scalar() or 0
    
    # 创建关卡
    stage = models.Task(
        practice_id=practice_id,
        title=stage_data['title'],
        task_type=stage_data['task_type'],
        order_in_practice=max_order + 1,
        difficulty=stage_data.get('difficulty', '初级'),
        skills=json.dumps(stage_data.get('skills', [])),
        handbook_markdown=stage_data.get('handbook_markdown', ''),
        coin=stage_data.get('coin', 0),
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(stage)
    db.commit()
    db.refresh(stage)
    
    return stage

def update_practice_stage_step2(
    db: Session,
    stage_id: int,
    settings_data: dict,
    creator_id: int
):
    """更新关卡 - 第二步：任务设置（实践题专用）"""
    # 验证权限
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    # 只有实践题才需要这些设置
    if stage.task_type != models.TaskTypeEnum.PRACTICE:
        return stage
    
    # 更新实践题设置
    stage.evaluation_timeout_seconds = settings_data.get('evaluation_timeout_seconds', 20)
    stage.student_task_file_paths = json.dumps(settings_data.get('student_task_file_paths', []))
    stage.evaluation_script_path = settings_data.get('evaluation_script_path')
    stage.evaluation_command = settings_data.get('evaluation_command')
    stage.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stage)
    
    return stage

def create_stage_test_cases(
    db: Session,
    stage_id: int,
    test_cases_data: List[dict],
    creator_id: int
):
    """创建关卡测试集"""
    # 验证权限
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    # 删除现有测试集
    db.query(models.TaskTest).filter(models.TaskTest.task_id == str(stage_id)).delete()
    
    # 创建新测试集
    test_cases = []
    for i, raw_data in enumerate(test_cases_data):
        tc = normalize_test_case(raw_data)
        test_case = models.TaskTest(
            task_id=str(stage_id),  # task_id 是 String 类型
            case_id=f"case-{stage_id}-{i+1}",  # 生成 case_id
            input_data=tc.get("input_data"),
            expected_output=tc.get("expected_output"),
            is_hidden=bool(tc.get("is_hidden", False)),
            match_rule=tc.get("match_rule", "EXACT_MATCH"),
            test_order=i  # 使用 test_order 而非 order_index
        )
        db.add(test_case)
        test_cases.append(test_case)
    
    db.commit()
    
    return test_cases

def update_practice_stage_step3(
    db: Session,
    stage_id: int,
    answer_data: dict,
    creator_id: int
):
    """更新关卡 - 第三步：参考答案"""
    # 验证权限
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    # 更新参考答案
    stage.answer_content_markdown = answer_data.get('answer_content_markdown', '')
    stage.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stage)
    
    return stage

def create_practice_stage_complete(
    db: Session,
    practice_id: int,
    stage_data: dict,
    creator_id: int
):
    """完整创建关卡（三步合一）"""
    try:
        # 第一步：创建基本信息
        stage = create_practice_stage_step1(
            db, practice_id, stage_data['task_info'], creator_id
        )
        if not stage:
            return None
        
        # 第二步：任务设置（实践题专用）
        if stage.task_type == models.TaskTypeEnum.PRACTICE and 'task_settings' in stage_data:
            update_practice_stage_step2(
                db, stage.id, stage_data['task_settings'], creator_id
            )
        
        # 创建测试集（实践题专用）
        if stage.task_type == models.TaskTypeEnum.PRACTICE and 'test_cases' in stage_data:
            create_stage_test_cases(
                db, stage.id, stage_data['test_cases'], creator_id
            )
        
        # 第三步：参考答案
        update_practice_stage_step3(
            db, stage.id, stage_data['answer_info'], creator_id
        )
        
        # 更新实践的任务数量
        update_practice_task_count(db, practice_id)
        
        return stage
        
    except Exception as e:
        db.rollback()
        raise e

def get_practice_stage_detail(
    db: Session,
    stage_id: int,
    creator_id: int
):
    """获取关卡详情 (教师视角): 通过 Practice.creator_id 校验创建者权限"""
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()

    if not stage:
        return None

    # 获取测试集
    test_cases = db.query(models.TaskTest).filter(
        models.TaskTest.task_id == stage_id
    ).order_by(models.TaskTest.test_order).all()

    # 对于题目类型的任务，解析题目数据
    if stage.task_type in [models.TaskTypeEnum.TRUE_FALSE, models.TaskTypeEnum.SINGLE_CHOICE, models.TaskTypeEnum.MULTIPLE_CHOICE]:
        if stage.student_task_file_paths:
            try:
                # 解析存储在student_task_file_paths中的题目数据
                question_data = json.loads(stage.student_task_file_paths)
                # 将题目数据添加到stage对象中，供API返回
                stage.question_data = question_data
            except json.JSONDecodeError as e:
                logger.warning(f"解析题目数据失败 task_id={stage_id}: {e}")

    return stage, test_cases


def get_stage_detail_for_student(
    db: Session,
    stage_id: int,
    user_id: int
):
    """获取关卡详情 (学生视角): 通过 classroom_courses + classroom_students 校验

    学生不是 Practice.creator, 因此不能用 creator_id 过滤. 改为校验:
    - task 所属 practice 已被布置进某课堂 (classroom_courses.practice_id = task.practice_id)
    - 学生在该课堂内 (classroom_students.student_id = user_id)
    - practice 已 PUBLISHED (避免学生看到草稿/未发布关卡 + test_cases 答案)
    任一条件 fail 返回 None.
    """
    stage = db.query(models.Task).join(
        models.Practice,
        models.Practice.id == models.Task.practice_id,
    ).join(
        models.ClassroomCourse,
        models.ClassroomCourse.practice_id == models.Task.practice_id,
    ).join(
        models.ClassroomStudent,
        models.ClassroomStudent.classroom_id == models.ClassroomCourse.classroom_id,
    ).filter(
        models.Task.id == stage_id,
        models.ClassroomStudent.student_id == user_id,
        models.Practice.publish_status == models.PracticePublishStatusEnum.PUBLISHED,
        models.Task.deleted_at.is_(None),
    ).first()

    if not stage:
        return None

    test_cases = db.query(models.TaskTest).filter(
        models.TaskTest.task_id == stage_id
    ).order_by(models.TaskTest.test_order).all()

    if stage.task_type in [models.TaskTypeEnum.TRUE_FALSE, models.TaskTypeEnum.SINGLE_CHOICE, models.TaskTypeEnum.MULTIPLE_CHOICE]:
        if stage.student_task_file_paths:
            try:
                question_data = json.loads(stage.student_task_file_paths)
                stage.question_data = question_data
            except json.JSONDecodeError as e:
                logger.warning(f"解析题目数据失败 task_id={stage_id}: {e}")

    return stage, test_cases

def update_practice_stage(
    db: Session,
    stage_id: int,
    update_data: dict,
    creator_id: int
):
    """更新关卡信息"""
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    # 验证技能标签唯一性（如果更新了技能标签）
    if 'skills' in update_data:
        existing_skills = db.query(models.Task).filter(
            models.Task.practice_id == stage.practice_id,
            models.Task.id != stage_id,
            models.Task.deleted_at.is_(None)
        ).all()
        
        used_skills = set()
        for task in existing_skills:
            if task.skills:
                try:
                    task_skills = json.loads(task.skills) if isinstance(task.skills, str) else task.skills
                    used_skills.update(task_skills)
                except:
                    pass
        
        new_skills = update_data['skills']
        duplicate_skills = set(new_skills) & used_skills
        if duplicate_skills:
            raise ValueError(f"技能标签已存在：{', '.join(duplicate_skills)}")
    
    # 更新字段
    for field, value in update_data.items():
        if field == 'skills':
            setattr(stage, field, json.dumps(value))
        elif field == 'student_task_file_paths':
            setattr(stage, field, json.dumps(value))
        elif hasattr(stage, field):
            setattr(stage, field, value)
    
    stage.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stage)
    
    return stage

def delete_practice_stage(
    db: Session,
    stage_id: int,
    creator_id: int
):
    """删除关卡（软删除）"""
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    # 软删除
    stage.deleted_at = datetime.now(timezone.utc)
    
    # 删除测试集
    db.query(models.TaskTest).filter(models.TaskTest.task_id == stage_id).delete()
    
    # 更新实践的任务数量
    update_practice_task_count(db, stage.practice_id)
    
    db.commit()
    
    return stage

def batch_delete_practice_stages(
    db: Session,
    stage_ids: List[int],
    creator_id: int
):
    """批量删除关卡"""
    stages = db.query(models.Task).join(models.Practice).filter(
        models.Task.id.in_(stage_ids),
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).all()
    
    if not stages:
        return []
    
    practice_ids = set()
    for stage in stages:
        stage.deleted_at = datetime.now(timezone.utc)
        practice_ids.add(stage.practice_id)
        
        # 删除测试集
        db.query(models.TaskTest).filter(models.TaskTest.task_id == stage.id).delete()
    
    # 更新实践的任务数量
    for practice_id in practice_ids:
        update_practice_task_count(db, practice_id)
    
    db.commit()
    
    return stages

def update_stage_order(
    db: Session,
    practice_id: int,
    stage_orders: List[dict],
    creator_id: int
):
    """更新关卡排序"""
    # 验证权限
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 更新排序
    for order_item in stage_orders:
        stage_id = order_item['stage_id']
        order_index = order_item['order_index']
        
        db.query(models.Task).filter(
            models.Task.id == stage_id,
            models.Task.practice_id == practice_id,
            models.Task.deleted_at.is_(None)
        ).update({
            'order_in_practice': order_index,
            'updated_at': datetime.now(timezone.utc)
        })
    
    db.commit()
    
    return True

def get_practice_code_repository_files(
    db: Session,
    practice_id: int,
    creator_id: int
):
    """获取实践代码仓库文件列表"""
    # 验证权限
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 获取代码仓库信息
    repo = db.query(models.PracticeCodeRepository).filter(
        models.PracticeCodeRepository.practice_id == practice_id,
        models.PracticeCodeRepository.is_enabled == True
    ).first()
    
    if not repo:
        return None
    
    # 这里应该调用Git API获取文件列表
    # 暂时返回模拟数据
    files = [
        {
            "file_path": "main.py",
            "file_name": "main.py",
            "file_type": "python",
            "is_directory": False,
            "size": 1024,
            "last_modified": datetime.now(timezone.utc)
        },
        {
            "file_path": "test.py",
            "file_name": "test.py", 
            "file_type": "python",
            "is_directory": False,
            "size": 512,
            "last_modified": datetime.now(timezone.utc)
        },
        {
            "file_path": "README.md",
            "file_name": "README.md",
            "file_type": "markdown",
            "is_directory": False,
            "size": 256,
            "last_modified": datetime.now(timezone.utc)
        }
    ]
    
    return {
        "repository_url": repo.repository_url,
        "branch_name": repo.branch_name,
        "files": files
    }

def validate_stage_data(
    db: Session,
    practice_id: int,
    stage_data: dict,
    creator_id: int,
    stage_id: Optional[int] = None
):
    """验证关卡数据（DB权限 + 纯字段校验委托给 stage_validators）"""
    errors = []
    warnings = []

    # 验证权限（DB-dependent）
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()

    if not practice:
        errors.append("实践不存在或无权限")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # 纯字段校验（委托给 pure function）
    field_errors, field_warnings = _validate_stage_fields(stage_data)
    errors.extend(field_errors)
    warnings.extend(field_warnings)

    # 验证技能标签唯一性（DB-dependent）
    skills = stage_data.get('task_info', {}).get('skills', [])
    if skills:
        existing_tasks = db.query(models.Task).filter(
            models.Task.practice_id == practice_id,
            models.Task.deleted_at.is_(None)
        )
        if stage_id:
            existing_tasks = existing_tasks.filter(models.Task.id != stage_id)
        existing_tasks = existing_tasks.all()

        existing_skills_sets = []
        for task in existing_tasks:
            if task.skills:
                try:
                    task_skills = json.loads(task.skills) if isinstance(task.skills, str) else task.skills
                    existing_skills_sets.append(task_skills)
                except:
                    pass

        duplicates = _check_duplicate_skills(skills, existing_skills_sets)
        if duplicates:
            errors.append(f"技能标签已存在：{', '.join(duplicates)}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def get_stage_templates(db: Session):
    """获取关卡模板列表（委托给 stage_validators 的纯数据）"""
    return list(_STAGE_TEMPLATES)

def apply_stage_template(
    db: Session,
    practice_id: int,
    template_id: str,
    customize_data: dict,
    creator_id: int
):
    """应用关卡模板"""
    template = _get_template_by_id(template_id)
    
    if not template:
        return None
    
    # 合并模板内容和自定义数据
    template_content = template['template_content'].copy()
    if customize_data:
        template_content.update(customize_data)
    
    # 构建关卡数据
    stage_data = {
        "task_info": {
            "title": customize_data.get('title', f"基于{template['name']}的关卡"),
            "difficulty": template['difficulty'],
            "skills": customize_data.get('skills', []),
            "handbook_markdown": template_content.get('handbook_markdown', ''),
            "task_type": template['task_type']
        },
        "answer_info": {
            "answer_title": "参考答案",
            "answer_content_markdown": customize_data.get('answer_content', '请填写参考答案...')
        }
    }
    
    # 添加实践题特有设置
    if template['task_type'] == 'PRACTICE':
        stage_data["task_settings"] = {
            "evaluation_timeout_seconds": 20,
            "student_task_file_paths": template_content.get('student_task_files', ['main.py']),
            "evaluation_script_path": template_content.get('evaluation_script_path', 'test.py'),
            "evaluation_command": template_content.get('evaluation_command', 'python3'),
            "enable_page_preview": False,
            "test_cases_visible": True,
            "match_rule": "EXACT_MATCH"
        }
        
        stage_data["test_cases"] = template_content.get('test_cases', [])
    
    # 添加选择题/判断题数据
    elif template['task_type'] in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'TRUE_FALSE']:
        question_data = template_content.get('question_data', {})
        stage_data["task_info"]["question_data"] = json.dumps(question_data)
    
    # 创建关卡
    return create_practice_stage_complete(db, practice_id, stage_data, creator_id)

def get_practice_stage_management_data(
    db: Session,
    practice_id: int,
    creator_id: int,
    allow_orphan: bool = False,
):
    """获取实践关卡管理页面数据

    allow_orphan=True 时, 同时放行 creator_id IS NULL 的 practice (Z3 P0-7 修).
    学校 21 个 practice creator_id 全 NULL — 教师/管理员视角下视为公共 practice 可编辑.
    """
    # 验证权限
    creator_filter = models.Practice.creator_id == creator_id
    if allow_orphan:
        from sqlalchemy import or_ as _or
        creator_filter = _or(models.Practice.creator_id == creator_id,
                             models.Practice.creator_id.is_(None))
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        creator_filter,
    ).first()

    if not practice:
        return None
    
    # 获取关卡列表
    stages = db.query(models.Task).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).order_by(models.Task.order_in_practice).all()
    
    # 计算总金币数
    total_coin = sum(stage.coin or 0 for stage in stages)
    
    return {
        "practice_info": {
            "id": practice.id,
            "title": practice.title,
            "description": practice.description,
            "difficulty": practice.difficulty.value if practice.difficulty else "beginner",
            "task_count": len(stages),
            "is_published": practice.is_published
        },
        "stages": stages,
        "total_coin": total_coin
    }

def update_practice_task_count(db: Session, practice_id: int):
    """更新实践的任务数量"""
    count = db.query(models.Task).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).count()
    
    db.query(models.Practice).filter(
        models.Practice.id == practice_id
    ).update({
        'task_count': count,
        'updated_at': datetime.now(timezone.utc)
    })
    
    db.commit()

# ==================== 判断题和选择题相关CRUD ====================

def create_question_stage_step2(
    db: Session,
    stage_id: int,
    question_settings: dict,
    creator_id: int
):
    """创建题目类型关卡 - 第二步：题目设置"""
    # 验证关卡存在且有权限
    stage = db.query(models.Task).filter(
        models.Task.id == stage_id,
        models.Task.practice.has(models.Practice.creator_id == creator_id)
    ).first()
    
    if not stage:
        return None
    
    # 验证关卡类型
    if stage.task_type not in [models.TaskTypeEnum.TRUE_FALSE, models.TaskTypeEnum.SINGLE_CHOICE, models.TaskTypeEnum.MULTIPLE_CHOICE]:
        raise ValueError("只有判断题和选择题关卡才能设置题目")
    
    # 构建题目数据
    question_data = {
        "question_type": question_settings["question_type"],
        "questions": []
    }
    
    # 处理题目列表
    for question in question_settings["questions"]:
        if question_settings["question_type"] == "judge":
            # 判断题
            question_item = {
                "question_id": question.get("question_id"),
                "question_content": question["question_content"],
                "correct_answer": question["correct_answer"],
                "explanation": question.get("explanation")
            }
        else:
            # 选择题
            question_item = {
                "question_id": question.get("question_id"),
                "question_content": question["question_content"],
                "question_type": question["question_type"],  # single/multiple
                "options": question["options"],
                "explanation": question.get("explanation")
            }
        
        question_data["questions"].append(question_item)
    
    # 更新关卡的题目数据
    stage.question_data = json.dumps(question_data, ensure_ascii=False)
    stage.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stage)
    
    return stage

def create_question_stage_complete(
    db: Session,
    practice_id: int,
    stage_data: dict,
    creator_id: int
):
    """完整创建题目类型关卡（三步合一）"""
    # 验证实践存在且有权限
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 第一步：创建基本信息
    task_info = stage_data["task_info"]
    
    # 根据题目类型确定task_type
    question_type = stage_data["question_settings"]["question_type"]
    if question_type == "judge":
        task_type = models.TaskTypeEnum.TRUE_FALSE
    elif question_type == "choice":
        # 根据第一个题目的类型确定是单选还是多选
        first_question = stage_data["question_settings"]["questions"][0]
        if first_question["question_type"] == "single":
            task_type = models.TaskTypeEnum.SINGLE_CHOICE
        else:
            task_type = models.TaskTypeEnum.MULTIPLE_CHOICE
    else:
        raise ValueError("不支持的题目类型")
    
    # 获取下一个排序号
    max_order = db.query(func.max(models.Task.order_in_practice)).filter(
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).scalar() or 0
    
    # 创建关卡
    stage = models.Task(
        practice_id=practice_id,
        title=task_info["title"],
        task_type=task_type,
        order_in_practice=max_order + 1,
        coin=task_info.get("coin", 0),
        difficulty=task_info.get("difficulty"),
        skills=json.dumps(task_info.get("skills", []), ensure_ascii=False),
        handbook_markdown=task_info.get("handbook_markdown"),
        answer_content_markdown=stage_data["answer_info"]["answer_content_markdown"],
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(stage)
    db.flush()  # 获取ID
    
    # 第二步：设置题目数据
    question_data = {
        "question_type": question_type,
        "questions": []
    }
    
    for question in stage_data["question_settings"]["questions"]:
        if question_type == "judge":
            question_item = {
                "question_id": question.get("question_id"),
                "question_content": question["question_content"],
                "correct_answer": question["correct_answer"],
                "explanation": question.get("explanation")
            }
        else:
            question_item = {
                "question_id": question.get("question_id"),
                "question_content": question["question_content"],
                "question_type": question["question_type"],
                "options": question["options"],
                "explanation": question.get("explanation")
            }
        
        question_data["questions"].append(question_item)
    
    stage.question_data = json.dumps(question_data, ensure_ascii=False)
    
    # 更新实践的任务数量
    practice.task_count = (practice.task_count or 0) + 1
    practice.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stage)
    
    return stage

def get_question_stage_data(
    db: Session,
    stage_id: int,
    creator_id: int
):
    """获取题目类型关卡的题目数据"""
    # 验证关卡存在且有权限
    stage = db.query(models.Task).filter(
        models.Task.id == stage_id,
        models.Task.practice.has(models.Practice.creator_id == creator_id)
    ).first()
    
    if not stage:
        return None
    
    # 解析题目数据
    if stage.question_data:
        try:
            question_data = json.loads(stage.question_data)
            return question_data
        except json.JSONDecodeError:
            return None
    
    return None

def update_question_stage_data(
    db: Session,
    stage_id: int,
    question_settings: dict,
    creator_id: int
):
    """更新题目类型关卡的题目数据"""
    # 验证关卡存在且有权限
    stage = db.query(models.Task).filter(
        models.Task.id == stage_id,
        models.Task.practice.has(models.Practice.creator_id == creator_id)
    ).first()
    
    if not stage:
        return None
    
    # 验证关卡类型
    if stage.task_type not in [models.TaskTypeEnum.TRUE_FALSE, models.TaskTypeEnum.SINGLE_CHOICE, models.TaskTypeEnum.MULTIPLE_CHOICE]:
        raise ValueError("只有判断题和选择题关卡才能设置题目")
    
    # 构建题目数据
    question_data = {
        "question_type": question_settings["question_type"],
        "questions": []
    }
    
    # 处理题目列表
    for question in question_settings["questions"]:
        if question_settings["question_type"] == "judge":
            question_item = {
                "question_id": question.get("question_id"),
                "question_content": question["question_content"],
                "correct_answer": question["correct_answer"],
                "explanation": question.get("explanation")
            }
        else:
            question_item = {
                "question_id": question.get("question_id"),
                "question_content": question["question_content"],
                "question_type": question["question_type"],
                "options": question["options"],
                "explanation": question.get("explanation")
            }
        
        question_data["questions"].append(question_item)
    
    # 更新关卡的题目数据
    stage.question_data = json.dumps(question_data, ensure_ascii=False)
    stage.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(stage)
    
    return stage

def validate_question_stage_data(
    db: Session,
    practice_id: int,
    stage_data: dict,
    creator_id: int,
    stage_id: Optional[int] = None
):
    """验证题目类型关卡数据"""
    errors = []
    warnings = []
    
    # 验证基本信息
    task_info = stage_data.get('task_info', {})
    if not task_info.get('title', '').strip():
        errors.append("关卡名称不能为空")
    
    if len(task_info.get('title', '')) > 60:
        errors.append("关卡名称不能超过60个字符")
    
    if len(task_info.get('skills', [])) > 5:
        errors.append("技能标签最多设置5个")
    
    # 验证题目设置
    question_settings = stage_data.get('question_settings', {})
    if not question_settings:
        errors.append("题目设置不能为空")
    else:
        question_type = question_settings.get('question_type')
        if question_type not in ['judge', 'choice']:
            errors.append("题目类型必须是judge或choice")
        
        questions = question_settings.get('questions', [])
        if not questions:
            errors.append("至少需要添加一道题目")
        elif len(questions) > 10:
            errors.append("题目数量不能超过10道")
        
        # 验证每道题目
        for i, question in enumerate(questions):
            if not question.get('question_content', '').strip():
                errors.append(f"第{i+1}题的题干不能为空")
            
            if question_type == 'judge':
                if question.get('correct_answer') not in ['true', 'false']:
                    errors.append(f"第{i+1}题的正确答案必须是true或false")
            elif question_type == 'choice':
                options = question.get('options', [])
                if len(options) < 2:
                    errors.append(f"第{i+1}题的选项数量不能少于2个")
                elif len(options) > 10:
                    errors.append(f"第{i+1}题的选项数量不能超过10个")
                
                # 检查正确答案
                correct_options = [opt for opt in options if opt.get('is_correct')]
                choice_type = question.get('question_type', 'single')
                
                if choice_type == 'single' and len(correct_options) != 1:
                    errors.append(f"第{i+1}题是单选题，必须有且仅有一个正确答案")
                elif choice_type == 'multiple' and len(correct_options) < 2:
                    errors.append(f"第{i+1}题是多选题，必须至少有2个正确答案")
    
    # 验证参考答案
    answer_info = stage_data.get('answer_info', {})
    if not answer_info.get('answer_title', '').strip():
        errors.append("答案标题不能为空")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def stage_sandbox_test(
    db: Session,
    stage_id: int,
    test_data: dict,
    creator_id: int
):
    """关卡沙盒测试（教师模拟学生做题）"""
    # 验证权限
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    test_mode = test_data.get('test_mode', 'teacher')
    
    # 根据题型进行不同的测试
    if stage.task_type == models.TaskTypeEnum.PRACTICE:
        return _test_practice_stage(db, stage, test_data, test_mode)
    elif stage.task_type in [models.TaskTypeEnum.SINGLE_CHOICE, models.TaskTypeEnum.MULTIPLE_CHOICE]:
        return _test_choice_stage(db, stage, test_data, test_mode)
    elif stage.task_type == models.TaskTypeEnum.TRUE_FALSE:
        return _test_judge_stage(db, stage, test_data, test_mode)
    else:
        return {
            "success": False,
            "error_message": f"不支持的题型: {stage.task_type}",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }

def _test_practice_stage(db: Session, stage: models.Task, test_data: dict, test_mode: str):
    """测试实践题关卡"""
    # 获取测试用例
    test_cases = db.query(models.TaskTest).filter(
        models.TaskTest.task_id == stage.id
    ).order_by(models.TaskTest.test_order).all()
    
    if not test_cases:
        return {
            "success": False,
            "error_message": "该关卡没有配置测试用例",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }
    
    # 模拟代码执行和测试
    code_content = test_data.get('code_content', '')
    file_contents = test_data.get('file_contents', {})
    
    if not code_content and not file_contents:
        return {
            "success": False,
            "error_message": "请提供代码内容或文件内容",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }
    
    # 模拟测试结果（实际项目中这里应该调用代码执行引擎）
    test_results = []
    passed_count = 0
    
    for i, test_case in enumerate(test_cases):
        # 模拟测试执行
        is_passed = True  # 简化处理，实际应该执行代码并比较输出
        
        test_result = {
            "test_case_id": test_case.id,
            "input_data": test_case.input_data if not test_case.is_hidden or test_mode == "teacher" else "***",
            "expected_output": test_case.expected_output if not test_case.is_hidden or test_mode == "teacher" else "***",
            "actual_output": test_case.expected_output if is_passed else "错误输出",
            "passed": is_passed,
            "execution_time": 50 + i * 10  # 模拟执行时间
        }
        
        test_results.append(test_result)
        if is_passed:
            passed_count += 1
    
    # 计算得分
    score = int((passed_count / len(test_cases)) * 100) if test_cases else 0
    
    return {
        "success": True,
        "score": score,
        "total_score": 100,
        "test_results": test_results,
        "execution_logs": f"执行了 {len(test_cases)} 个测试用例，通过 {passed_count} 个",
        "execution_time": sum(tr["execution_time"] for tr in test_results),
        "test_mode": test_mode,
        "tested_at": datetime.now(timezone.utc)
    }

def _test_choice_stage(db: Session, stage: models.Task, test_data: dict, test_mode: str):
    """测试选择题关卡"""
    if not stage.question_data:
        return {
            "success": False,
            "error_message": "该关卡没有配置题目数据",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }
    
    try:
        question_data = json.loads(stage.question_data)
    except:
        return {
            "success": False,
            "error_message": "题目数据格式错误",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }
    
    selected_options = test_data.get('selected_options', [])
    
    # 获取正确答案
    correct_options = []
    for option in question_data.get('options', []):
        if option.get('is_correct', False):
            correct_options.append(option.get('key', ''))
    
    # 判断答案是否正确
    is_correct = set(selected_options) == set(correct_options)
    score = 100 if is_correct else 0
    
    return {
        "success": True,
        "score": score,
        "total_score": 100,
        "correct_answer": ', '.join(correct_options) if test_mode == "teacher" else None,
        "is_correct": is_correct,
        "explanation": question_data.get('explanation', '') if test_mode == "teacher" else None,
        "test_mode": test_mode,
        "tested_at": datetime.now(timezone.utc)
    }

def _test_judge_stage(db: Session, stage: models.Task, test_data: dict, test_mode: str):
    """测试判断题关卡"""
    if not stage.question_data:
        return {
            "success": False,
            "error_message": "该关卡没有配置题目数据",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }
    
    try:
        question_data = json.loads(stage.question_data)
    except:
        return {
            "success": False,
            "error_message": "题目数据格式错误",
            "test_mode": test_mode,
            "tested_at": datetime.now(timezone.utc)
        }
    
    answer = test_data.get('answer', '').lower()
    correct_answer = question_data.get('correct_answer', '').lower()
    
    # 判断答案是否正确
    is_correct = answer == correct_answer
    score = 100 if is_correct else 0
    
    return {
        "success": True,
        "score": score,
        "total_score": 100,
        "correct_answer": correct_answer if test_mode == "teacher" else None,
        "is_correct": is_correct,
        "explanation": question_data.get('explanation', '') if test_mode == "teacher" else None,
        "test_mode": test_mode,
        "tested_at": datetime.now(timezone.utc)
    }

def validate_stage_deletion(
    db: Session,
    stage_id: int,
    creator_id: int
):
    """验证关卡是否可以删除"""
    # 验证权限
    stage = db.query(models.Task).join(models.Practice).filter(
        models.Task.id == stage_id,
        models.Practice.creator_id == creator_id,
        models.Task.deleted_at.is_(None)
    ).first()
    
    if not stage:
        return None
    
    # 检查该实践下还有多少关卡
    remaining_stages_count = db.query(models.Task).filter(
        models.Task.practice_id == stage.practice_id,
        models.Task.deleted_at.is_(None),
        models.Task.id != stage_id
    ).count()
    
    # 至少保留一关的验证
    can_delete = remaining_stages_count > 0
    reason = None if can_delete else "至少需要保留一个关卡，无法删除最后一个关卡"
    
    return {
        "can_delete": can_delete,
        "reason": reason,
        "remaining_stages_count": remaining_stages_count
    }

def delete_practice_stage_with_validation(
    db: Session,
    stage_id: int,
    creator_id: int
):
    """删除关卡（带验证）"""
    # 先验证是否可以删除
    validation_result = validate_stage_deletion(db, stage_id, creator_id)
    
    if not validation_result:
        return None
    
    if not validation_result["can_delete"]:
        raise ValueError(validation_result["reason"])
    
    # 执行删除
    return delete_practice_stage(db, stage_id, creator_id)

def update_stage_order_optimized(
    db: Session,
    practice_id: int,
    stage_orders: List[dict],
    creator_id: int
):
    """更新关卡排序（优化版）"""
    # 验证权限
    practice = db.query(models.Practice).filter(
        models.Practice.id == practice_id,
        models.Practice.creator_id == creator_id
    ).first()
    
    if not practice:
        return None
    
    # 验证所有关卡都属于该实践
    stage_ids = [item["stage_id"] for item in stage_orders]
    existing_stages = db.query(models.Task).filter(
        models.Task.id.in_(stage_ids),
        models.Task.practice_id == practice_id,
        models.Task.deleted_at.is_(None)
    ).all()
    
    if len(existing_stages) != len(stage_ids):
        raise ValueError("部分关卡不存在或不属于该实践")
    
    # 检查是否有顺序变化
    current_orders = {stage.id: stage.order_in_practice for stage in existing_stages}
    new_orders = {item["stage_id"]: item["order_index"] for item in stage_orders}
    
    has_changes = False
    for stage_id, new_order in new_orders.items():
        if current_orders.get(stage_id) != new_order:
            has_changes = True
            break
    
    if not has_changes:
        return {"updated_count": 0, "message": "排序未发生变化"}
    
    # 批量更新排序
    updated_count = 0
    for order_item in stage_orders:
        stage_id = order_item["stage_id"]
        order_index = order_item["order_index"]
        
        result = db.query(models.Task).filter(
            models.Task.id == stage_id,
            models.Task.practice_id == practice_id,
            models.Task.deleted_at.is_(None)
        ).update({
            'order_in_practice': order_index,
            'updated_at': datetime.now(timezone.utc)
        })
        
        updated_count += result

    db.commit()

    return {"updated_count": updated_count, "message": "排序更新成功"}


def check_student_passed_stage(db: Session, stage_id: int, student_id: int) -> bool:
    """
    检查学生是否已通过关卡

    Args:
        db: 数据库会话
        stage_id: 关卡ID
        student_id: 学生ID

    Returns:
        bool: True表示已通过，False表示未通过
    """
    # 查询学生对该关卡的提交记录
    submission = db.query(models.TaskSubmission).filter(
        models.TaskSubmission.task_id == stage_id,
        models.TaskSubmission.user_id == student_id,
        models.TaskSubmission.status == 'pass'
    ).first()

    return submission is not None


def get_student_stage_detail(
    db: Session,
    stage_id: int,
    student_id: int,
    include_answer: bool = False
) -> Optional[Dict]:
    """
    获取学生视角的关卡详情（根据通关状态决定是否返回参考答案）

    Args:
        db: 数据库会话
        stage_id: 关卡ID
        student_id: 学生ID
        include_answer: 是否包含参考答案（教师或已通关学生为True）

    Returns:
        Dict: 关卡详情，已通关包含参考答案，未通关不包含
    """
    # 获取关卡信息（不验证creator_id，因为学生也可以访问）
    stage = db.query(models.Task).filter(
        models.Task.id == stage_id,
        models.Task.deleted_at.is_(None)
    ).first()

    if not stage:
        return None

    # 获取测试集（不返回隐藏测试用例）
    test_cases = db.query(models.TaskTest).filter(
        models.TaskTest.task_id == stage_id,
        models.TaskTest.is_hidden == False
    ).order_by(models.TaskTest.test_order).all()

    # 构建响应数据
    stage_response = {
        'id': stage.id,
        'practice_id': stage.practice_id,
        'title': stage.title,
        'order_in_practice': stage.order_in_practice,
        'task_type': stage.task_type.value if hasattr(stage.task_type, 'value') else stage.task_type,
        'difficulty': stage.difficulty,
        'skills': stage.skills,
        'handbook_markdown': stage.handbook_markdown,
        'coin': stage.coin,
        'answer_title': None,
        'answer_content_markdown': None,
        'created_at': stage.created_at.isoformat() if stage.created_at else None,
    }

    # 检查学生是否已通过该关卡
    has_passed = check_student_passed_stage(db, stage_id, student_id)

    # 如果已通过或明确要求包含答案，返回参考答案
    if include_answer or has_passed:
        stage_response['answer_title'] = stage.answer_title
        stage_response['answer_content_markdown'] = stage.answer_content_markdown

    # 对于题目类型的任务，解析题目数据
    if stage.task_type in [models.TaskTypeEnum.TRUE_FALSE, models.TaskTypeEnum.SINGLE_CHOICE, models.TaskTypeEnum.MULTIPLE_CHOICE]:
        if stage.student_task_file_paths:
            try:
                question_data = json.loads(stage.student_task_file_paths)
                stage_response['question_data'] = question_data
            except json.JSONDecodeError as e:
                logger.warning(f"解析题目数据失败 task_id={stage_id}: {e}")

    # 返回测试用例数据
    test_case_list = []
    for tc in test_cases:
        test_case_list.append({
            'id': tc.id,
            'case_id': tc.case_id,
            'input_data': tc.input_data,
            'expected_output': tc.expected_output,
            'description': tc.description,
            'is_hidden': tc.is_hidden,
        })

    return {
        'stage': stage_response,
        'test_cases': test_case_list,
        'has_passed': has_passed,
    } 