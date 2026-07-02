"""
试卷库功能的API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id
from app.models import models
from app.schemas import schemas
from app.crud import crud_paper_library

router = APIRouter(
    prefix="/api/v1/paper-library",
    tags=['试卷库']
)

# 试卷列表和详情路由
@router.get("/papers", response_model=schemas.ApiResponse)
async def get_paper_library_list(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    keyword: Optional[str] = Query(None, description="试卷名称关键词"),
    direction: Optional[str] = Query(None, description="方向筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    source: Optional[str] = Query(None, description="来源筛选：personal/platform"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取试卷库列表"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    skip = (page - 1) * page_size

    papers, total = crud_paper_library.get_paper_library_list(
        db=db,
        teacher_id=teacher_id,
        keyword=keyword,
        direction=direction,
        difficulty=difficulty,
        source=source,
        skip=skip,
        limit=page_size
    )
    
    # 获取筛选标签
    filter_tags = crud_paper_library.get_paper_filter_tags(db)
    
    meta = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
    
    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data={
            "list": papers,
            "meta": meta,
            "filter_tags": filter_tags
        }
    )


@router.post("/create", response_model=schemas.ApiResponse)
async def create_test_paper(
    paper_request: schemas.PaperCreateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """新建试卷"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))

    paper_data = {
        "title": paper_request.title,
        "direction": paper_request.direction,
        "difficulty": paper_request.difficulty,
        "composition_method": paper_request.composition_method,
        "description": paper_request.description
    }
    
    new_paper = crud_paper_library.create_test_paper(
        db=db,
        paper_data=paper_data,
        creator_id=teacher_id
    )
    
    # 获取详情返回
    paper_detail = crud_paper_library.get_test_paper_detail(
        db=db,
        paper_id=new_paper.id,
        teacher_id=teacher_id
    )
    
    return schemas.ApiResponse(
        code="0000",
        message="试卷创建成功",
        data=paper_detail
    )


@router.get("/filter-tags", response_model=schemas.ApiResponse)
async def get_paper_filter_tags(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取试卷筛选标签"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    tags = crud_paper_library.get_paper_filter_tags(db)

    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data=tags
    )


@router.get("/classrooms", response_model=schemas.ApiResponse)
async def get_user_classrooms_for_exam(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取教师的课堂列表，用于创建考试时选择"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    classrooms = crud_paper_library.get_user_classrooms_for_exam(
        db=db,
        teacher_id=teacher_id
    )

    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data={"classrooms": classrooms}
    )


# ==================== 试卷模板相关API ====================

@router.get("/templates", response_model=schemas.ApiResponse)
async def get_paper_templates(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取试卷模板列表"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    templates = crud_paper_library.get_paper_templates(
        db=db,
        teacher_id=teacher_id
    )

    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data=templates
    )


