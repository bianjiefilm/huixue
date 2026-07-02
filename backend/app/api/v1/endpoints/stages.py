"""
任务关卡编辑相关的API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone
import json

# 导入依赖
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id
from app.models import models as db_models
from app.crud import stage_crud
from app.schemas import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=['stages']
)

# ==================== 关卡管理相关API ====================

@router.get("/practices/{practice_id}/stages", response_model=schemas.ApiResponse)
def get_practice_stages(
    practice_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取实践的关卡列表"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        skip = (page - 1) * page_size
        stages, total = stage_crud.get_practice_stages(
            db=db,
            practice_id=practice_id,
            creator_id=creator_id,
            skip=skip,
            limit=page_size
        )
        
        if stages is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_list = [schemas.StageResponse.model_validate(stage) for stage in stages]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": [stage.model_dump() for stage in stage_list],
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
        logger.error(f"获取关卡列表失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/practices/{practice_id}/stages/management", response_model=schemas.ApiResponse)
def get_practice_stage_management(
    practice_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取实践关卡管理页面数据 (教师管理视图)

    Z3 P0-7 修: 强制 JWT, 用 token 中 user_id / role 覆盖 query.creator_id.
    teacher/admin 角色才放行无主 (creator_id IS NULL) practice — 学校 21 个 practice
    全 NULL creator_id, 这是单租户运营现状, 教师/管理员都可编辑.
    """
    try:
        user_id = current_user["id"]
        user_role = (current_user.get("roles") or ["student"])[0]

        # 学生不能管理关卡
        if user_role not in ("teacher", "admin"):
            return schemas.ApiResponse(
                code="1003",
                message="无权限访问关卡管理",
                trace_id=str(uuid.uuid4())
            )

        data = stage_crud.get_practice_stage_management_data(
            db=db,
            practice_id=practice_id,
            creator_id=user_id,
            allow_orphan=True,  # teacher/admin 视角放行 NULL creator_id 的 practice
        )
        
        if data is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 转换stages为响应格式
        stage_list = [schemas.StageResponse.model_validate(stage) for stage in data['stages']]
        data['stages'] = [stage.model_dump() for stage in stage_list]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关卡管理数据失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡创建相关API ====================

