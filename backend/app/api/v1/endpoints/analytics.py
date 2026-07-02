"""
学情分析端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid
import logging
import io
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# 修正的导入路径
from app.core.database import get_db, engine, Base
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id
from app.models import models as db_models  # 避免与FastAPI的models冲突
from app.crud import crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=['learning_analytics']
)

@router.get("/classrooms/{classroom_id}/learning/overview", response_model=schemas.ApiResponse)
def get_learning_overview(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取学情总览"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        overview_data = crud.get_learning_overview(db, classroom_id)
        
        if overview_data is None:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=overview_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学情总览失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/learning/students", response_model=schemas.ApiResponse)
def get_learning_students(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    course_type: str = Query(..., description="课程类型：required(必修), optional(拓展)"),
    keyword: Optional[str] = Query(None, description="按姓名或学号搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取学生学习统计（必修课程统计/拓展课程统计）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 验证课程类型参数
        if course_type not in ["required", "optional"]:
            return schemas.ApiResponse(
                code="1003",
                message="无效的课程类型参数，必须是 required 或 optional",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        
        if course_type == "required":
            analytics_data = crud.get_required_courses_analytics(
                db, classroom_id, keyword, skip, page_size
            )
        else:
            analytics_data = crud.get_optional_courses_analytics(
                db, classroom_id, keyword, skip, page_size
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=analytics_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生学习统计失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/learning/transcript/{student_id}", response_model=schemas.ApiResponse)
def get_student_transcript(
    classroom_id: int,
    student_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """查看学生个人成绩单"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        transcript_data = crud.get_student_transcript(db, classroom_id, student_id)
        
        if transcript_data is None:
            return schemas.ApiResponse(
                code="1004",
                message="学生不存在或不在该课堂中",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=transcript_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生成绩单失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/learning/export")
def export_learning_analytics_get(
    classroom_id: int,
    course_type: str = Query(..., description="课程类型：required(必修), optional(拓展)"),
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    student_ids: Optional[str] = Query(None, description="要导出的学生学员ID逗号分隔列表。为空则导出全部。"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """导出学情分析数据(Excel表格)"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="课堂不存在或无权限")
        
        # 验证课程类型参数
        if course_type not in ["required", "optional"]:
            raise HTTPException(status_code=400, detail="无效的课程类型参数，必须是 required 或 optional")
            
        # 根据选中的学生ID获取对应数据
        target_student_ids = None
        if student_ids:
            target_student_ids = [int(sid) for sid in student_ids.split(",") if sid.strip().isdigit()]
        
        # 获取要导出的数据 (如果条目过多可分页，此处设置大一点的limit来做导出)
        # TODO: 获取未作废或所有符合条件的记录。目前的crud实现没提供基于student_ids过滤，先获取全部再筛选
        limit = 10000 
        if course_type == "required":
            analytics_data = crud.get_required_courses_analytics(db, classroom_id, None, 0, limit)
        else:
            analytics_data = crud.get_optional_courses_analytics(db, classroom_id, None, 0, limit)
            
        records = analytics_data.get("list", [])
        
        # 在内存中过滤指定的学生
        if target_student_ids:
            records = [r for r in records if r["student_id"] in target_student_ids]
            
        if not records:
            raise HTTPException(status_code=404, detail="没有可导出的数据")
            
        # 准备数据为DataFrame
        export_data = []
        for r in records:
            status_text = "在线" if r.get("online_status") == "online" else "离线"
            export_data.append({
                "姓名": r.get("student_name", ""),
                "在线状态": status_text,
                "年级/班级": f"{r.get('grade') or ''} {r.get('class_name') or ''}".strip(),
                "实践完成数": r.get("practice_completed", 0),
                "实践平均分": round(r.get("practice_average_score", 0), 2),
                "实训完成数": r.get("training_completed", 0),
                "实训平均分": round(r.get("training_average_score", 0), 2),
                "总平均分": round(r.get("course_average_score", 0), 2),
                "学习时长(小时)": round(r.get("total_study_hours", 0), 2)
            })
            
        df = pd.DataFrame(export_data)
        
        # 创建一个内存缓冲区来保存Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='学情统计', index=False)
            
        output.seek(0)
        
        # 文件名
        time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        course_type_name = "必修" if course_type == "required" else "拓展"
        filename = f"学情统计_{course_type_name}_{time_str}.xlsx"
        # 进行URL转码以便浏览器正确解析中文名
        filename_encoded = quote(filename)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename_encoded}"',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
        
        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
        
    except HTTPException as he:
        raise he
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出学情分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部异常: {str(e)}")

# (原 POST export 已废弃，但为了兼容性可以保留或者删除，这里将其删除以强制使用GET)

# 保留原有的API端点以保持向后兼容
@router.get("/classrooms/{classroom_id}/analytics/overview", response_model=schemas.ApiResponse)
def get_classroom_analytics_overview(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取学情分析总览（兼容旧版本）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        analytics_data = crud.get_classroom_analytics_overview(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=analytics_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/analytics/mandatory-courses", response_model=schemas.ApiResponse)
def get_mandatory_courses_analytics(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取必修课程统计（兼容旧版本）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        analytics_data = crud.get_mandatory_courses_analytics(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=analytics_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/classrooms/{classroom_id}/analytics/elective-courses", response_model=schemas.ApiResponse)
def get_elective_courses_analytics(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取拓展课程统计（兼容旧版本）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        analytics_data = crud.get_elective_courses_analytics(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=analytics_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


