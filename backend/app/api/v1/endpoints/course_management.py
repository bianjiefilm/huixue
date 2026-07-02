"""
课程管理API端点
包含实践课程管理、实训课程管理、课程申请审批等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import app.models.models as models
import app.schemas.course_management as course_management_schemas
import app.schemas.schemas as schemas
import app.crud.course_management_crud as crud
from app.core.database import get_db
from datetime import datetime, timezone
from app.core.auth import get_current_user, require_role

router = APIRouter()

# ==================== 实践课程管理 ====================

@router.get("/practice-courses/categories", response_model=course_management_schemas.CategoryTreeResponse)
async def get_practice_course_categories(db: Session = Depends(get_db)):
    """获取实践课程分类树"""
    categories = crud.get_practice_course_categories(db)
    return course_management_schemas.CategoryTreeResponse(categories=categories)

@router.get("/practice-courses", response_model=course_management_schemas.PracticeCourseListResponse)
async def get_practice_courses(
    category: Optional[str] = Query(None, description="课程分类"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序顺序"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _admin_check: None = Depends(require_role("admin")),
):
    """获取实践课程列表 (Z3 P0-8: admin 视角, 含 PRIVATE 草稿全部 14+1=15 行)"""
    try:
        skip = (page - 1) * page_size

        practices, total = crud.get_practice_courses(
            db=db,
            category=category,
            skip=skip,
            limit=page_size,
            sort_field=sort_field,
            sort_order=sort_order
        )

        # 转换为响应格式
        items = []
        for practice in practices:
            item = course_management_schemas.PracticeCourseItem(
                id=practice.id,
                title=practice.title,
                description=practice.description,
                cover_url=practice.cover_url,
                direction=practice.direction,
                category=practice.category,
                difficulty=practice.difficulty.value if hasattr(practice.difficulty, 'value') and practice.difficulty else None,
                task_count=practice.task_count,
                coin=practice.coin,
                created_at=practice.created_at,
                updated_at=practice.updated_at,
                creator=course_management_schemas.PracticeCourseCreator(
                    id=practice.creator.id,
                    full_name=practice.creator.full_name,
                    username=practice.creator.username
                ) if practice.creator else None,
                publish_status=getattr(practice.publish_status, 'value', 'EDITING') if practice.publish_status else "EDITING",
                visibility=getattr(practice.visibility, 'value', 'PRIVATE') if practice.visibility else "PRIVATE",
                can_unpublish=getattr(practice.visibility, 'value', 'PRIVATE') == 'PUBLIC',
                can_publish=not practice.creator_id
            )
            items.append(item)

        total_pages = (total + page_size - 1) // page_size

        return course_management_schemas.PracticeCourseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实践课程列表失败: {str(e)}")

@router.get("/practice-courses/{course_id}", response_model=course_management_schemas.PracticeCourseDetail)
async def get_practice_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取实践课程详情"""
    practice = crud.get_practice_course_detail(db, course_id)
    if not practice:
        raise HTTPException(status_code=404, detail="课程不存在或未公开发布")
    
    return course_management_schemas.PracticeCourseDetail(
        id=practice.id,
        title=practice.title,
        description=practice.description,
        cover_url=practice.cover_url,
        direction=practice.direction,
        category=practice.category,
        difficulty=practice.difficulty.value if hasattr(practice.difficulty, 'value') and practice.difficulty else None,
        task_count=practice.task_count,
        coin=practice.coin,
        created_at=practice.created_at,
        updated_at=practice.updated_at,
        intro=practice.intro,
        summary=practice.summary,
        practice_type=practice.practice_type,
        environment_id=practice.environment_id,
        storage_limit=practice.storage_limit,
        memory_limit=practice.memory_limit,
        cpu_limit=practice.cpu_limit,
        creator=course_management_schemas.PracticeCourseCreator(
            id=practice.creator.id,
            full_name=practice.creator.full_name,
            username=practice.creator.username
        ) if practice.creator else None,
        can_unpublish=practice.visibility == models.PracticeVisibilityEnum.PUBLIC
    )

