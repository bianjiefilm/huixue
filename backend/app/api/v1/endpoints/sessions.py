"""
会话管理端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="",
    tags=['sessions']
)

@router.post("/sessions/{session_id}/close", response_model=schemas.ApiResponse)
def close_session(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """正常结束并释放资源"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        # 这里应该实现实际的session关闭逻辑
        return schemas.ApiResponse(
            code="0000",
            message="Session已关闭",
            data={"session_id": session_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/heartbeat", response_model=schemas.ApiResponse)
def session_heartbeat(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """前端每60s调用，若超时则容器自动回收"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        # 这里应该实现实际的心跳续期逻辑
        return schemas.ApiResponse(
            code="0000",
            message="心跳续期成功",
            data={"session_id": session_id, "expires_in": 3600}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.2 在线编码环境操作

@router.patch("/sessions/{session_id}/font-size", response_model=schemas.ApiResponse)
def update_font_size(
    session_id: str,
    request: schemas.FontSizeRequest,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """字号调整"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        size = request.size
        if not (10 <= size <= 40):
            return schemas.ApiResponse(
                code="1001",
                message="字号范围应在10-40之间",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="字号调整成功",
            data={"session_id": session_id, "font_size": size}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/reset-code", response_model=schemas.ApiResponse)
def reset_code(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置全部代码 - 仓库回到初始化提交"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        return schemas.ApiResponse(
            code="0000",
            message="全部代码已重置",
            data={"session_id": session_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/reset-file", response_model=schemas.ApiResponse)
def reset_file(
    session_id: str,
    request: schemas.ResetFileRequest,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置当前文件 - 仅回滚单文件"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        file_path = request.path
        return schemas.ApiResponse(
            code="0000",
            message=f"文件 {file_path} 已重置",
            data={"session_id": session_id, "path": file_path}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/restore-pass", response_model=schemas.ApiResponse)
def restore_pass(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """回溯至通关代码 - 通关后可用"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        # 这里应该检查用户是否已通关
        return schemas.ApiResponse(
            code="0000",
            message="已恢复至通关代码",
            data={"session_id": session_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.3 HTML前端实践环境操作

@router.post("/sessions/{session_id}/toggle-preview", response_model=schemas.ApiResponse)
def toggle_preview(
    session_id: str,
    request: schemas.TogglePreviewRequest,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开关实时预览"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        enabled = request.enabled
        return schemas.ApiResponse(
            code="0000",
            message="预览状态已更新",
            data={"session_id": session_id, "preview_enabled": enabled}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.patch("/sessions/{session_id}/preview-size", response_model=schemas.ApiResponse)
def update_preview_size(
    session_id: str,
    request: schemas.PreviewSizeRequest,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """窗口尺寸调整"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        width = request.width
        height = request.height
        return schemas.ApiResponse(
            code="0000",
            message="预览窗口尺寸已调整",
            data={"session_id": session_id, "width": width, "height": height}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.4 命令行环境操作

@router.post("/sessions/{session_id}/reset-shell", response_model=schemas.ApiResponse)
def reset_shell(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置命令行 - 重新启动终端并清空历史"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        return schemas.ApiResponse(
            code="0000",
            message="命令行已重置",
            data={"session_id": session_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.5 云桌面环境操作

@router.post("/sessions/{session_id}/extend", response_model=schemas.ApiResponse)
def extend_session(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """延时 - 默认+30min"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        return schemas.ApiResponse(
            code="0000",
            message="会话已延时30分钟",
            data={"session_id": session_id, "extended_minutes": 30}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/clipboard", response_model=schemas.ApiResponse)
def update_clipboard(
    session_id: str,
    request: schemas.ClipboardRequest,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """剪切板同步 - 双向剪贴板"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        content = request.content
        return schemas.ApiResponse(
            code="0000",
            message="剪切板同步成功",
            data={"session_id": session_id, "content_length": len(content)}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/fullscreen", response_model=schemas.ApiResponse)
def toggle_fullscreen(
    session_id: str,
    request: schemas.FullscreenRequest,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """全屏/退出 - 切换显示模式"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        enabled = request.enabled
        return schemas.ApiResponse(
            code="0000",
            message="全屏状态已更新",
            data={"session_id": session_id, "fullscreen": enabled}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/reset-env", response_model=schemas.ApiResponse)
def reset_environment(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置环境 - 保留持久化路径，其他全部还原"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        return schemas.ApiResponse(
            code="0000",
            message="环境已重置",
            data={"session_id": session_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/sessions/{session_id}/reset-task", response_model=schemas.ApiResponse)
def reset_task(
    session_id: str,
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置任务文件 - 仅回滚学生代码区"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        return schemas.ApiResponse(
            code="0000",
            message="任务文件已重置",
            data={"session_id": session_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 保留参考答案接口作为独立功能


# ==================== 实训会话相关路由 ====================

@router.post("/training-sessions", response_model=schemas.ApiResponse)
def create_training_session(
    request: schemas.TrainingSessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建实训会话
    
    学生开始实训时创建会话，分配容器资源
    """
    try:
        # 检查课堂实训是否存在
        classroom_training = db.query(db_models.ClassroomTraining).filter(
            db_models.ClassroomTraining.id == request.classroom_training_id,
            db_models.ClassroomTraining.is_active == True
        ).first()
        
        if not classroom_training:
            return schemas.ApiResponse(
                code="1001",
                message="课堂实训不存在或已失效",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查学生是否在课堂中
        student_classroom = db.query(db_models.StudentClassroom).filter(
            db_models.StudentClassroom.classroom_id == classroom_training.classroom_id,
            db_models.StudentClassroom.student_id == request.student_id
        ).first()
        
        if not student_classroom:
            return schemas.ApiResponse(
                code="1002",
                message="学生不在该课堂中",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否已有活跃会话
        existing_session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.classroom_training_id == request.classroom_training_id,
            db_models.TrainingSession.student_id == request.student_id,
            db_models.TrainingSession.is_active == True
        ).first()
        
        if existing_session:
            # 返回现有会话
            return schemas.ApiResponse(
                code="0000",
                message="已存在活跃会话",
                data={
                    "id": existing_session.id,
                    "session_id": existing_session.session_id,
                    "jupyter_url": existing_session.jupyter_url,
                    "jupyter_token": existing_session.jupyter_token
                }
            )
        
        # 创建新会话
        import secrets
        session_id = f"training_{request.classroom_training_id}_{request.student_id}_{secrets.token_hex(8)}"
        jupyter_token = secrets.token_urlsafe(32)
        
        # TODO: 这里应该调用容器管理服务创建实际的容器
        # 暂时使用模拟数据
        container_name = f"jupyter_{session_id}"
        jupyter_port = 8888  # 实际应该动态分配
        jupyter_url = f"http://localhost:{jupyter_port}/lab?token={jupyter_token}"
        
        new_session = db_models.TrainingSession(
            session_id=session_id,
            classroom_training_id=request.classroom_training_id,
            student_id=request.student_id,
            container_name=container_name,
            container_status="running",
            jupyter_token=jupyter_token,
            jupyter_url=jupyter_url,
            start_time=datetime.utcnow(),
            last_active_time=datetime.utcnow(),
            is_active=True
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return schemas.ApiResponse(
            code="0000",
            message="实训会话创建成功",
            data={
                "id": new_session.id,
                "session_id": new_session.session_id,
                "jupyter_url": new_session.jupyter_url,
                "jupyter_token": new_session.jupyter_token,
                "container_name": new_session.container_name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建实训会话失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.get("/training-sessions/{session_id}", response_model=schemas.ApiResponse)
def get_training_session(
    session_id: int,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取实训会话详情"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.id == session_id,
            db_models.TrainingSession.student_id == student_id
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1003",
                message="会话不存在或无权访问",
                trace_id=str(uuid.uuid4())
            )
        
        # 计算总时长（分钟）
        if session.is_active:
            duration = datetime.utcnow() - session.start_time
        else:
            duration = session.last_active_time - session.start_time
        total_minutes = int(duration.total_seconds() / 60)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取会话详情成功",
            data={
                "id": session.id,
                "session_id": session.session_id,
                "classroom_training_id": session.classroom_training_id,
                "student_id": session.student_id,
                "container_name": session.container_name,
                "container_status": session.container_status,
                "jupyter_url": session.jupyter_url,
                "jupyter_token": session.jupyter_token,
                "start_time": session.start_time,
                "last_active_time": session.last_active_time,
                "total_duration_minutes": total_minutes,
                "progress_percentage": session.progress_percentage,
                "is_active": session.is_active
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训会话失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/training-sessions/{session_id}/heartbeat", response_model=schemas.ApiResponse)
def training_session_heartbeat(
    session_id: int,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """实训会话心跳"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.id == session_id,
            db_models.TrainingSession.student_id == student_id,
            db_models.TrainingSession.is_active == True
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1003",
                message="会话不存在或已结束",
                trace_id=str(uuid.uuid4())
            )
        
        # 更新最后活跃时间
        session.last_active_time = datetime.utcnow()
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="心跳续期成功",
            data={
                "session_id": session.id,
                "expires_in": 3600  # 1小时后过期
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实训会话心跳失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.put("/training-sessions/{session_id}/progress", response_model=schemas.ApiResponse)
def update_training_progress(
    session_id: int,
    request: schemas.TrainingProgressUpdateRequest,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新实训进度"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.id == session_id,
            db_models.TrainingSession.student_id == student_id,
            db_models.TrainingSession.is_active == True
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1003",
                message="会话不存在或已结束",
                trace_id=str(uuid.uuid4())
            )
        
        # 更新进度
        session.progress_percentage = request.progress_percentage
        if request.current_step:
            session.current_step = request.current_step
        if request.completed_tasks:
            import json
            session.completed_tasks = json.dumps(request.completed_tasks)
        
        session.last_active_time = datetime.utcnow()
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="进度更新成功",
            data={
                "session_id": session.id,
                "progress_percentage": session.progress_percentage
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新实训进度失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/training-sessions/{session_id}/submit", response_model=schemas.ApiResponse)
def submit_training(
    session_id: int,
    request: schemas.TrainingSubmissionRequest,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交实训结果"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.id == session_id,
            db_models.TrainingSession.student_id == student_id
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1003",
                message="会话不存在或无权访问",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否已提交
        existing_submission = db.query(db_models.TrainingSubmission).filter(
            db_models.TrainingSubmission.session_id == session_id
        ).first()
        
        if existing_submission:
            return schemas.ApiResponse(
                code="1004",
                message="已提交过实训结果",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否超过截止时间
        classroom_training = db.query(db_models.ClassroomTraining).filter(
            db_models.ClassroomTraining.id == session.classroom_training_id
        ).first()
        
        now = datetime.utcnow()
        is_late = now > classroom_training.end_time
        
        # 如果迟交，检查是否在允许补交期限内
        if is_late and classroom_training.allow_late_submission:
            late_deadline = classroom_training.end_time + timedelta(days=classroom_training.late_submission_days)
            if now > late_deadline:
                return schemas.ApiResponse(
                    code="1005",
                    message="已超过补交期限",
                    trace_id=str(uuid.uuid4())
                )
        elif is_late:
            return schemas.ApiResponse(
                code="1006",
                message="已超过提交期限且不允许补交",
                trace_id=str(uuid.uuid4())
            )
        
        # 创建提交记录
        import json
        submission = db_models.TrainingSubmission(
            session_id=session_id,
            submission_type=request.submission_type,
            notebook_content=request.notebook_content,
            project_files=json.dumps(request.project_files) if request.project_files else None,
            summary=request.summary,
            submission_time=now,
            is_late=is_late
        )
        
        db.add(submission)
        
        # 更新会话进度为100%
        session.progress_percentage = 100.0
        session.is_active = False  # 结束会话
        
        db.commit()
        db.refresh(submission)
        
        return schemas.ApiResponse(
            code="0000",
            message="实训提交成功",
            data={
                "id": submission.id,
                "submission_time": submission.submission_time,
                "is_late": submission.is_late
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交实训失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/training-sessions/{session_id}/close", response_model=schemas.ApiResponse)
def close_training_session(
    session_id: int,
    student_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """关闭实训会话"""
    try:
        student_id = resolve_scoped_id(current_user, student_id, allowed_roles=("student",))
        session = db.query(db_models.TrainingSession).filter(
            db_models.TrainingSession.id == session_id,
            db_models.TrainingSession.student_id == student_id,
            db_models.TrainingSession.is_active == True
        ).first()
        
        if not session:
            return schemas.ApiResponse(
                code="1003",
                message="会话不存在或已关闭",
                trace_id=str(uuid.uuid4())
            )
        
        # TODO: 调用容器管理服务停止并删除容器
        
        # 更新会话状态
        session.is_active = False
        session.container_status = "stopped"
        session.last_active_time = datetime.utcnow()
        
        # 计算总时长
        duration = session.last_active_time - session.start_time
        session.total_duration_minutes = int(duration.total_seconds() / 60)
        
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="会话已关闭",
            data={
                "session_id": session.id,
                "total_duration_minutes": session.total_duration_minutes
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关闭实训会话失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