@router.post("/templates", response_model=schemas.ApiResponse)
async def create_paper_template(
    template_request: schemas.PaperTemplateCreateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建试卷模板"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    template_data = template_request.model_dump()

    new_template = crud_paper_library.create_paper_template(
        db=db,
        template_data=template_data,
        creator_id=teacher_id
    )

    return schemas.ApiResponse(
        code="0000",
        message="模板创建成功",
        data={
            "template_id": new_template.id,
            "name": new_template.name
        }
    )


@router.get("/question-pool-stats", response_model=schemas.ApiResponse)
async def get_question_pool_stats(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    direction: Optional[str] = Query(None, description="方向筛选"),
    source: Optional[str] = Query(None, description="来源筛选"),
    template_id: Optional[int] = Query(None, description="模板ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取题库统计信息"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    stats = crud_paper_library.get_question_pool_stats(
        db=db,
        teacher_id=teacher_id,
        direction=direction,
        source=source
    )

    # 如果提供了模板ID，检查是否可以生成试卷
    can_generate = True
    missing_types = []

    if template_id:
        template = db.query(models.PaperTemplate).options(
            joinedload(models.PaperTemplate.question_configs)
        ).filter(
            models.PaperTemplate.id == template_id,
            models.PaperTemplate.is_active == True
        ).first()

        if template:
            for config in template.question_configs:
                q_type = config.question_type.value
                required_count = config.question_count
                available_count = stats["question_type_stats"].get(q_type, 0)

                if available_count < required_count:
                    can_generate = False
                    missing_types.append(f"{q_type}需要{required_count}道，实际{available_count}道")

    stats.update({
        "can_generate": can_generate,
        "missing_types": missing_types
    })

    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data=stats
    )


@router.post("/{paper_id}/copy", response_model=schemas.ApiResponse)
async def copy_test_paper(
    paper_id: int,
    copy_request: schemas.PaperCopyRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """复制试卷"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    new_paper = crud_paper_library.copy_test_paper(
        db=db,
        paper_id=paper_id,
        teacher_id=teacher_id,
        new_title=copy_request.new_title
    )
    
    if not new_paper:
        raise HTTPException(status_code=404, detail="试卷不存在")
    
    return schemas.ApiResponse(
        code="0000",
        message="试卷复制成功",
        data={
            "new_paper_id": new_paper.id,
            "new_title": new_paper.title
        }
    )


@router.delete("/{paper_id}", response_model=schemas.ApiResponse)
async def delete_test_paper(
    paper_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除试卷"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    success = crud_paper_library.delete_test_paper(
        db=db,
        paper_id=paper_id,
        teacher_id=teacher_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="试卷不存在或无权限删除")
    
    return schemas.ApiResponse(
        code="0000",
        message="试卷删除成功"
    )


@router.put("/{paper_id}", response_model=schemas.ApiResponse)
async def update_test_paper(
    paper_id: int,
    update_request: schemas.PaperUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新试卷信息"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    # 验证试卷名称长度
    if update_request.title and len(update_request.title) > 60:
        raise HTTPException(status_code=400, detail="试卷名称不能超过60个字符")
    
    # 构建更新数据
    update_data = {}
    if update_request.title is not None:
        update_data["title"] = update_request.title
    if update_request.direction is not None:
        update_data["direction"] = update_request.direction
    if update_request.difficulty is not None:
        update_data["difficulty"] = update_request.difficulty
    if update_request.description is not None:
        update_data["description"] = update_request.description
    
    updated_paper = crud_paper_library.update_test_paper(
        db=db,
        paper_id=paper_id,
        teacher_id=teacher_id,
        update_data=update_data
    )
    
    if not updated_paper:
        raise HTTPException(status_code=404, detail="试卷不存在或无权限编辑")
    
    return schemas.ApiResponse(
        code="0000",
        message="试卷更新成功"
    )


@router.get("/{paper_id}", response_model=schemas.ApiResponse)
async def get_test_paper_detail(
    paper_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取试卷详情"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    paper_detail = crud_paper_library.get_test_paper_detail(
        db=db,
        paper_id=paper_id,
        teacher_id=teacher_id
    )
    
    if not paper_detail:
        raise HTTPException(status_code=404, detail="试卷不存在或无权限查看")
    
    return schemas.ApiResponse(
        code="0000",
        message="获取成功",
        data=paper_detail
    )


@router.post("/{paper_id}/create-exam", response_model=schemas.ApiResponse)
async def create_exam_from_paper(
    paper_id: int,
    exam_request: schemas.CreateExamFromPaperRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """从试卷创建考试"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    # 验证考试名称长度
    if len(exam_request.exam_title) > 60:
        raise HTTPException(status_code=400, detail="考试名称不能超过60个字符")
    
    new_exam = crud_paper_library.create_exam_from_paper(
        db=db,
        paper_id=paper_id,
        classroom_id=exam_request.classroom_id,
        teacher_id=teacher_id,
        exam_title=exam_request.exam_title
    )
    
    if not new_exam:
        raise HTTPException(status_code=400, detail="创建考试失败，请检查试卷和课堂是否存在")
    
    return schemas.ApiResponse(
        code="0000",
        message="考试创建成功",
        data={
            "exam_id": new_exam.id,
            "exam_title": new_exam.title
        }
    )


@router.post("/{paper_id}/export", response_model=schemas.ApiResponse)
async def export_test_paper(
    paper_id: int,
    export_request: schemas.PaperExportRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """导出试卷"""
    teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
    result = crud_paper_library.export_test_paper_to_word(
        db=db,
        paper_id=paper_id,
        teacher_id=teacher_id
    )
    
    if result["success"]:
        return schemas.ApiResponse(
            code="0000",
            message="导出成功",
            data={
                "filename": result["filename"],
                "download_url": f"/api/v1/paper-library/download/{result['filename']}"
            }
        )
    else:
        raise HTTPException(status_code=500, detail=result["error"])


@router.post("/template-composition", response_model=schemas.ApiResponse)
async def template_composition(
    composition_request: schemas.TemplateCompositionRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """模板组卷"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        paper_data = {
            "title": composition_request.paper_title,
            "description": composition_request.description,
            "difficulty": composition_request.difficulty
        }
        
        new_paper = crud_paper_library.generate_paper_from_template(
            db=db,
            paper_data=paper_data,
            template_id=composition_request.template_id,
            teacher_id=teacher_id,
            direction=composition_request.direction,
            source=composition_request.source
        )
        
        # 获取生成的试卷详情
        paper_detail = crud_paper_library.get_test_paper_detail(
            db=db,
            paper_id=new_paper.id,
            teacher_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="试卷生成成功",
            data=paper_detail
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试卷生成失败: {str(e)}")


# ==================== 试卷编辑相关API ====================

@router.post("/{paper_id}/questions", response_model=schemas.ApiResponse)
async def add_questions_to_paper(
    paper_id: int,
    add_request: schemas.PaperQuestionAddRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """向试卷添加题目"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        added_count = crud_paper_library.add_questions_to_paper(
            db=db,
            paper_id=paper_id,
            question_ids=add_request.question_ids,
            teacher_id=teacher_id,
            scores=add_request.scores
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加{added_count}道题目",
            data={
                "added_count": added_count,
                "question_ids": add_request.question_ids
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加题目失败: {str(e)}")


@router.delete("/{paper_id}/questions", response_model=schemas.ApiResponse)
async def remove_questions_from_paper(
    paper_id: int,
    remove_request: schemas.PaperQuestionRemoveRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """从试卷移除题目"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        removed_count = crud_paper_library.remove_questions_from_paper(
            db=db,
            paper_id=paper_id,
            question_ids=remove_request.question_ids,
            teacher_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功移除{removed_count}道题目",
            data={
                "removed_count": removed_count,
                "question_ids": remove_request.question_ids
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除题目失败: {str(e)}")


@router.put("/{paper_id}/questions/{question_id}", response_model=schemas.ApiResponse)
async def update_paper_question(
    paper_id: int,
    question_id: int,
    update_request: schemas.PaperQuestionUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新试卷中的题目信息"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        update_data = {}
        if update_request.score is not None:
            update_data["score"] = update_request.score
        if update_request.order_index is not None:
            update_data["order_index"] = update_request.order_index
        
        updated_question = crud_paper_library.update_paper_question(
            db=db,
            paper_id=paper_id,
            question_id=question_id,
            teacher_id=teacher_id,
            update_data=update_data
        )

        # 构建标准化的响应数据
        response_data = {
            "paper_id": paper_id,
            "question_id": question_id,
            "score": updated_question.score if hasattr(updated_question, 'score') else update_data.get('score'),
            "order_index": updated_question.order_index if hasattr(updated_question, 'order_index') else update_data.get('order_index'),
            "updated_at": updated_question.updated_at.isoformat() if hasattr(updated_question, 'updated_at') and updated_question.updated_at else None
        }

        return schemas.ApiResponse(
            code="0000",
            message="题目信息更新成功",
            data=response_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新题目信息失败: {str(e)}")


# ==================== 试卷分值设置API ====================

@router.patch("/{paper_id}/questions/{question_id}/score", response_model=schemas.ApiResponse)
async def update_paper_question_score(
    paper_id: int,
    question_id: int,
    score_request: schemas.PaperQuestionScoreUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """单独更新题目分值"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud_paper_library.update_paper_question_score(
            db=db,
            paper_id=paper_id,
            question_id=question_id,
            teacher_id=teacher_id,
            new_score=score_request.score
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="题目分值更新成功",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新题目分值失败: {str(e)}")


@router.patch("/{paper_id}/questions/batch-score", response_model=schemas.ApiResponse)
async def batch_update_paper_questions_score(
    paper_id: int,
    batch_score_request: schemas.PaperBatchScoreUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量设置同类型题目分值"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud_paper_library.batch_update_paper_questions_score(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id,
            question_type=batch_score_request.question_type,
            score_per_question=batch_score_request.score_per_question
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功批量更新{result['updated_count']}道{batch_score_request.question_type}题目分值",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量更新题目分值失败: {str(e)}")


# ==================== 试卷排序API ====================

@router.patch("/{paper_id}/questions/order", response_model=schemas.ApiResponse)
async def update_paper_questions_order(
    paper_id: int,
    order_request: schemas.PaperQuestionOrderUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新题目排序（小题排序）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud_paper_library.update_paper_questions_order(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id,
            question_orders=order_request.question_orders
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功更新{result['updated_count']}道题目排序",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新题目排序失败: {str(e)}")


@router.patch("/{paper_id}/sections/order", response_model=schemas.ApiResponse)
async def update_paper_sections_order(
    paper_id: int,
    section_order_request: schemas.PaperSectionOrderUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新大题排序"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        result = crud_paper_library.update_paper_sections_order(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id,
            section_orders=section_order_request.section_orders
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功更新{len(section_order_request.section_orders)}个大题排序",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新大题排序失败: {str(e)}")


# ==================== 试卷增强详情API ====================

@router.get("/{paper_id}/enhanced-detail", response_model=schemas.ApiResponse)
async def get_paper_enhanced_detail(
    paper_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取增强的试卷详情（包含分组和统计信息）"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        paper_detail = crud_paper_library.get_paper_enhanced_detail(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取试卷详情成功",
            data=paper_detail
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试卷详情失败: {str(e)}")


# ==================== 试卷基本信息编辑API ====================

@router.patch("/{paper_id}/basic-info", response_model=schemas.ApiResponse)
async def update_paper_basic_info(
    paper_id: int,
    basic_info_request: schemas.PaperBasicInfoUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新试卷基本信息"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 构建更新数据
        update_data = {}
        if basic_info_request.title is not None:
            update_data["title"] = basic_info_request.title
        if basic_info_request.direction is not None:
            update_data["direction"] = basic_info_request.direction
        if basic_info_request.difficulty is not None:
            update_data["difficulty"] = basic_info_request.difficulty
        if basic_info_request.description is not None:
            update_data["description"] = basic_info_request.description
        if basic_info_request.estimated_duration_minutes is not None:
            update_data["estimated_duration_minutes"] = basic_info_request.estimated_duration_minutes
        
        updated_paper = crud_paper_library.update_paper_basic_info(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id,
            update_data=update_data
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="试卷基本信息更新成功",
            data=updated_paper
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新试卷基本信息失败: {str(e)}")


# ==================== 试卷导出增强API ====================

@router.post("/{paper_id}/export-enhanced", response_model=schemas.ApiResponse)
async def export_paper_enhanced(
    paper_id: int,
    export_request: schemas.PaperExportRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """增强的试卷导出功能"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 获取试卷详情
        paper_detail = crud_paper_library.get_paper_enhanced_detail(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id
        )
        
        # 生成导出文件
        if export_request.format == "word":
            file_path = crud_paper_library.export_paper_to_word_enhanced(
                db=db,
                paper_id=paper_id,
                teacher_id=teacher_id,
                include_answers=export_request.include_answers
            )
        else:
            raise ValueError("暂不支持该导出格式")
        
        return schemas.ApiResponse(
            code="0000",
            message="试卷导出成功",
            data={
                "file_path": file_path,
                "paper_title": paper_detail["title"],
                "format": export_request.format,
                "include_answers": export_request.include_answers
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出试卷失败: {str(e)}")


# ==================== 试卷完成编辑API ====================

@router.post("/{paper_id}/complete", response_model=schemas.ApiResponse)
async def complete_paper_editing(
    paper_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """完成试卷编辑"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 验证试卷权限
        paper = db.query(models.TestPaper).filter(
            models.TestPaper.id == paper_id,
            models.TestPaper.creator_id == teacher_id,
            models.TestPaper.deleted_at.is_(None)
        ).first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限编辑")
        
        # 检查试卷是否有题目
        question_count = db.query(models.TestPaperQuestion).filter(
            models.TestPaperQuestion.test_paper_id == paper_id
        ).count()
        
        if question_count == 0:
            raise HTTPException(status_code=400, detail="试卷中没有题目，无法完成编辑")
        
        # 获取试卷详情
        paper_detail = crud_paper_library.get_paper_enhanced_detail(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="试卷编辑完成",
            data={
                "paper_id": paper_id,
                "title": paper.title,
                "total_score": paper.total_score,
                "question_count": question_count,
                "sections": paper_detail["sections"],
                "completed_at": paper.updated_at
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完成试卷编辑失败: {str(e)}")


# ==================== 试卷统计信息API ====================

@router.get("/{paper_id}/statistics", response_model=schemas.ApiResponse)
async def get_paper_statistics(
    paper_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取试卷统计信息"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        paper_detail = crud_paper_library.get_paper_enhanced_detail(
            db=db,
            paper_id=paper_id,
            teacher_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="获取试卷统计信息成功",
            data=paper_detail["statistics"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取试卷统计信息失败: {str(e)}")


# ==================== 试卷管理API ====================

@router.get("/{paper_id}/edit-permission", response_model=schemas.ApiResponse)
async def check_paper_edit_permission(
    paper_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """检查试卷编辑权限"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        paper = db.query(models.TestPaper).filter(
            models.TestPaper.id == paper_id,
            models.TestPaper.deleted_at.is_(None)
        ).first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="试卷不存在")
        
        # 检查权限：创建者可以直接编辑，其他人需要复制后编辑
        can_edit = paper.creator_id == teacher_id
        edit_mode = "direct" if paper.creator_id == teacher_id else "copy"
        
        return schemas.ApiResponse(
            code="0000",
            message="权限检查成功",
            data={
                "can_edit": can_edit,
                "edit_mode": edit_mode,  # direct: 直接编辑, copy: 复制后编辑
                "paper_source": "personal",  # 暂时固定为个人试卷
                "is_owner": paper.creator_id == teacher_id
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"权限检查失败: {str(e)}") 