@router.post("/practice-courses/action", response_model=course_management_schemas.CourseActionResponse)
async def practice_course_action(
    request: course_management_schemas.CourseActionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_role("admin", "teacher")),
):
    """实践课程操作（发布/下架）"""
    if request.action == "unpublish":
        result = crud.unpublish_practice_course(
            db=db, 
            course_id=request.course_id, 
            operator_id=current_user.id
        )
    elif request.action == "publish":
        result = crud.publish_practice_course(
            db=db, 
            course_id=request.course_id, 
            operator_id=current_user.id
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的操作类型")
    
    return course_management_schemas.CourseActionResponse(
        success=result["success"],
        message=result["message"]
    )

# ==================== 实训课程管理 ====================

@router.get("/training-courses/categories", response_model=course_management_schemas.CategoryTreeResponse)
async def get_training_course_categories(db: Session = Depends(get_db)):
    """获取实训课程分类树"""
    categories = crud.get_training_course_categories(db)
    return course_management_schemas.CategoryTreeResponse(categories=categories)

@router.get("/training-courses", response_model=course_management_schemas.TrainingCourseListResponse)
async def get_training_courses(
    category: Optional[str] = Query(None, description="课程分类"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序顺序"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取实训课程列表"""
    skip = (page - 1) * page_size
    
    trainings, total = crud.get_training_courses(
        db=db,
        category=category,
        skip=skip,
        limit=page_size,
        sort_field=sort_field,
        sort_order=sort_order
    )
    
    # 转换为响应格式
    items = []
    for training in trainings:
        item = course_management_schemas.TrainingCourseItem(
            id=training.id,
            title=training.title,
            intro=training.intro,
            cover_url=training.cover_url,
            industry=training.industry,
            difficulty=training.difficulty.value if training.difficulty else None,
            course_hours=training.course_hours,
            training_type=training.training_type.value if training.training_type else None,
            created_at=training.created_at,
            updated_at=training.updated_at or datetime.now(timezone.utc),
            creator=course_management_schemas.TrainingCourseCreator(
                id=training.creator.id,
                full_name=training.creator.full_name,
                username=training.creator.username
            ) if training.creator else None,
            publish_status=training.publish_status.value if training.publish_status else "EDITING",
            visibility=training.visibility.value if training.visibility else "PRIVATE",
            can_unpublish=training.visibility == models.TrainingVisibilityEnum.PUBLIC,
            can_publish=(not training.creator_id and 
                        training.publish_status == models.TrainingPublishStatusEnum.EDITING)
        )
        items.append(item)
    
    total_pages = (total + page_size - 1) // page_size
    
    return course_management_schemas.TrainingCourseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/training-courses/{course_id}", response_model=course_management_schemas.TrainingCourseDetail)
async def get_training_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取实训课程详情"""
    training = crud.get_training_course_detail(db, course_id)
    if not training:
        raise HTTPException(status_code=404, detail="课程不存在或未公开发布")
    
    return course_management_schemas.TrainingCourseDetail(
        id=training.id,
        title=training.title,
        intro=training.intro,
        industry=training.industry,
        difficulty=training.difficulty.value if training.difficulty else None,
        course_hours=training.course_hours,
        training_type=training.training_type.value if training.training_type else None,
        created_at=training.created_at,
        updated_at=training.updated_at,
        handbook_content=training.handbook_content,
        assignment_nodes=training.assignment_nodes,
        require_design_files=training.require_design_files,
        require_experiment_report=training.require_experiment_report,
        environment_id=training.environment_id,
        storage_limit=training.storage_limit,
        memory_limit=training.memory_limit,
        cpu_limit=training.cpu_limit,
        creator=course_management_schemas.TrainingCourseCreator(
            id=training.creator.id,
            full_name=training.creator.full_name,
            username=training.creator.username
        ) if training.creator else None,
        can_unpublish=training.visibility == models.TrainingVisibilityEnum.PUBLIC
    )

@router.post("/training-courses/action", response_model=course_management_schemas.CourseActionResponse)
async def training_course_action(
    request: course_management_schemas.CourseActionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_role("admin", "teacher")),
):
    """实训课程操作（发布/下架）"""
    if request.action == "unpublish":
        result = crud.unpublish_training_course(
            db=db, 
            course_id=request.course_id, 
            operator_id=current_user.id
        )
    elif request.action == "publish":
        result = crud.publish_training_course(
            db=db, 
            course_id=request.course_id, 
            operator_id=current_user.id
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的操作类型")
    
    return course_management_schemas.CourseActionResponse(
        success=result["success"],
        message=result["message"]
    )

# ==================== 课程审批管理 ====================

@router.get("/course-requests", response_model=course_management_schemas.CourseRequestListResponse)
async def get_course_requests(
    status: Optional[course_management_schemas.RequestStatusEnum] = Query(None, description="申请状态"),
    course_type: Optional[course_management_schemas.CourseTypeEnum] = Query(None, description="课程类型"),
    request_type: Optional[course_management_schemas.RequestTypeEnum] = Query(None, description="申请类型"),
    course_name: Optional[str] = Query(None, description="课程名称"),
    applicant_name: Optional[str] = Query(None, description="申请人姓名"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_field: str = Query("applied_at", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序顺序"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取课程申请列表"""
    skip = (page - 1) * page_size
    
    requests, total = crud.get_course_requests(
        db=db,
        status=status.value if status else None,
        course_type=course_type.value if course_type else None,
        request_type=request_type.value if request_type else None,
        course_name=course_name,
        applicant_name=applicant_name,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size,
        sort_field=sort_field,
        sort_order=sort_order
    )
    
    # 转换为响应格式
    items = []
    for request in requests:
        # 获取课程信息
        if request.course_type == models.CourseTypeEnum.PRACTICE:
            course = db.query(models.Practice).filter(models.Practice.id == request.course_id).first()
        elif request.course_type == models.CourseTypeEnum.TRAINING:
            course = db.query(models.Training).filter(models.Training.id == request.course_id).first()
        else:
            course = None
        
        item = course_management_schemas.CourseRequestItem(
            id=request.id,
            course_id=request.course_id,
            course_type=request.course_type,
            request_type=request.request_type,
            status=request.status,
            application_reason=request.application_reason,
            applied_at=request.applied_at,
            review_comments=request.review_comments,
            reviewed_at=request.reviewed_at,
            course=course_management_schemas.CourseRequestCourse(
                id=course.id,
                title=course.title
            ) if course else course_management_schemas.CourseRequestCourse(id=0, title="未知课程"),
            applicant=course_management_schemas.CourseRequestUser(
                id=request.applicant.id,
                full_name=request.applicant.full_name,
                username=request.applicant.username
            ),
            reviewer=course_management_schemas.CourseRequestUser(
                id=request.reviewer.id,
                full_name=request.reviewer.full_name,
                username=request.reviewer.username
            ) if request.reviewer else None,
            course_type_text=crud.get_course_type_text(request.course_type),
            request_type_text=crud.get_request_type_text(request.request_type),
            status_text=crud.get_request_status_text(request.status),
            can_approve=request.status == models.CourseRequestStatusEnum.PENDING,
            can_reject=request.status == models.CourseRequestStatusEnum.PENDING,
            can_view_detail=True
        )
        items.append(item)
    
    total_pages = (total + page_size - 1) // page_size
    
    return course_management_schemas.CourseRequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/course-requests/{request_id}", response_model=course_management_schemas.CourseRequestDetail)
async def get_course_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取课程申请详情"""
    request = crud.get_course_request_detail(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    
    # 获取课程信息
    if request.course_type == models.CourseTypeEnum.PRACTICE:
        course = db.query(models.Practice).filter(models.Practice.id == request.course_id).first()
    elif request.course_type == models.CourseTypeEnum.TRAINING:
        course = db.query(models.Training).filter(models.Training.id == request.course_id).first()
    else:
        course = None
    
    return course_management_schemas.CourseRequestDetail(
        id=request.id,
        course_id=request.course_id,
        course_type=request.course_type,
        request_type=request.request_type,
        status=request.status,
        application_reason=request.application_reason,
        applied_at=request.applied_at,
        review_comments=request.review_comments,
        reviewed_at=request.reviewed_at,
        cancelled_reason=request.cancelled_reason,
        cancelled_at=request.cancelled_at,
        course=course_management_schemas.CourseRequestCourse(
            id=course.id,
            title=course.title
        ) if course else course_management_schemas.CourseRequestCourse(id=0, title="未知课程"),
        applicant=course_management_schemas.CourseRequestUser(
            id=request.applicant.id,
            full_name=request.applicant.full_name,
            username=request.applicant.username
        ),
        reviewer=course_management_schemas.CourseRequestUser(
            id=request.reviewer.id,
            full_name=request.reviewer.full_name,
            username=request.reviewer.username
        ) if request.reviewer else None,
        course_type_text=crud.get_course_type_text(request.course_type),
        request_type_text=crud.get_request_type_text(request.request_type),
        status_text=crud.get_request_status_text(request.status),
        can_approve=request.status == models.CourseRequestStatusEnum.PENDING,
        can_reject=request.status == models.CourseRequestStatusEnum.PENDING
    )

@router.post("/course-requests/{request_id}/approve", response_model=course_management_schemas.CourseActionResponse)
async def approve_course_request(
    request_id: int,
    request: course_management_schemas.CourseRequestApprovalRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_role("admin", "teacher")),
):
    """同意课程申请"""
    if request.action == "approve":
        result = crud.approve_course_request(
            db=db,
            request_id=request_id,
            reviewer_id=current_user.id,
            review_comments=request.review_comments
        )
    elif request.action == "reject":
        result = crud.reject_course_request(
            db=db,
            request_id=request_id,
            reviewer_id=current_user.id,
            review_comments=request.review_comments
        )
    else:
        raise HTTPException(status_code=400, detail="不支持的操作类型")
    
    return course_management_schemas.CourseActionResponse(
        success=result["success"],
        message=result["message"]
    )

@router.post("/course-requests", response_model=course_management_schemas.CourseActionResponse)
async def submit_course_request(
    request: course_management_schemas.CourseRequestSubmitRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """提交课程申请"""
    result = crud.submit_course_request(
        db=db,
        course_id=request.course_id,
        course_type=request.course_type.value,
        applicant_id=current_user.id,
        request_type=request.request_type.value,
        application_reason=request.application_reason
    )
    
    return course_management_schemas.CourseActionResponse(
        success=result["success"],
        message=result["message"]
    )

@router.post("/course-requests/{request_id}/cancel", response_model=course_management_schemas.CourseActionResponse)
async def cancel_course_request(
    request_id: int,
    request: course_management_schemas.CourseRequestCancelRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """撤销课程申请"""
    result = crud.cancel_course_request(
        db=db,
        request_id=request_id,
        applicant_id=current_user.id,
        cancel_reason=request.cancel_reason
    )
    
    return course_management_schemas.CourseActionResponse(
        success=result["success"],
        message=result["message"]
    )

# ==================== 统计信息 ====================

@router.get("/stats", response_model=schemas.CourseManagementStatsResponse)
async def get_course_management_stats(db: Session = Depends(get_db)):
    """获取课程管理统计信息"""
    try:
        stats = crud.get_course_management_stats(db)
        return schemas.CourseManagementStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# ==================== 分类树 ====================

@router.get("/category-tree")
async def get_category_tree(
    course_type: Optional[str] = Query(None, description="课程类型"),
    db: Session = Depends(get_db)
):
    """获取课程分类树"""
    try:
        tree = crud.get_course_category_tree(db, course_type)
        return {"tree": tree}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类树失败: {str(e)}") 
