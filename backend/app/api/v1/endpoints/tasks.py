"""
任务管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
import json
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.core.auth import get_current_user, User as AuthUser  # P1-B/C: 真实身份从 token 解出
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

def _normalize_options(options: list) -> list:
    """
    标准化选项格式，支持 SSOT-P-v3.0 格式转换
    SSOT-P-v3.0 格式: [{"text": "选项A", "isCorrect": true}, ...]
    标准格式: ["选项A", "选项B", ...] 或 [{"text": "选项A"}, ...]
    """
    if not options:
        return []
    
    normalized = []
    for opt in options:
        if isinstance(opt, dict):
            # 如果是 SSOT-P-v3.0 格式，提取 text 字段
            if "text" in opt:
                normalized.append(opt["text"])
            elif "content" in opt:
                normalized.append(opt["content"])
            else:
                normalized.append(str(opt))
        else:
            normalized.append(str(opt))
    return normalized

# 创建路由器
router = APIRouter(
    tags=['tasks']
)

@router.get("/practices/{practice_id}/tasks", response_model=schemas.ApiResponse)
def get_practice_tasks(
    practice_id: int,
    user_id: Optional[int] = Query(None, description="用户ID，用于查询完成状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取实践的任务关卡列表"""
    try:
        # 检查实践是否存在
        practice = crud.get_practice(db, practice_id=practice_id)
        if practice is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        tasks, total = crud.get_practice_tasks(
            db=db,
            practice_id=practice_id,
            skip=skip,
            limit=page_size
        )
        
        # 如果提供了user_id，查询用户的任务完成状态
        user_task_status = {}
        if user_id:
            # 查询该用户所有已通过的任务
            completed_results = db.query(db_models.TaskEvaluationResult).filter(
                db_models.TaskEvaluationResult.user_id == user_id,
                db_models.TaskEvaluationResult.status == "pass"
            ).all()
            for result in completed_results:
                user_task_status[result.task_id] = {
                    "is_completed": True,
                    "score": result.score,
                    "passed_tests": result.passed_tests,
                    "total_tests": result.total_tests,
                    "completed_at": result.created_at.isoformat() if result.created_at else None
                }
        
        # 映射环境类型（支持大写和小写）
        env_type_mapping = {
            "CODING_ONLINE": "code",
            "HTML_PREVIEW": "html",
            "COMMAND_LINE": "shell",
            "CLOUD_DESKTOP": "desktop",
            "code": "code",
            "html": "html",
            "shell": "shell",
            "desktop": "desktop",
            "jupyter": "jupyter"
        }

        # 计算解锁状态逻辑
        # 1. 获取配置 - 使用 Practice 模型的 allow_skip_levels 字段
        allow_skip = practice.allow_skip_levels if practice.allow_skip_levels is not None else True  # 默认为 True (允许跳过)
        
        # 2. 如果不允许跳过，计算已完成的最大关卡顺序
        max_passed_order = 0
        if not allow_skip and user_id:
            from sqlalchemy import func
            # 查询该用户在该实践中已完成任务的最大顺序号
            max_passed_order = db.query(func.max(db_models.Task.order_in_practice)).join(
                db_models.TaskEvaluationResult, 
                db_models.TaskEvaluationResult.task_id == db_models.Task.id
            ).filter(
                db_models.Task.practice_id == practice_id,
                db_models.TaskEvaluationResult.user_id == user_id,
                db_models.TaskEvaluationResult.status == 'pass'
            ).scalar() or 0

        task_list = []
        for task in tasks:
            # 获取该任务的完成状态
            task_status = user_task_status.get(task.id, {
                "is_completed": False,
                "score": 0,
                "passed_tests": 0,
                "total_tests": 0,
                "completed_at": None
            })
            
            # 计算锁定状态
            is_locked = False
            if not allow_skip:
                # 逻辑：如果当前任务顺序 > (已完成最大顺序 + 1)，则锁定
                # 即：只能玩已完成的任务，或者下一个未完成的任务
                # 例如：已完成 1, 2 (max=2)。任务 3 (3 <= 2+1) 解锁。任务 4 (4 > 3) 锁定。
                # 特例：第一关 (order=1) 总是解锁 (1 <= 0+1)
                if (task.order_in_practice or 0) > max_passed_order + 1:
                    is_locked = True
            
            # 手动创建响应数据，应用环境类型映射
            task_dict = {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type,
                "order_in_practice": task.order_in_practice,
                "coin": task.coin,
                "env_type": task.env_type,
                "envType": env_type_mapping.get(task.env_type, "code"),  # 添加映射后的envType
                "difficulty": task.difficulty,
                "skills": task.skills,
                "practice_id": task.practice_id,
                "handbook_markdown": task.handbook_markdown,
                "answer_content_markdown": task.answer_content_markdown,
                "evaluation_script_path": task.evaluation_script_path,
                "evaluation_command": task.evaluation_command,
                "evaluation_timeout_seconds": task.evaluation_timeout_seconds,
                "student_task_file_paths": task.student_task_file_paths,
                "question_data": task.question_data,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "deleted_at": task.deleted_at,
                # 添加完成状态字段
                "is_completed": task_status["is_completed"],
                "completion_score": task_status["score"],
                "passed_tests": task_status["passed_tests"],
                "total_tests": task_status["total_tests"],
                "completed_at": task_status["completed_at"],
                # 添加锁定状态
                "isLocked": is_locked
            }
            task_list.append(task_dict)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": task_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 课堂管理