@router.post("/practices/{practice_id}/stages/step1", response_model=schemas.ApiResponse)
def create_stage_step1(
    practice_id: int,
    request: schemas.StageTaskEditRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建关卡 - 第一步：基本信息"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage_data = request.model_dump()
        stage = stage_crud.create_practice_stage_step1(
            db=db,
            practice_id=practice_id,
            stage_data=stage_data,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="关卡基本信息创建成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建关卡第一步失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/stages/{stage_id}/step1", response_model=schemas.ApiResponse)
def update_stage_step1(
    stage_id: int,
    request: schemas.StageTaskEditRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关卡 - 第一步：基本信息"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        update_data = request.model_dump()
        stage = stage_crud.update_practice_stage(
            db=db,
            stage_id=stage_id,
            update_data=update_data,
            creator_id=creator_id
        )

        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )

        stage_response = schemas.StageResponse.model_validate(stage)

        return schemas.ApiResponse(
            code="0000",
            message="关卡基本信息更新成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关卡第一步失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/stages/{stage_id}/step2", response_model=schemas.ApiResponse)
def update_stage_step2(
    stage_id: int,
    request: schemas.StageTaskSettingsRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关卡 - 第二步：任务设置（实践题专用）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        settings_data = request.model_dump()
        stage = stage_crud.update_practice_stage_step2(
            db=db,
            stage_id=stage_id,
            settings_data=settings_data,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="任务设置更新成功",
            data=stage_response.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关卡第二步失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/stages/{stage_id}/test-cases", response_model=schemas.ApiResponse)
def create_stage_test_cases(
    stage_id: int,
    request: schemas.StageTestCasesRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建关卡测试集"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # request.test_cases 已经是 List[Dict]，无需 model_dump()
        test_cases_data = request.test_cases
        test_cases = stage_crud.create_stage_test_cases(
            db=db,
            stage_id=stage_id,
            test_cases_data=test_cases_data,
            creator_id=creator_id
        )
        
        if test_cases is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        test_case_list = [schemas.TaskTestResponse.model_validate(tc) for tc in test_cases]
        
        return schemas.ApiResponse(
            code="0000",
            message="测试集创建成功",
            data={
                "test_cases": [tc.model_dump() for tc in test_case_list],
                "count": len(test_case_list)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建测试集失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/stages/{stage_id}/step3", response_model=schemas.ApiResponse)
def update_stage_step3(
    stage_id: int,
    request: schemas.StageAnswerRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关卡 - 第三步：参考答案"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        answer_data = request.model_dump()
        stage = stage_crud.update_practice_stage_step3(
            db=db,
            stage_id=stage_id,
            answer_data=answer_data,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="参考答案更新成功",
            data=stage_response.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关卡第三步失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/practices/{practice_id}/stages/complete", response_model=schemas.ApiResponse)
def create_stage_complete(
    practice_id: int,
    request: schemas.StageCreateCompleteRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """完整创建关卡（三步合一）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage_data = request.model_dump()
        stage = stage_crud.create_practice_stage_complete(
            db=db,
            practice_id=practice_id,
            stage_data=stage_data,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="关卡创建成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完整创建关卡失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡详情和编辑相关API ====================

@router.get("/stages/{stage_id}", response_model=schemas.ApiResponse)
def get_stage_detail(
    stage_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取关卡详情

    安全 (Z1 加固): 强制要求 JWT, 用 token 中 user_id / role 覆盖 query.creator_id,
    防止 ?creator_id=任意学生id 的横向越权. query.creator_id 仅作向后兼容保留, 不参与查询.

    端点同时承担教师 (查看自己创建的关卡) 和学生 (从课堂进入关卡) 两种角色:
    - role==teacher/admin: 按 Practice.creator_id 视角查
    - role==student: 按 ClassroomCourse + ClassroomStudent 视角查 (含 PUBLISHED 过滤)
    """
    try:
        user_id = current_user["id"]
        user_role = (current_user.get("roles") or ["student"])[0]

        # 教师/管理员视角: 通过 Practice.creator_id 校验
        result = None
        if user_role in ("teacher", "admin"):
            result = stage_crud.get_practice_stage_detail(
                db=db,
                stage_id=stage_id,
                creator_id=user_id
            )

        # 学生视角 (或教师视角未命中时 fallback): 通过 classroom_courses + classroom_students 校验
        if result is None:
            result = stage_crud.get_stage_detail_for_student(
                db=db,
                stage_id=stage_id,
                user_id=user_id,
            )

        if result is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage, test_cases = result
        stage_response = schemas.StageResponse.model_validate(stage)
        test_case_list = [schemas.TaskTestResponse.model_validate(tc) for tc in test_cases]
        
        # 构建详情响应
        detail_data = stage_response.model_dump()
        detail_data['test_cases'] = [tc.model_dump() for tc in test_case_list]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=detail_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关卡详情失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/stages/{stage_id}", response_model=schemas.ApiResponse)
def update_stage(
    stage_id: int,
    request: schemas.StageUpdateRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关卡信息"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}

        stage = stage_crud.update_practice_stage(
            db=db,
            stage_id=stage_id,
            update_data=update_data,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="关卡更新成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关卡失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.delete("/stages/{stage_id}", response_model=schemas.ApiResponse)
def delete_stage(
    stage_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除关卡（带验证）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage = stage_crud.delete_practice_stage_with_validation(
            db=db,
            stage_id=stage_id,
            creator_id=creator_id
        )

        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message="关卡删除成功",
            data={"stage_id": stage_id}
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1003",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除关卡失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/stages/batch-delete", response_model=schemas.ApiResponse)
def batch_delete_stages(
    request: schemas.BatchStageDeleteRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量删除关卡"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stages = stage_crud.batch_delete_practice_stages(
            db=db,
            stage_ids=request.stage_ids,
            creator_id=creator_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功删除{len(stages)}个关卡",
            data={
                "deleted_count": len(stages),
                "stage_ids": request.stage_ids
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除关卡失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡排序相关API ====================

@router.put("/practices/{practice_id}/stages/order", response_model=schemas.ApiResponse)
def update_stage_order(
    practice_id: int,
    request: schemas.StageOrderUpdateRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关卡排序"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        result = stage_crud.update_stage_order(
            db=db,
            practice_id=practice_id,
            stage_orders=request.stage_orders,
            creator_id=creator_id
        )
        
        if result is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="关卡排序更新成功",
            data={"updated_count": len(request.stage_orders)}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关卡排序失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 代码仓库文件管理相关API ====================

@router.get("/practices/{practice_id}/repository/files", response_model=schemas.ApiResponse)
def get_repository_files(
    practice_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取实践代码仓库文件列表"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        files_data = stage_crud.get_practice_code_repository_files(
            db=db,
            practice_id=practice_id,
            creator_id=creator_id
        )
        
        if files_data is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在、无权限或未配置代码仓库",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=files_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代码仓库文件失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡验证相关API ====================

@router.post("/practices/{practice_id}/stages/validate", response_model=schemas.ApiResponse)
def validate_stage_data(
    practice_id: int,
    request: schemas.StageCreateCompleteRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    stage_id: Optional[int] = Query(None, description="关卡ID（更新时提供）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """验证关卡数据"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage_data = request.model_dump()
        validation_result = stage_crud.validate_stage_data(
            db=db,
            practice_id=practice_id,
            stage_data=stage_data,
            creator_id=creator_id,
            stage_id=stage_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="验证完成",
            data=validation_result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证关卡数据失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡模板相关API ====================

@router.get("/stage-templates", response_model=schemas.ApiResponse)
def get_stage_templates(db: Session = Depends(get_db)):
    """获取关卡模板列表"""
    try:
        templates = stage_crud.get_stage_templates(db)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"templates": templates}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关卡模板失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/practices/{practice_id}/stages/apply-template", response_model=schemas.ApiResponse)
def apply_stage_template(
    practice_id: int,
    request: schemas.ApplyTemplateRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """应用关卡模板"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage = stage_crud.apply_stage_template(
            db=db,
            practice_id=practice_id,
            template_id=request.template_id,
            customize_data=request.customize_data or {},
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="模板不存在或实践无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="模板应用成功",
            data=stage_response.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"应用关卡模板失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 判断题和选择题相关API ====================

@router.put("/stages/{stage_id}/question-settings", response_model=schemas.ApiResponse)
def update_question_stage_settings(
    stage_id: int,
    request: schemas.StageQuestionTaskSettingsRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新题目类型关卡 - 第二步：题目设置"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        question_settings = request.model_dump()
        stage = stage_crud.create_question_stage_step2(
            db=db,
            stage_id=stage_id,
            question_settings=question_settings,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="题目设置更新成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新题目设置失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.get("/stages/{stage_id}/question-data", response_model=schemas.ApiResponse)
def get_question_stage_data(
    stage_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取题目类型关卡的题目数据"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        question_data = stage_crud.get_question_stage_data(
            db=db,
            stage_id=stage_id,
            creator_id=creator_id
        )
        
        if question_data is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=question_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目数据失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/stages/{stage_id}/question-data", response_model=schemas.ApiResponse)
def update_question_stage_data(
    stage_id: int,
    request: schemas.StageQuestionTaskSettingsRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新题目类型关卡的题目数据"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        question_settings = request.model_dump()
        stage = stage_crud.update_question_stage_data(
            db=db,
            stage_id=stage_id,
            question_settings=question_settings,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="题目数据更新成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新题目数据失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/practices/{practice_id}/stages/question-complete", response_model=schemas.ApiResponse)
def create_question_stage_complete(
    practice_id: int,
    request: schemas.StageQuestionCreateCompleteRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """完整创建题目类型关卡（三步合一）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage_data = request.model_dump()
        stage = stage_crud.create_question_stage_complete(
            db=db,
            practice_id=practice_id,
            stage_data=stage_data,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        stage_response = schemas.StageResponse.model_validate(stage)
        
        return schemas.ApiResponse(
            code="0000",
            message="题目类型关卡创建成功",
            data=stage_response.model_dump()
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1001",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建题目类型关卡失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.post("/practices/{practice_id}/stages/question-validate", response_model=schemas.ApiResponse)
def validate_question_stage_data(
    practice_id: int,
    request: schemas.StageQuestionCreateCompleteRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    stage_id: Optional[int] = Query(None, description="关卡ID（更新时提供）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """验证题目类型关卡数据"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage_data = request.model_dump()
        validation_result = stage_crud.validate_question_stage_data(
            db=db,
            practice_id=practice_id,
            stage_data=stage_data,
            creator_id=creator_id,
            stage_id=stage_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="验证完成",
            data=validation_result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证题目类型关卡数据失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡沙盒测试相关API ====================

@router.post("/stages/{stage_id}/sandbox-test", response_model=schemas.ApiResponse)
def stage_sandbox_test(
    stage_id: int,
    request: schemas.StageSandboxTestRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """关卡沙盒测试（教师模拟学生做题）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        result = stage_crud.stage_sandbox_test(
            db=db,
            stage_id=stage_id,
            test_data=request.model_dump(),
            creator_id=creator_id
        )
        
        if result is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        # 构建响应数据
        response_data = schemas.StageSandboxTestResponse(**result)
        
        return schemas.ApiResponse(
            code="0000",
            message="测试完成",
            data=response_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关卡沙盒测试失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡删除验证相关API ====================

@router.get("/stages/{stage_id}/delete-validation", response_model=schemas.ApiResponse)
def validate_stage_deletion(
    stage_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """验证关卡是否可以删除"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        result = stage_crud.validate_stage_deletion(
            db=db,
            stage_id=stage_id,
            creator_id=creator_id
        )
        
        if result is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        response_data = schemas.StageDeleteValidationResponse(**result)
        
        return schemas.ApiResponse(
            code="0000",
            message="验证完成",
            data=response_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关卡删除验证失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.delete("/stages/{stage_id}/with-validation", response_model=schemas.ApiResponse)
def delete_stage_with_validation(
    stage_id: int,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除关卡（带验证）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        stage = stage_crud.delete_practice_stage_with_validation(
            db=db,
            stage_id=stage_id,
            creator_id=creator_id
        )
        
        if stage is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="关卡删除成功",
            data={"stage_id": stage_id}
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1003",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除关卡失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡排序优化相关API ====================

@router.patch("/practices/{practice_id}/stages/sort", response_model=schemas.ApiResponse)
def update_stage_order_optimized(
    practice_id: int,
    request: schemas.StageOrderUpdateRequest,
    creator_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新关卡排序（优化版）"""
    try:
        creator_id = resolve_scoped_id(current_user, creator_id, allowed_roles=("teacher", "admin"))
        # 转换请求数据格式
        stage_orders = [
            {"stage_id": item.stage_id, "order_index": item.order_index}
            for item in request.stage_orders
        ]

        result = stage_crud.update_stage_order_optimized(
            db=db,
            practice_id=practice_id,
            stage_orders=stage_orders,
            creator_id=creator_id
        )

        if result is None:
            return schemas.ApiResponse(
                code="1002",
                message="实践不存在或无权限",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message=result["message"],
            data={"updated_count": result["updated_count"]}
        )
    except ValueError as e:
        return schemas.ApiResponse(
            code="1003",
            message=str(e),
            trace_id=str(uuid.uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新关卡排序失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 学生视角关卡详情API（权限隔离）====================

@router.get("/stages/{stage_id}/student-view", response_model=schemas.ApiResponse)
def get_student_stage_detail(
    stage_id: int,
    student_id: Optional[int] = Query(None, description="(已弃用) 历史 query 参数, 强制以 JWT 中 user_id 为准"),
    include_answer: bool = Query(False, description="是否包含参考答案（教师访问时设为True）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取学生视角的关卡详情

    - 学生访问时：未通关不返回参考答案，已通关返回参考答案
    - 教师访问时（include_answer=True）：返回完整数据包括参考答案
    """
    try:
        student_id = resolve_scoped_id(
            current_user, student_id,
            allowed_roles=("student", "teacher"),
            admin_roles=("admin",),
        )
        result = stage_crud.get_student_stage_detail(
            db=db,
            stage_id=stage_id,
            student_id=student_id,
            include_answer=include_answer
        )

        if result is None:
            return schemas.ApiResponse(
                code="1002",
                message="关卡不存在",
                trace_id=str(uuid.uuid4())
            )

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生关卡详情失败: {str(e)}")
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        ) 