@router.get("/tasks/{task_id}", response_model=schemas.ApiResponse)
def get_task_detail(
    task_id: str, 
    user_id: Optional[int] = Query(None, description="用户ID，用于获取完成状态"),
    db: Session = Depends(get_db)
):
    """返回单个关卡的元信息、任务手册、测试集概览与当前学习状态"""
    try:
        task = crud.get_task_detail(db, task_id=task_id, user_id=user_id)
        if task is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取任务手册
        handbook = crud.get_task_handbook(db, task_id=task_id)
        
        # 获取测试集数量
        tests = crud.get_task_tests(db, task_id=task_id)
        
        # 映射环境类型（支持大写和小写）
        env_type_mapping = {
            "CODING_ONLINE": "code",
            "HTML_PREVIEW": "html", 
            "COMMAND_LINE": "shell",
            "CLOUD_DESKTOP": "desktop",
            # 小写版本（兼容数据库直接存储的小写值）
            "code": "code",
            "html": "html",
            "shell": "shell",
            "desktop": "desktop",
            "jupyter": "jupyter"
        }
        
        # 映射状态
        status_mapping = {
            "未开始": "not_started",
            "进行中": "in_progress", 
            "已完成": "passed"
        }
        
        # 为题目类型的任务添加额外数据
        extra_data = {}
        if task.task_type in [db_models.TaskTypeEnum.TRUE_FALSE, db_models.TaskTypeEnum.SINGLE_CHOICE, db_models.TaskTypeEnum.MULTIPLE_CHOICE]:
            # 优先从 question_data 字段读取，兼容旧数据从 student_task_file_paths 读取
            question_json = task.question_data or task.student_task_file_paths
            if question_json:
                try:
                    question_data = json.loads(question_json)
                    # 支持三种数据格式：
                    # 1. 直接的题目数组 [{...}, {...}] (SSOT-P-v3.0格式)
                    # 2. 包含 questions 键的对象 {"questions": [{...}, {...}]}
                    # 3. 单个题目对象 {...}
                    
                    questions = None
                    if isinstance(question_data, list):
                        # 格式1: 直接的题目数组 (SSOT-P-v3.0格式)
                        questions = question_data
                    elif isinstance(question_data, dict):
                        if "questions" in question_data and question_data["questions"]:
                            # 格式2: 包含 questions 键的对象
                            questions = question_data["questions"]
                        else:
                            # 格式3: 单个题目对象
                            questions = [question_data]
                    
                    if questions:
                        # 返回所有题目，兼容 SSOT-P-v3.0 格式 (stem/choiceType/isCorrect)
                        extra_data = {
                            "taskType": task.task_type.value,
                            "questions": [
                                {
                                    "id": q.get("id", f"q{i+1}"),
                                    "type": q.get("type", q.get("choiceType", "single")),
                                    "question": q.get("content", q.get("stem", "")),
                                    "options": _normalize_options(q.get("options", [])),
                                    "correctAnswer": q.get("correctAnswer", q.get("correct_answer", q.get("isCorrect", ""))),
                                    "explanation": q.get("explanation", "")
                                }
                                for i, q in enumerate(questions)
                            ],
                            # 兼容旧代码：第一道题的数据
                            "question": questions[0].get("content", questions[0].get("stem", "")) if questions else "",
                            "options": _normalize_options(questions[0].get("options", [])) if questions else [],
                            "correctAnswer": questions[0].get("correctAnswer", questions[0].get("correct_answer", questions[0].get("isCorrect", ""))) if questions else "",
                            "explanation": questions[0].get("explanation", "") if questions else ""
                        }
                    else:
                        extra_data = {"taskType": task.task_type.value}
                except json.JSONDecodeError as e:
                    logger.warning(f"解析题目数据失败 task_id={task_id}: {e}")
            else:
                # 即使没有question数据，也返回taskType
                extra_data = {"taskType": task.task_type.value}

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "taskId": task.id,
                "title": task.title,
                "coin": task.coin,
                "difficulty": task.difficulty.lower() if task.difficulty else "intermediate",
                "envType": env_type_mapping.get(task.env_type, "code"),
                "handbookMd": handbook.get("markdown", "") if handbook else "",
                "status": status_mapping.get(getattr(task, 'status', '未开始'), "not_started"),
                "skills": task.skills or [],
                "tests": len(tests),
                **extra_data
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.2 列出测试集

@router.get("/tasks/{task_id}/tests", response_model=schemas.ApiResponse)
def get_task_tests(
    task_id: str,
    revealAll: bool = Query(False, description="是否包含隐藏测试集（仅教师可true）"),
    # 【P1-B 修复】保留 user_role query param 但忽略，改用 current_user.role 做 RBAC
    user_role_q: Optional[str] = Query(None, description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """按需拉取全部或公开测试集明细"""
    # 【P1-B 安全修复】禁止信任 query param，从 token 中取真实角色
    if user_role_q is not None:
        logger.warning(
            f"[P1-B] 攻击探测：客户端尝试用 query param 绕过 RBAC，task_id={task_id}，"
            f"client_role={user_role_q}，real_role={current_user.role}"
        )
    # 真实角色（来自 JWT token）
    real_role = current_user.role

    try:
        tests = crud.get_task_tests(db, task_id=task_id)

        test_list = []
        for test in tests:
            # 权限检查：只有教师/管理员可以查看隐藏测试集（不再信任 client param）
            if test.is_hidden and not (revealAll and real_role in ["teacher", "assistant", "admin"]):
                continue

            test_data = {
                "caseId": test.id,
                "hidden": test.is_hidden
            }

            # 隐藏测试用例不返回输入输出内容（除非是教师且revealAll=true）
            if not test.is_hidden or (revealAll and real_role in ["teacher", "assistant", "admin"]):
                test_data["input"] = test.input_data or ""
                test_data["expected"] = test.expected_output or ""

            test_list.append(test_data)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"tests": test_list}  # 包装在tests字段中
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.3 在线自动评测

@router.post("/tasks/{task_id}/evaluate", response_model=schemas.ApiResponse)
def evaluate_task(
    task_id: str,
    request: schemas.TaskEvaluationRequest,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交代码仓库当前快照哈希触发判题"""
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份访问 /evaluate，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        # 获取代码仓库hash，优先使用codeRepoHash，其次使用repo_hash
        repo_hash = request.codeRepoHash or request.repo_hash
        
        submission_data = {
            "answer": request.answer,
            "files": request.files,
            "code": request.code,
            "repo_hash": repo_hash
        }
        
        result = crud.submit_task_evaluation(
            db, task_id=task_id, user_id=user_id, submission_data=submission_data
        )
        
        # 格式化响应数据
        response_data = {
            "status": result["status"],
            "score": result["score"],
            "elapsed": result.get("execution_time", 0) / 1000.0,  # 转换为秒
            "logs": result.get("error_message", "") or "评测完成",
            # 添加详细统计信息
            "total_tests": result.get("total_tests", 0),
            "passed_tests": result.get("passed_tests", 0),
            "error_message": result.get("error_message", ""),
            # 添加每道题的详细结果（用于选择题等）
            "question_results": result.get("question_results", [])
        }
        
        # 如果有详细的测试结果，添加到logs中
        if result.get("test_results"):
            logs = []
            for i, test_result in enumerate(result["test_results"], 1):
                if test_result["passed"]:
                    logs.append(f"Case{i} OK")
                else:
                    logs.append(f"Case{i} FAIL: {test_result.get('error_message', '输出不匹配')}")
            response_data["logs"] = "\n".join(logs)
        
        # 如果是重复提交且已通过，添加提示信息
        if result.get("is_duplicate") and result["status"] == "pass":
            response_data["logs"] = (response_data.get("logs", "") + "\n\n注意：该任务已完成，本次评测不给予金币奖励。").strip()
            response_data["message"] = "任务已完成，本次评测不给予金币奖励"

        # 如果是重复提交但本次失败，仍然返回失败状态
        # 这允许学生验证已通过的代码是否仍然正确
        if result["status"] == "fail":
            response_data["message"] = "代码评测失败，请检查你的解决方案"

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=response_data
        )
    except ValueError as e:
        if "冷却" in str(e):
            return schemas.ApiResponse(
                code="1006",
                message=str(e),
                trace_id=str(uuid.uuid4())
            )
        else:
            return schemas.ApiResponse(
                code="1001",
                message=str(e),
                trace_id=str(uuid.uuid4())
            )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.4 保存代码快照

@router.post("/tasks/{task_id}/snapshots", response_model=schemas.ApiResponse)
def create_task_snapshot(
    task_id: str,
    request: schemas.CodeSnapshotRequest,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """在评测或离开页面时保存当前代码"""
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份保存快照，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        snapshot = crud.save_code_snapshot(
            db, task_id=task_id, user_id=user_id,
            repo_hash=request.repo_hash, files=request.files
        )

        return schemas.ApiResponse(
            code="0000",
            message="代码快照保存成功",
            data={"snapshot_id": snapshot.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.5 获取通关时代码快照

@router.get("/tasks/{task_id}/passed-snapshot", response_model=schemas.ApiResponse)
def get_passed_code_snapshot(
    task_id: str,
    # 【P1-C 修复】保留 query param 兼容，但完全忽略，改用 current_user 的真实身份
    user_id_q: Optional[int] = Query(None, description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取通关时代的代码快照"""
    # 【P1-C 安全修复】检测并记录攻击探测
    if user_id_q is not None:
        logger.warning(
            f"[P1-C] 攻击探测：客户端尝试用 user_id query param 冒用身份访问 /passed-snapshot，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    real_user_id = current_user.id

    try:
        snapshot = crud.get_passed_code_snapshot(db, task_id=task_id, user_id=real_user_id)
        if snapshot is None:
            return schemas.ApiResponse(
                code="1001",
                message="未找到通关时代码快照",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message="获取通关时代码快照成功",
            data=snapshot["files"]
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 实践环境相关API ====================

# 4.6.1 通用Session操作

@router.get("/tasks/{task_id}/answer", response_model=schemas.ApiResponse)
def get_task_answer(
    task_id: str,
    # 【P1-C 修复】保留 query param 兼容，但完全忽略，改用 current_user 的真实身份
    user_id_q: Optional[int] = Query(None, description="[已忽略，请使用真实 token]"),
    user_role_q: Optional[str] = Query(None, description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取参考答案，教师或已通关学生可查看"""
    # 【P1-C 安全修复】检测并记录攻击探测
    if user_id_q is not None or user_role_q is not None:
        logger.warning(
            f"[P1-C] 攻击探测：客户端尝试用 query param 冒用身份访问 /answer，"
            f"task_id={task_id}，client_user_id={user_id_q}，client_role={user_role_q}，"
            f"real_user_id={current_user.id}，real_role={current_user.role}"
        )
    real_user_id = current_user.id
    real_user_role = current_user.role

    try:
        answer = crud.get_task_answer(
            db, task_id=task_id, user_id=real_user_id, user_role=real_user_role
        )
        if answer is None:
            return schemas.ApiResponse(
                code="1003",
                message="无权限查看参考答案或答案不存在",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"content": answer["content"]}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课程状态相关API ====================

@router.get("/courses/{course_id}/tasks", response_model=schemas.ApiResponse)
def get_course_tasks(
    course_id: int,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    user_role_q: Optional[str] = Query(None, alias="user_role", description="[已忽略，请使用真实 token]"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取课程任务列表

    支持分页查询课程下的所有任务，包含完成状态信息
    """
    # 【IDOR 修复】禁止客户端通过 user_id/user_role query 冒用他人身份查看完成状态
    if user_id_q is not None and user_id_q != current_user.id and current_user.role not in ("teacher", "admin"):
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份查看完成状态，"
            f"course_id={course_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
        raise HTTPException(status_code=403, detail="无权查看他人任务完成状态")
    user_id = user_id_q if (current_user.role in ("teacher", "admin") and user_id_q is not None) else current_user.id
    user_role = current_user.role

    try:
        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        if not course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        
        # 获取任务列表
        tasks, total = crud.get_practice_tasks(
            db=db,
            practice_id=course_id,
            skip=skip,
            limit=page_size
        )
        
        # 构建任务响应数据
        task_list = []
        for task in tasks:
            # 获取学生完成状态
            evaluation_result = None
            if user_id and user_role == "student":
                evaluation_result = db.query(db_models.TaskEvaluationResult).filter(
                    db_models.TaskEvaluationResult.task_id == task.id,
                    db_models.TaskEvaluationResult.user_id == user_id,
                    db_models.TaskEvaluationResult.status == "pass"
                ).first()
            
            task_data = {
                "id": task.id,
                "title": task.title,
                "task_type": task.task_type.value,
                "order_in_practice": task.order_in_practice,
                "coin": task.coin,
                "difficulty": task.difficulty,
                "env_type": task.env_type,
                "is_completed": evaluation_result is not None,
                "completion_status": "已完成" if evaluation_result else "未开始",
                "score": evaluation_result.score if evaluation_result else None,
                "completion_time": evaluation_result.created_at if evaluation_result else None,
                "created_at": task.created_at
            }
            task_list.append(task_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": task_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/courses/{course_id}/start-task/{task_id}", response_model=schemas.ApiResponse)
def start_course_task(
    course_id: int,
    task_id: int,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    开始课程任务

    学生点击关卡挑战时调用，开始计时
    """
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份开始任务，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        # 验证课程和任务是否存在
        task = db.query(db_models.Task).filter(
            db_models.Task.id == task_id,
            db_models.Task.practice_id == course_id
        ).first()
        
        if not task:
            return schemas.ApiResponse(
                code="1002",
                message="任务不存在",
                trace_id=str(uuid.uuid4())
            )

        # 检查关卡顺序：只有完成前序关卡才能开始当前关卡
        if task.order_in_practice > 1:
            # 获取前序关卡
            previous_tasks = db.query(db_models.Task).filter(
                db_models.Task.practice_id == course_id,
                db_models.Task.order_in_practice < task.order_in_practice
            ).all()

            # 检查每个前序关卡是否已完成
            for prev_task in previous_tasks:
                # 检查是否有完成的评测结果记录
                evaluation_result = db.query(db_models.TaskEvaluationResult).filter(
                    db_models.TaskEvaluationResult.task_id == prev_task.id,
                    db_models.TaskEvaluationResult.user_id == user_id,
                    db_models.TaskEvaluationResult.status == "pass"
                ).first()

                if not evaluation_result:
                    return schemas.ApiResponse(
                        code="1004",
                        message=f"请先完成关卡 {prev_task.order_in_practice}：{prev_task.title}",
                        trace_id=str(uuid.uuid4())
                    )

        # 创建或更新环境会话
        session = db.query(db_models.PracticeEnvironmentSession).filter(
            db_models.PracticeEnvironmentSession.task_id == task_id,
            db_models.PracticeEnvironmentSession.user_id == user_id,
            db_models.PracticeEnvironmentSession.status == "active"
        ).first()
        
        if not session:
            # 创建新的环境会话
            session_id = f"session_{user_id}_{task_id}_{int(datetime.now().timestamp())}"
            session = db_models.PracticeEnvironmentSession(
                task_id=task_id,
                user_id=user_id,
                env_type=task.env_type or "online-code",
                session_id=session_id,
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=2)  # 2小时后过期
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        return schemas.ApiResponse(
            code="0000",
            message="任务已开始",
            data={
                "session_id": session.session_id,
                "task_id": task_id,
                "env_type": session.env_type,
                "expires_at": session.expires_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 命令行环境管理API ====================

@router.post("/tasks/{task_id}/reset-terminal")
async def reset_terminal_environment(
    task_id: int,
    request: Request,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置命令行环境"""
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份重置终端，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        # 验证任务存在
        task = crud.get_task_detail(db, task_id=task_id)
        if not task:
            return schemas.ApiResponse(
                code="1001",
                message="任务不存在",
                trace_id=str(uuid.uuid4())
            )

        # 验证任务环境类型
        if task.env_type != "COMMAND_LINE":
            return schemas.ApiResponse(
                code="1002",
                message="该任务不是命令行类型的任务",
                trace_id=str(uuid.uuid4())
            )

        # 调用重置函数
        result = crud.reset_terminal(db, terminal_id=task_id, user_id=user_id)

        return schemas.ApiResponse(
            code="0000",
            message="命令行环境重置成功",
            data=result,
            trace_id=str(uuid.uuid4())
        )

    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 代码保存和状态查询API ====================

@router.post("/tasks/{task_id}/save", response_model=schemas.ApiResponse)
def save_task_code(
    task_id: str,
    request: schemas.CodeSnapshotRequest,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存用户的代码快照（前端自动保存）"""
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份保存代码，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        snapshot = crud.save_code_snapshot(
            db, task_id=task_id, user_id=user_id,
            repo_hash=request.repo_hash, files=request.files
        )

        return schemas.ApiResponse(
            code="0000",
            message="代码保存成功",
            data={"snapshot_id": snapshot.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/tasks/{task_id}/hints", response_model=schemas.ApiResponse)
def get_task_hints(
    task_id: str,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    hint_index: int = Query(0, ge=0, description="已显示的提示数量"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务提示，按顺序逐步显示"""
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 绕过'必须先通关'门槛查看提示，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        task = crud.get_task_detail(db, task_id=task_id)
        if not task:
            return schemas.ApiResponse(
                code="1002",
                message="任务不存在",
                trace_id=str(uuid.uuid4())
            )

        # 检查用户是否有权限查看提示（已通关或教师）
        evaluation_result = db.query(db_models.TaskEvaluationResult).filter(
            db_models.TaskEvaluationResult.task_id == task_id,
            db_models.TaskEvaluationResult.user_id == user_id,
            db_models.TaskEvaluationResult.status == "pass"
        ).first()

        # 如果用户还没通关，检查是否为教师
        # 这里暂时只允许已通关用户查看提示
        if not evaluation_result:
            return schemas.ApiResponse(
                code="1003",
                message="请先完成关卡后再查看提示",
                trace_id=str(uuid.uuid4())
            )

        # 从task.question_data字段获取提示列表（暂时用question_data存储提示）
        hints = []
        if task.question_data:
            try:
                question_data = json.loads(task.question_data)
                hints = question_data.get("hints", [])
            except json.JSONDecodeError:
                hints = []
        # 如果没有hints，暂时返回空提示（后续需要添加hints字段到数据库）
        elif hasattr(task, 'hints') and task.hints:
            try:
                hints = json.loads(task.hints)
            except json.JSONDecodeError:
                hints = []

        if hint_index >= len(hints):
            return schemas.ApiResponse(
                code="1004",
                message="没有更多提示了",
                trace_id=str(uuid.uuid4())
            )

        next_hint = hints[hint_index] if hint_index < len(hints) else None

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "hint": next_hint,
                "hint_index": hint_index + 1,
                "total_hints": len(hints),
                "has_more": hint_index + 1 < len(hints)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/tasks/{task_id}/status", response_model=schemas.ApiResponse)
def get_task_evaluation_status(
    task_id: str,
    user_id_q: Optional[int] = Query(None, alias="user_id", description="[已忽略，请使用真实 token]"),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务的评测状态"""
    if user_id_q is not None:
        logger.warning(
            f"[IDOR修复] 攻击探测：客户端尝试用 user_id query param 冒用身份查看评测状态，"
            f"task_id={task_id}，client_user_id={user_id_q}，real_user_id={current_user.id}"
        )
    user_id = current_user.id
    try:
        task = crud.get_task_detail(db, task_id=task_id)
        if not task:
            return schemas.ApiResponse(
                code="1002",
                message="任务不存在",
                trace_id=str(uuid.uuid4())
            )

        # 查询最新的评测结果
        latest_evaluation = db.query(db_models.TaskEvaluationResult).filter(
            db_models.TaskEvaluationResult.task_id == task_id,
            db_models.TaskEvaluationResult.user_id == user_id
        ).order_by(db_models.TaskEvaluationResult.created_at.desc()).first()

        status_data = {
            "task_id": task_id,
            "status": "not_started",  # 默认状态
            "score": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "execution_time": 0,
            "last_evaluation_time": None,
            "error_message": "",
            "is_completed": False
        }

        if latest_evaluation:
            status_data.update({
                "status": latest_evaluation.status,
                "score": latest_evaluation.score,
                "total_tests": latest_evaluation.total_tests,
                "passed_tests": latest_evaluation.passed_tests,
                "execution_time": latest_evaluation.execution_time,
                "last_evaluation_time": latest_evaluation.created_at,
                "error_message": latest_evaluation.error_message,
                "is_completed": latest_evaluation.status == "pass"
            })

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=status_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 学生管理相关API ====================


