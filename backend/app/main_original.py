from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uvicorn
import uuid
import logging
from datetime import datetime, timezone, timedelta

from database import get_db, engine, Base
from models import User, Post
import crud
import schemas
import models

# 配置日志
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="慧学 API",
    description="基于FastAPI和PostgreSQL的后端API - 课程实践模块",
    version="1.0.0"
)

# 根路径
@app.get("/")
async def root():
    return {"message": "欢迎使用慧学 API", "status": "运行中"}

# 健康检查
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # 测试数据库连接
        db.execute("SELECT 1")
        
        # 如果连接成功，创建数据库表
        try:
            Base.metadata.create_all(bind=engine)
            return {"status": "健康", "database": "已连接", "tables": "已创建"}
        except Exception as table_error:
            return {"status": "健康", "database": "已连接", "tables": f"创建失败: {str(table_error)}"}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"数据库连接失败: {str(e)}"
        )

# ==================== 课程实践相关API ====================

# 4.1 课程资源库
@app.get("/api/v1/courses", response_model=schemas.ApiResponse)
def get_courses(
    keyword: Optional[str] = Query(None, description="模糊搜索关键字"),
    direction: Optional[List[str]] = Query(None, description="方向标签，可多选"),
    category: Optional[List[str]] = Query(None, description="分类标签，可多选"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """查询课程教材列表"""
    try:
        skip = (page - 1) * page_size
        courses, total = crud.get_courses(
            db=db,
            skip=skip,
            limit=page_size,
            keyword=keyword,
            directions=direction,
            categories=category,
            difficulty=difficulty
        )
        
        course_list = [schemas.CourseResponse.model_validate(course) for course in courses]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": [course.model_dump() for course in course_list],
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 获取课程筛选标签（用于课程选择页面）
@app.get("/api/v1/courses/filter-tags", response_model=schemas.ApiResponse)
def get_course_filter_tags(
    course_type: Optional[str] = Query(None, description="课程类型：practice, training, course_material"),
    db: Session = Depends(get_db)
):
    """获取课程筛选标签（用于课程选择页面）"""
    try:
        filter_tags = crud.get_course_filter_tags_for_selection(db, course_type)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=filter_tags
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 获取课程库中的课程（用于添加课程时选择）
@app.get("/api/v1/courses/library", response_model=schemas.ApiResponse)
def get_course_library(
    course_type: Optional[str] = Query(None, description="课程类型：practice, training, course_material"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    direction: Optional[str] = Query(None, description="方向标签"),
    category: Optional[str] = Query(None, description="分类标签"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取课程库中的课程列表（用于课程选择）"""
    try:
        skip = (page - 1) * page_size
        courses, total = crud.get_courses_for_library(
            db=db,
            course_type=course_type,
            keyword=keyword,
            direction=direction,
            category=category,
            difficulty=difficulty,
            skip=skip,
            limit=page_size
        )
        
        # 获取筛选标签
        filter_tags = crud.get_course_filter_tags_for_selection(db, course_type)
        
        # 转换为响应格式
        course_list = []
        for course in courses:
            course_data = schemas.CourseSelectionResponse.model_validate(course)
            course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": course_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "filter_tags": filter_tags
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}", response_model=schemas.ApiResponse)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    """课程教材详情"""
    try:
        course = crud.get_course(db, course_id=course_id)
        if course is None:
            return schemas.ApiResponse(
                code="1002",
                message="资源不存在",
                trace_id=str(uuid.uuid4())
            )
        
        course_detail = schemas.CourseDetailResponse.model_validate(course)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=course_detail.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}/outline", response_model=schemas.ApiResponse)
def get_course_outline(course_id: int, db: Session = Depends(get_db)):
    """获取课程教学大纲"""
    try:
        outline = crud.get_course_outline(db, course_id=course_id)
        if outline is None:
            return schemas.ApiResponse(
                code="1002",
                message="教学大纲不存在",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=outline
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}/resources", response_model=schemas.ApiResponse)
def get_course_resources(course_id: int, db: Session = Depends(get_db)):
    """获取课程教学资源"""
    try:
        resources = crud.get_course_resources(db, course_id=course_id)
        resource_list = [schemas.CourseResourceResponse.model_validate(resource) for resource in resources]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=[resource.model_dump() for resource in resource_list]
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}/assessments", response_model=schemas.ApiResponse)
def get_course_assessments(course_id: int, db: Session = Depends(get_db)):
    """获取课程考核"""
    try:
        assessments = crud.get_course_assessments(db, course_id=course_id)
        assessment_list = [schemas.CourseAssessmentResponse.model_validate(assessment) for assessment in assessments]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=[assessment.model_dump() for assessment in assessment_list]
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.3 微型实验库
@app.get("/api/v1/practices", response_model=schemas.ApiResponse)
def get_practices(
    keyword: Optional[str] = Query(None, description="模糊搜索关键字"),
    direction: Optional[str] = Query(None, description="一级方向"),
    category: Optional[str] = Query(None, description="二级分类"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """查询微型实验列表"""
    try:
        skip = (page - 1) * page_size
        practices, total = crud.get_practices(
            db=db,
            skip=skip,
            limit=page_size,
            keyword=keyword,
            direction=direction,
            category=category,
            difficulty=difficulty
        )
        
        practice_list = [schemas.PracticeResponse.model_validate(practice) for practice in practices]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": [practice.model_dump() for practice in practice_list],
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/practices/{practice_id}", response_model=schemas.ApiResponse)
def get_practice_detail(practice_id: int, db: Session = Depends(get_db)):
    """实践详情 - 包含任务列表、技能标签和推荐实践"""
    try:
        # 获取实践详情
        practice = crud.get_practice_detail(db, practice_id=practice_id)
        if practice is None:
            return schemas.ApiResponse(
                code="1002",
                message="资源不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取推荐实践
        recommended_practices = crud.get_recommended_practices(db, practice_id=practice_id, limit=5)
        recommended_list = [schemas.PracticeResponse.model_validate(p) for p in recommended_practices]
        
        # 构建响应数据
        practice_detail = schemas.PracticeDetailResponse.model_validate(practice)
        response_data = practice_detail.model_dump()
        response_data["recommended_practices"] = [p.model_dump() for p in recommended_list]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=response_data
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/practices/{practice_id}/tasks", response_model=schemas.ApiResponse)
def get_practice_tasks(
    practice_id: int,
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
        
        task_list = [schemas.TaskResponse.model_validate(task) for task in tasks]
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": [task.model_dump() for task in task_list],
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 课堂管理
@app.get("/api/v1/classrooms", response_model=schemas.ApiResponse)
def get_classrooms(
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    status: Optional[str] = Query(None, description="课堂状态筛选，可选值：ongoing, upcoming, ended"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取课堂列表
    - 如果指定teacher_id且不指定status，返回按状态分组的课堂列表
    - 如果同时指定teacher_id和status，返回指定状态的课堂列表  
    - 如果不指定teacher_id，返回所有课堂的分页列表
    """
    try:
        if teacher_id and not status:
            # 按状态分组返回课堂列表
            classrooms_by_status = crud.get_classrooms_by_status(db, teacher_id)
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data=classrooms_by_status.model_dump()
            )
        elif teacher_id and status:
            # 返回指定状态的课堂
            classrooms_by_status = crud.get_classrooms_by_status(db, teacher_id)
            
            if status == "ongoing":
                filtered_classrooms = classrooms_by_status.ongoing
            elif status == "upcoming":
                filtered_classrooms = classrooms_by_status.upcoming
            elif status == "ended":
                filtered_classrooms = classrooms_by_status.ended
            else:
                return schemas.ApiResponse(
                    code="1001",
                    message="无效的状态参数",
                    trace_id=str(uuid.uuid4())
                )
            
            # 分页处理
            skip = (page - 1) * page_size
            total = len(filtered_classrooms)
            paginated_classrooms = filtered_classrooms[skip:skip + page_size]
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data={
                    "list": [classroom.model_dump() for classroom in paginated_classrooms],
                    "meta": {
                        "total": total,
                        "page": page,
                        "page_size": page_size
                    }
                }
            )
        else:
            # 原有逻辑：返回所有课堂的分页列表
            skip = (page - 1) * page_size
            classrooms, total = crud.get_classrooms(
                db=db,
                teacher_id=teacher_id,
                skip=skip,
                limit=page_size
            )
            
            classroom_list = [schemas.ClassroomDetailResponse.model_validate(classroom) for classroom in classrooms]
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data={
                    "list": [classroom.model_dump() for classroom in classroom_list],
                    "meta": {
                        "total": total,
                        "page": page,
                        "page_size": page_size
                    }
                }
            )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/classrooms/{classroom_id}", response_model=schemas.ApiResponse)
def get_classroom_detail(
    classroom_id: int, 
    enhanced: bool = Query(False, description="是否返回增强版详情"),
    db: Session = Depends(get_db)
):
    """
    课堂详情
    - enhanced=true: 返回包含统计信息的增强版详情
    - enhanced=false: 返回基础详情
    """
    try:
        if enhanced:
            classroom_detail = crud.get_classroom_detail_enhanced(db, classroom_id)
            if classroom_detail is None:
                return schemas.ApiResponse(
                    code="1002",
                    message="课堂不存在",
                    trace_id=str(uuid.uuid4())
                )
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data=classroom_detail.model_dump()
            )
        else:
            classroom = crud.get_classroom(db, classroom_id=classroom_id)
            if classroom is None:
                return schemas.ApiResponse(
                    code="1002",
                    message="课堂不存在",
                    trace_id=str(uuid.uuid4())
                )
            
            classroom_detail = schemas.ClassroomDetailResponse.model_validate(classroom)
            
            return schemas.ApiResponse(
                code="0000",
                message="success",
                data=classroom_detail.model_dump()
            )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms", response_model=schemas.ApiResponse)
def create_classroom(
    classroom: schemas.ClassroomCreate,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """创建课堂"""
    try:
        db_classroom = crud.create_classroom(db=db, classroom=classroom, teacher_id=teacher_id)
        
        if db_classroom is None:
            # 检查具体错误原因
            existing = crud.get_classrooms(db, teacher_id=teacher_id)
            for existing_classroom, _ in [existing]:
                for c in existing_classroom:
                    if c.name == classroom.name:
                        return schemas.ApiResponse(
                            code="1005",
                            message="课堂名称已存在",
                            trace_id=str(uuid.uuid4())
                        )
            
            return schemas.ApiResponse(
                code="1006",
                message="业务校验失败：结束日期必须晚于开始日期",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课堂创建成功",
            data={"classroom_id": db_classroom.id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.put("/api/v1/classrooms/{classroom_id}", response_model=schemas.ApiResponse)
def update_classroom(
    classroom_id: int,
    classroom_update: schemas.ClassroomUpdateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """编辑课堂"""
    try:
        result = crud.update_classroom(db, classroom_id, classroom_update, teacher_id)
        
        if result is None:
            return schemas.ApiResponse(
                code="1003",
                message="权限不足或课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        elif isinstance(result, str):
            # 返回的是错误消息
            return schemas.ApiResponse(
                code="1006",
                message=result,
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课堂更新成功",
            data={"classroom_id": result.id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.delete("/api/v1/classrooms/{classroom_id}", response_model=schemas.ApiResponse)
def delete_classroom(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除课堂（软删除）"""
    try:
        # 检查权限
        if not crud.check_teacher_classroom_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1003",
                message="权限不足或课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        classroom = crud.get_classroom(db, classroom_id)
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查是否已经是软删除状态
        if classroom.deleted_at:
            return schemas.ApiResponse(
                code="1007",
                message="课堂已删除",
                trace_id=str(uuid.uuid4())
            )
        
        # 执行软删除
        classroom.deleted_at = datetime.now(timezone.utc)
        db.commit()
        
        return schemas.ApiResponse(
            code="0000",
            message="课堂删除成功"
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/my-classrooms", response_model=schemas.ApiResponse)
def get_my_classrooms(
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """我的课堂 - 按状态分组显示"""
    try:
        classrooms_by_status = crud.get_classrooms_by_status(db, teacher_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=classrooms_by_status.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 筛选标签和统计
@app.get("/api/v1/filter-tags/courses", response_model=schemas.ApiResponse)
def get_course_filter_tags(db: Session = Depends(get_db)):
    """获取课程筛选标签"""
    try:
        tags = crud.get_filter_tags(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=tags
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/filter-tags/practices", response_model=schemas.ApiResponse)
def get_practice_filter_tags(db: Session = Depends(get_db)):
    """获取微型实验筛选标签"""
    try:
        tags = crud.get_practice_filter_tags(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=tags
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/statistics", response_model=schemas.ApiResponse)
def get_statistics(db: Session = Depends(get_db)):
    """获取统计信息"""
    try:
        stats = crud.get_statistics(db)
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=stats
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 原有用户和文章API ====================

# 用户相关API
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user

@app.delete("/users/{user_id}", response_model=schemas.MessageResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "用户删除成功"}

# 文章相关API
@app.post("/posts/", response_model=schemas.PostResponse)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    return crud.create_post(db=db, post=post)

@app.get("/posts/", response_model=List[schemas.PostResponse])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts

@app.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.get_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return db_post

@app.delete("/posts/{post_id}", response_model=schemas.MessageResponse)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.delete_post(db, post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"message": "文章删除成功"}

# 添加实践到课堂
@app.post("/api/v1/classrooms/{classroom_id}/practices", response_model=schemas.ApiResponse)
def add_practice_to_classroom(
    classroom_id: int,
    request: schemas.AddPracticeToClassroomRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """将实践添加到课堂"""
    try:
        # 检查教师权限
        if not crud.check_teacher_classroom_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1003",
                message="权限不足：只有课堂创建者可以添加实践",
                trace_id=str(uuid.uuid4())
            )
        
        # 添加实践到课堂
        result = crud.add_practice_to_classroom(
            db=db,
            classroom_id=classroom_id,
            practice_id=request.practice_id,
            sync_doc=request.sync_doc
        )
        
        if result is None:
            # 检查具体失败原因
            classroom = crud.get_classroom(db, classroom_id)
            if not classroom:
                return schemas.ApiResponse(
                    code="1002",
                    message="课堂不存在",
                    trace_id=str(uuid.uuid4())
                )
            
            practice = crud.get_practice(db, request.practice_id)
            if not practice:
                return schemas.ApiResponse(
                    code="1002",
                    message="实践不存在",
                    trace_id=str(uuid.uuid4())
                )
            
            return schemas.ApiResponse(
                code="1004",
                message="该实践已存在于课堂中",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="实践添加成功",
            data={"classroom_practice_id": result.id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 关卡详情相关API ====================

# 4.5.1 查询关卡详情 - 返回完整的关卡信息
@app.get("/api/v1/tasks/{task_id}", response_model=schemas.ApiResponse)
def get_task_detail(
    task_id: int, 
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
        
        # 映射环境类型
        env_type_mapping = {
            "CODING_ONLINE": "code",
            "HTML_PREVIEW": "html", 
            "COMMAND_LINE": "shell",
            "CLOUD_DESKTOP": "desktop"
        }
        
        # 映射状态
        status_mapping = {
            "未开始": "not_started",
            "进行中": "in_progress", 
            "已完成": "passed"
        }
        
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
                "tests": len(tests)
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.2 列出测试集
@app.get("/api/v1/tasks/{task_id}/tests", response_model=schemas.ApiResponse)
def get_task_tests(
    task_id: int, 
    revealAll: bool = Query(False, description="是否包含隐藏测试集（仅教师可true）"),
    user_role: str = Query("student", description="用户角色"),
    db: Session = Depends(get_db)
):
    """按需拉取全部或公开测试集明细"""
    try:
        tests = crud.get_task_tests(db, task_id=task_id)
        
        test_list = []
        for test in tests:
            # 权限检查：只有教师可以查看隐藏测试集
            if test.is_hidden and not (revealAll and user_role in ["teacher", "assistant"]):
                continue
                
            test_data = {
                "caseId": test.id,
                "hidden": test.is_hidden
            }
            
            # 隐藏测试用例不返回输入输出内容（除非是教师且revealAll=true）
            if not test.is_hidden or (revealAll and user_role in ["teacher", "assistant"]):
                test_data["input"] = test.input_data or ""
                test_data["expected"] = test.expected_output or ""
            
            test_list.append(test_data)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=test_list  # 直接返回数组，不包装在tests字段中
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.3 在线自动评测
@app.post("/api/v1/tasks/{task_id}/evaluate", response_model=schemas.ApiResponse)
def submit_task_evaluation(
    task_id: int,
    request: schemas.TaskEvaluationRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """提交代码仓库当前快照哈希触发判题"""
    try:
        # 获取代码仓库hash，优先使用codeRepoHash，其次使用repo_hash
        repo_hash = request.codeRepoHash or request.repo_hash
        
        submission_data = {
            "answer": request.answer,
            "code": request.code,
            "repo_hash": repo_hash,
            "files": {}
        }
        
        result = crud.submit_task_evaluation(
            db, task_id=task_id, user_id=user_id, submission_data=submission_data
        )
        
        # 格式化响应数据
        response_data = {
            "status": result["status"],
            "score": result["score"],
            "elapsed": result.get("execution_time", 0) / 1000.0,  # 转换为秒
            "logs": result.get("error_message", "") or "评测完成"
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.4 保存代码快照
@app.post("/api/v1/tasks/{task_id}/snapshots", response_model=schemas.ApiResponse)
def save_code_snapshot(
    task_id: int,
    request: schemas.CodeSnapshotRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """在评测或离开页面时保存当前代码"""
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 实践环境相关API ====================

# 4.6.1 通用Session操作
@app.post("/api/v1/sessions/{session_id}/close", response_model=schemas.ApiResponse)
def close_session(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """正常结束并释放资源"""
    try:
        # 这里应该实现实际的session关闭逻辑
        return schemas.ApiResponse(
            code="0000",
            message="Session已关闭",
            data={"session_id": session_id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/heartbeat", response_model=schemas.ApiResponse)
def session_heartbeat(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """前端每60s调用，若超时则容器自动回收"""
    try:
        # 这里应该实现实际的心跳续期逻辑
        return schemas.ApiResponse(
            code="0000",
            message="心跳续期成功",
            data={"session_id": session_id, "expires_in": 3600}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.2 在线编码环境操作
@app.patch("/api/v1/sessions/{session_id}/font-size", response_model=schemas.ApiResponse)
def adjust_font_size(
    session_id: str,
    request: schemas.FontSizeRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """字号调整"""
    try:
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/reset-code", response_model=schemas.ApiResponse)
def reset_all_code(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """重置全部代码 - 仓库回到初始化提交"""
    try:
        return schemas.ApiResponse(
            code="0000",
            message="全部代码已重置",
            data={"session_id": session_id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/reset-file", response_model=schemas.ApiResponse)
def reset_current_file(
    session_id: str,
    request: schemas.ResetFileRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """重置当前文件 - 仅回滚单文件"""
    try:
        file_path = request.path
        return schemas.ApiResponse(
            code="0000",
            message=f"文件 {file_path} 已重置",
            data={"session_id": session_id, "path": file_path}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/restore-pass", response_model=schemas.ApiResponse)
def restore_pass_code(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """回溯至通关代码 - 通关后可用"""
    try:
        # 这里应该检查用户是否已通关
        return schemas.ApiResponse(
            code="0000",
            message="已恢复至通关代码",
            data={"session_id": session_id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.3 HTML前端实践环境操作
@app.post("/api/v1/sessions/{session_id}/toggle-preview", response_model=schemas.ApiResponse)
def toggle_preview(
    session_id: str,
    request: schemas.TogglePreviewRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """开关实时预览"""
    try:
        enabled = request.enabled
        return schemas.ApiResponse(
            code="0000",
            message="预览状态已更新",
            data={"session_id": session_id, "preview_enabled": enabled}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.patch("/api/v1/sessions/{session_id}/preview-size", response_model=schemas.ApiResponse)
def adjust_preview_size(
    session_id: str,
    request: schemas.PreviewSizeRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """窗口尺寸调整"""
    try:
        width = request.width
        height = request.height
        return schemas.ApiResponse(
            code="0000",
            message="预览窗口尺寸已调整",
            data={"session_id": session_id, "width": width, "height": height}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.4 命令行环境操作
@app.post("/api/v1/sessions/{session_id}/reset-shell", response_model=schemas.ApiResponse)
def reset_shell(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """重置命令行 - 重新启动终端并清空历史"""
    try:
        return schemas.ApiResponse(
            code="0000",
            message="命令行已重置",
            data={"session_id": session_id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6.5 云桌面环境操作
@app.post("/api/v1/sessions/{session_id}/extend", response_model=schemas.ApiResponse)
def extend_session(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """延时 - 默认+30min"""
    try:
        return schemas.ApiResponse(
            code="0000",
            message="会话已延时30分钟",
            data={"session_id": session_id, "extended_minutes": 30}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/clipboard", response_model=schemas.ApiResponse)
def sync_clipboard(
    session_id: str,
    request: schemas.ClipboardRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """剪切板同步 - 双向剪贴板"""
    try:
        content = request.content
        return schemas.ApiResponse(
            code="0000",
            message="剪切板同步成功",
            data={"session_id": session_id, "content_length": len(content)}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/fullscreen", response_model=schemas.ApiResponse)
def toggle_fullscreen(
    session_id: str,
    request: schemas.FullscreenRequest,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """全屏/退出 - 切换显示模式"""
    try:
        enabled = request.enabled
        return schemas.ApiResponse(
            code="0000",
            message="全屏状态已更新",
            data={"session_id": session_id, "fullscreen": enabled}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/reset-env", response_model=schemas.ApiResponse)
def reset_environment(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """重置环境 - 保留持久化路径，其他全部还原"""
    try:
        return schemas.ApiResponse(
            code="0000",
            message="环境已重置",
            data={"session_id": session_id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/sessions/{session_id}/reset-task", response_model=schemas.ApiResponse)
def reset_task_files(
    session_id: str,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """重置任务文件 - 仅回滚学生代码区"""
    try:
        return schemas.ApiResponse(
            code="0000",
            message="任务文件已重置",
            data={"session_id": session_id}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 保留参考答案接口作为独立功能
@app.get("/api/v1/tasks/{task_id}/answer", response_model=schemas.ApiResponse)
def get_task_answer(
    task_id: int, 
    user_id: int = Query(..., description="用户ID"),
    user_role: str = Query("student", description="用户角色"),
    db: Session = Depends(get_db)
):
    """获取参考答案，教师或已通关学生可查看"""
    try:
        answer = crud.get_task_answer(db, task_id=task_id, user_id=user_id, user_role=user_role)
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课程状态相关API ====================

@app.get("/api/v1/classrooms/{classroom_id}/courses", response_model=schemas.ApiResponse)
def get_classroom_courses(
    classroom_id: int,
    status: Optional[str] = Query(None, description="状态筛选：all, unpublished, learning, makeup, completed"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID（用于权限验证）"),
    db: Session = Depends(get_db)
):
    """获取课堂中的课程列表（支持状态筛选）"""
    try:
        skip = (page - 1) * page_size
        courses, total = crud.get_classroom_courses(
            db=db,
            classroom_id=classroom_id,
            status=status,
            keyword=keyword,
            skip=skip,
            limit=page_size
        )
        
        # 获取状态统计
        summary = crud.get_classroom_course_status_summary(db, classroom_id)
        
        # 转换为响应格式
        course_list = []
        for classroom_course in courses:
            course_data = schemas.ClassroomCourseDetailResponse.model_validate(classroom_course)
            course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "courses": course_list,
                "summary": summary,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/courses", response_model=schemas.ApiResponse)
def add_course_to_classroom(
    classroom_id: int,
    course_id: int = Query(..., description="课程ID"),
    classroom_chapter_title: Optional[str] = Query(None, description="课堂章节标题"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """添加课程到课堂"""
    try:
        classroom_course = crud.add_course_to_classroom(
            db=db,
            classroom_id=classroom_id,
            course_id=course_id,
            teacher_id=teacher_id,
            classroom_chapter_title=classroom_chapter_title
        )
        
        if classroom_course is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程添加成功",
            data=course_data.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/courses/publish", response_model=schemas.ApiResponse)
def publish_classroom_courses(
    classroom_id: int,
    request: schemas.CourseBatchOperationRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """批量发布课程"""
    try:
        success = crud.publish_classroom_courses(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id
        )
        
        if not success:
            return schemas.ApiResponse(
                code="1001",
                message="发布失败，课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课程发布成功"
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.delete("/api/v1/classrooms/{classroom_id}/courses", response_model=schemas.ApiResponse)
def delete_classroom_courses(
    classroom_id: int,
    request: schemas.CourseBatchOperationRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """批量删除课程（仅限未发布的课程）"""
    try:
        success = crud.delete_classroom_courses(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id
        )
        
        if not success:
            return schemas.ApiResponse(
                code="1001",
                message="删除失败，课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课程删除成功"
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/classrooms/{classroom_id}/courses/summary", response_model=schemas.ApiResponse)
def get_classroom_course_summary(
    classroom_id: int,
    teacher_id: Optional[int] = Query(None, description="教师ID（用于权限验证）"),
    db: Session = Depends(get_db)
):
    """获取课堂课程状态统计"""
    try:
        summary = crud.get_classroom_course_status_summary(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=summary
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 学生端课程状态API
@app.get("/api/v1/classrooms/{classroom_id}/my-courses", response_model=schemas.ApiResponse)
def get_student_classroom_courses(
    classroom_id: int,
    status: Optional[str] = Query(None, description="状态筛选：all, not_started, learning, pending_makeup, completed"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    student_id: int = Query(..., description="学生ID"),
    db: Session = Depends(get_db)
):
    """获取学生在课堂中的课程列表（学生端）"""
    try:
        # 基础查询：只显示已发布的课程
        query = db.query(models.ClassroomCourse).options(
            joinedload(models.ClassroomCourse.course)
        ).filter(
            models.ClassroomCourse.classroom_id == classroom_id,
            models.ClassroomCourse.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED
        )
        
        # 关键词搜索
        if keyword:
            query = query.join(models.Course).filter(
                or_(
                    models.Course.title.ilike(f"%{keyword}%"),
                    models.ClassroomCourse.classroom_chapter_title.ilike(f"%{keyword}%")
                )
            )
        
        # 获取学生进度信息
        skip = (page - 1) * page_size
        classroom_courses = query.order_by(
            models.ClassroomCourse.order_in_classroom, 
            models.ClassroomCourse.id
        ).offset(skip).limit(page_size).all()
        
        # 构建响应数据
        course_list = []
        for classroom_course in classroom_courses:
            # 获取学生进度
            progress = crud.get_student_course_progress(
                db, classroom_course.id, student_id
            )
            
            course_data = {
                "id": classroom_course.id,
                "course_id": classroom_course.course_id,
                "title": classroom_course.classroom_chapter_title or classroom_course.course.title,
                "course_type": classroom_course.course.course_type,
                "cover_url": classroom_course.course.cover_url,
                "difficulty": classroom_course.course.difficulty,
                "teacher_status": classroom_course.teacher_publish_status,
                "student_status": progress.student_status if progress else models.CourseInClassroomStatusStudentEnum.NOT_STARTED,
                "deadline_at": classroom_course.deadline_at,
                "makeup_deadline_at": classroom_course.makeup_deadline_at,
                "is_mandatory": classroom_course.is_mandatory,
                "total_score": classroom_course.total_score,
                "student_score": progress.final_calculated_score if progress else 0,
                "completed_task_count": progress.completed_task_count if progress else 0,
                "total_time_spent_seconds": progress.total_time_spent_seconds if progress else 0,
                "first_access_at": progress.first_access_at if progress else None,
                "last_submission_at": progress.last_submission_at if progress else None
            }
            
            # 状态筛选
            if status and status != "all":
                student_status = course_data["student_status"]
                if status == "not_started" and student_status != models.CourseInClassroomStatusStudentEnum.NOT_STARTED:
                    continue
                elif status == "learning" and student_status != models.CourseInClassroomStatusStudentEnum.LEARNING:
                    continue
                elif status == "pending_makeup" and student_status != models.CourseInClassroomStatusStudentEnum.PENDING_MAKEUP:
                    continue
                elif status == "completed" and student_status not in [
                    models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME,
                    models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                ]:
                    continue
            
            course_list.append(course_data)
        
        total = len(course_list)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "courses": course_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课程详情相关API ====================

@app.get("/api/v1/courses/{course_id}/detail", response_model=schemas.ApiResponse)
def get_course_detail_for_classroom(
    course_id: int,
    user_id: int = Query(..., description="用户ID"),
    user_role: str = Query("student", description="用户角色：teacher, student"),
    classroom_id: Optional[int] = Query(None, description="课堂ID（从课堂进入时必填）"),
    db: Session = Depends(get_db)
):
    """
    4.1.4 课程详情API
    
    功能简介：用户可点击课程名称进入课程详情页面，对于实践和实训课程，
    课程详情页都包含课程的一些基本信息，包括课程标题，课程状态，完成该课程
    可获得的金币数，各状态下的学生人数，课程难易程度，课程起止时间，以及课
    程剩余时间。
    
    支持：
    - 4.1.4.1 教师端实践详情
    - 4.1.4.2 学生端实践详情  
    - 4.1.4.3 教师端实训详情
    - 4.1.4.4 学生端实训详情
    """
    try:
        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        if not course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 如果指定了课堂ID，验证课程是否在该课堂中
        if classroom_id:
            classroom_course = db.query(models.ClassroomCourse).filter(
                models.ClassroomCourse.classroom_id == classroom_id,
                models.ClassroomCourse.course_id == course_id
            ).first()
            
            if not classroom_course:
                return schemas.ApiResponse(
                    code="1002",
                    message="课程不在指定课堂中",
                    trace_id=str(uuid.uuid4())
                )
        
        # 获取Banner信息
        banner_data = crud.get_course_detail_banner(
            db=db, 
            course_id=course_id, 
            classroom_id=classroom_id,
            user_id=user_id
        )
        
        # 获取任务列表及进度
        tasks_data = crud.get_course_tasks_with_progress(
            db=db,
            course_id=course_id,
            user_id=user_id,
            user_role=user_role
        )
        
        # 获取技能标签及点亮状态
        skills_data = crud.get_course_skills_with_progress(
            db=db,
            course_id=course_id,
            user_id=user_id,
            user_role=user_role
        )
        
        # 获取学习统计
        learning_stats = crud.get_course_learning_stats(
            db=db,
            course_id=course_id,
            user_id=user_id if user_role == "student" else None
        )
        
        # 构建响应数据
        response_data = {
            "banner": banner_data,
            "tasks": tasks_data,
            "skills": skills_data,
            "learning_stats": learning_stats
        }
        
        # 实训课程特有功能
        if course.course_type == models.CourseTypeEnum.TRAINING:
            # 获取目录章节
            chapters = [
                {
                    "id": chapter.id,
                    "title": chapter.title,
                    "order_index": chapter.order_index,
                    "experiment_count": chapter.experiment_count,
                    "created_at": chapter.created_at
                }
                for chapter in course.chapters
            ]
            response_data["chapters"] = chapters
            
            # 学生端：获取作业列表
            if user_role == "student":
                assignments = crud.get_course_assignments(
                    db=db,
                    course_id=course_id,
                    classroom_id=classroom_id,
                    user_id=user_id
                )
                response_data["assignments"] = assignments
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=response_data
        )
        
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}/tasks", response_model=schemas.ApiResponse)
def get_course_task_list(
    course_id: int,
    user_id: Optional[int] = Query(None, description="用户ID"),
    user_role: str = Query("student", description="用户角色：teacher, student"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取课程任务列表
    
    支持分页查询课程下的所有任务，包含完成状态信息
    """
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
                evaluation_result = db.query(models.TaskEvaluationResult).filter(
                    models.TaskEvaluationResult.task_id == task.id,
                    models.TaskEvaluationResult.user_id == user_id,
                    models.TaskEvaluationResult.status == "pass"
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
        
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}/skills", response_model=schemas.ApiResponse)
def get_course_skill_tags(
    course_id: int,
    user_id: Optional[int] = Query(None, description="用户ID"),
    user_role: str = Query("student", description="用户角色：teacher, student"),
    db: Session = Depends(get_db)
):
    """
    获取课程技能标签
    
    返回课程的所有技能标签及其点亮状态
    """
    try:
        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        if not course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取技能标签
        skills_data = crud.get_course_skills_with_progress(
            db=db,
            course_id=course_id,
            user_id=user_id,
            user_role=user_role
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=skills_data
        )
        
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/courses/{course_id}/progress", response_model=schemas.ApiResponse)
def get_course_learning_progress(
    course_id: int,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取课程学习进度
    
    返回用户在该课程中的学习统计信息
    """
    try:
        # 验证课程是否存在
        course = crud.get_course(db, course_id=course_id)
        if not course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 获取学习统计
        learning_stats = crud.get_course_learning_stats(
            db=db,
            course_id=course_id,
            user_id=user_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=learning_stats
        )
        
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/courses/{course_id}/start-task/{task_id}", response_model=schemas.ApiResponse)
def start_course_task(
    course_id: int,
    task_id: int,
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    开始课程任务
    
    学生点击关卡挑战时调用，开始计时
    """
    try:
        # 验证课程和任务是否存在
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.practice_id == course_id
        ).first()
        
        if not task:
            return schemas.ApiResponse(
                code="1002",
                message="任务不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 创建或更新环境会话
        session = db.query(models.PracticeEnvironmentSession).filter(
            models.PracticeEnvironmentSession.task_id == task_id,
            models.PracticeEnvironmentSession.user_id == user_id,
            models.PracticeEnvironmentSession.status == "active"
        ).first()
        
        if not session:
            # 创建新的环境会话
            session_id = f"session_{user_id}_{task_id}_{int(datetime.now().timestamp())}"
            session = models.PracticeEnvironmentSession(
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
        
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 学生管理相关API ====================

@app.get("/api/v1/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
async def get_classroom_students(
    classroom_id: int,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """获取课堂学生列表"""
    try:
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        skip = (page - 1) * page_size
        classroom_students, total = crud.get_classroom_students(
            db, classroom_id, keyword, skip, page_size
        )
        
        # 构建响应数据
        student_list = []
        for cs in classroom_students:
            student_data = {
                "id": cs.student.id,
                "username": cs.student.username,
                "full_name": cs.student.full_name,
                "email": cs.student.email,
                "student_number": cs.student.username,  # 暂时用username作为学号
                "department": None,  # 暂时为空，实际应该从用户扩展信息获取
                "major": None,
                "grade": None,
                "avatar_url": None,
                "joined_at": cs.joined_at
            }
            student_list.append(student_data)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": student_list,
                "meta": meta
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课堂学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课堂学生列表失败: {str(e)}")

@app.get("/api/v1/classrooms/{classroom_id}/students/available", response_model=schemas.ApiResponse)
async def get_available_students(
    classroom_id: int,
    keyword: Optional[str] = None,
    department: Optional[str] = None,
    major: Optional[str] = None,
    grade: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """获取可添加的学生列表（排除已在课堂的学生）"""
    try:
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        skip = (page - 1) * page_size
        students, total = crud.get_students_by_search(
            db, keyword, department, major, grade, classroom_id, skip, page_size
        )
        
        # 构建响应数据
        student_list = []
        for student in students:
            student_data = {
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "student_number": student.username,  # 暂时用username作为学号
                "department": department,  # 使用查询参数
                "major": major,
                "grade": grade,
                "avatar_url": None,
                "joined_at": None
            }
            student_list.append(student_data)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": student_list,
                "meta": meta
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取可添加学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可添加学生列表失败: {str(e)}")

@app.get("/api/v1/organization-tree", response_model=schemas.ApiResponse)
async def get_organization_tree(db: Session = Depends(get_db)):
    """获取组织架构树"""
    try:
        organization_tree = crud.get_organization_tree(db)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={"organization_tree": organization_tree}
        )
        
    except Exception as e:
        logger.error(f"获取组织架构树失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取组织架构树失败: {str(e)}")

@app.post("/api/v1/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
async def add_students_to_classroom(
    classroom_id: int,
    request: schemas.AddStudentsRequest,
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """批量添加学生到课堂"""
    try:
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        if not request.student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")
        
        result = crud.add_students_to_classroom(db, classroom_id, request.student_ids)
        
        message = f"成功添加 {result['added_count']} 名学生"
        if result['already_exists_count'] > 0:
            message += f"，{result['already_exists_count']} 名学生已在课堂中"
        if result['not_found_count'] > 0:
            message += f"，{result['not_found_count']} 名学生不存在"
        
        return schemas.ApiResponse(
            code="0000",
            message=message,
            data=result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加学生到课堂失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加学生到课堂失败: {str(e)}")

@app.delete("/api/v1/classrooms/{classroom_id}/students", response_model=schemas.ApiResponse)
async def remove_students_from_classroom(
    classroom_id: int,
    request: schemas.RemoveStudentsRequest,
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """批量从课堂移除学生"""
    try:
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        if not request.student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")
        
        result = crud.remove_students_from_classroom(db, classroom_id, request.student_ids)
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功移除 {result['removed_count']} 名学生",
            data=result
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"从课堂移除学生失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"从课堂移除学生失败: {str(e)}")

@app.get("/api/v1/classrooms/{classroom_id}/students/management", response_model=schemas.ApiResponse)
async def get_student_management_page(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID，用于权限验证"),
    db: Session = Depends(get_db)
):
    """获取学生管理页面数据（组织架构树 + 可选学生列表）"""
    try:
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课堂")
        
        # 获取组织架构树
        organization_tree = crud.get_organization_tree(db)
        
        # 获取可选学生列表（默认前20个）
        students, total = crud.get_students_by_search(
            db, exclude_classroom_id=classroom_id, skip=0, limit=20
        )
        
        # 构建学生列表
        student_list = []
        for student in students:
            student_data = {
                "id": student.id,
                "username": student.username,
                "full_name": student.full_name,
                "email": student.email,
                "student_number": student.username,
                "department": None,
                "major": None,
                "grade": None,
                "avatar_url": None,
                "joined_at": None
            }
            student_list.append(student_data)
        
        available_students = {
            "list": student_list,
            "meta": {
                "total": total,
                "page": 1,
                "page_size": 20
            }
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "organization_tree": organization_tree,
                "available_students": available_students,
                "selected_students": []
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生管理页面数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生管理页面数据失败: {str(e)}")

# ==================== 课程添加和发布API ====================

# 4.5.1 按课表添加课程
@app.get("/api/v1/classrooms/{classroom_id}/courses/available", response_model=schemas.ApiResponse)
def get_available_courses_for_classroom(
    classroom_id: int,
    course_type: Optional[str] = Query(None, description="课程类型：practice, training, course_material"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    direction: Optional[str] = Query(None, description="方向标签"),
    category: Optional[str] = Query(None, description="分类标签"),
    difficulty: Optional[str] = Query(None, description="难度级别"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取可添加到课堂的课程列表"""
    try:
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="无权限访问该课堂",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        courses, total = crud.get_courses_for_selection(
            db=db,
            classroom_id=classroom_id,
            course_type=course_type,
            keyword=keyword,
            direction=direction,
            category=category,
            difficulty=difficulty,
            skip=skip,
            limit=page_size
        )
        
        # 获取筛选标签
        filter_tags = crud.get_course_filter_tags_for_selection(db, course_type)
        
        # 转换为响应格式
        course_list = []
        for course in courses:
            course_data = schemas.CourseSelectionResponse.model_validate(course)
            course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": course_list,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "filter_tags": filter_tags
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/courses/add-by-timetable", response_model=schemas.ApiResponse)
def add_courses_by_timetable(
    classroom_id: int,
    request: schemas.AddCoursesByTimetableRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """按课表添加课程"""
    try:
        result = crud.add_courses_by_timetable(
            db=db,
            classroom_id=classroom_id,
            source_course_id=request.source_course_id,
            teacher_id=teacher_id,
            selected_modules=request.selected_modules
        )
        
        if result is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限，或源课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 转换课程数据
        course_list = []
        for course in result["added_courses"]:
            course_data = schemas.ClassroomCourseResponse.model_validate(course)
            course_list.append(course_data.model_dump())
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功按课表添加 {result['total_added']} 个课程模块",
            data={
                "added_courses": course_list,
                "source_course": {
                    "id": result["source_course"].id,
                    "title": result["source_course"].title,
                    "course_type": result["source_course"].course_type.value
                },
                "selected_modules": result["selected_modules"],
                "total_added": result["total_added"],
                "message": f"已从课表 '{result['source_course'].title}' 添加 {result['total_added']} 个模块"
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.2 添加实践课程
@app.post("/api/v1/classrooms/{classroom_id}/courses/add-practice", response_model=schemas.ApiResponse)
def add_practice_courses_to_classroom(
    classroom_id: int,
    request: schemas.AddPracticeCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """添加实践课程到课堂"""
    try:
        added_courses = crud.add_practice_courses_to_classroom(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id
        )
        
        if added_courses is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_list = [schemas.ClassroomCourseResponse.model_validate(course).model_dump() 
                      for course in added_courses]
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {len(added_courses)} 个实践课程",
            data={
                "added_courses": course_list,
                "success_count": len(added_courses)
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.5.3 添加实训课程
@app.post("/api/v1/classrooms/{classroom_id}/courses/add-training", response_model=schemas.ApiResponse)
def add_training_courses_to_classroom(
    classroom_id: int,
    request: schemas.AddTrainingCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """添加实训课程到课堂"""
    try:
        added_courses = crud.add_training_courses_to_classroom(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id
        )
        
        if added_courses is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_list = [schemas.ClassroomCourseResponse.model_validate(course).model_dump() 
                      for course in added_courses]
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功添加 {len(added_courses)} 个实训课程",
            data={
                "added_courses": course_list,
                "success_count": len(added_courses)
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.6 课程发布相关API

@app.post("/api/v1/classrooms/{classroom_id}/courses/{course_id}/publish", response_model=schemas.ApiResponse)
def publish_single_course(
    classroom_id: int,
    course_id: int,
    request: schemas.CoursePublishSettings,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """发布单个课程"""
    try:
        # 验证截止时间格式和业务规则
        classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查截止时间是否超过课堂结束时间
        if request.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        # 如果课堂剩余时间少于7天，使用课堂结束时间作为默认截止时间
        remaining_days = (classroom.end_date - datetime.now(timezone.utc).date()).days
        if remaining_days < 7 and request.deadline_at.date() > classroom.end_date:
            request.deadline_at = classroom.end_date
        
        settings = request.model_dump()
        classroom_course = crud.publish_single_course(
            db=db,
            classroom_id=classroom_id,
            course_id=course_id,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if classroom_course is None:
            return schemas.ApiResponse(
                code="1001",
                message="课程不存在、已发布或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程发布成功",
            data=course_data.model_dump()
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
            trace_id=str(uuid.uuid4())
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/courses/publish-batch", response_model=schemas.ApiResponse)
def publish_batch_courses(
    classroom_id: int,
    request: schemas.PublishBatchCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """一键发布（批量发布课程）"""
    try:
        # 验证截止时间
        classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        if request.settings.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        settings = request.settings.model_dump()
        updated_count = crud.publish_batch_courses(
            db=db,
            classroom_id=classroom_id,
            course_ids=request.course_ids,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if updated_count is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功发布 {updated_count} 个课程",
            data={
                "success_count": updated_count,
                "failed_count": len(request.course_ids) - updated_count
            }
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
            trace_id=str(uuid.uuid4())
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/courses/publish-chapter", response_model=schemas.ApiResponse)
def publish_chapter_courses(
    classroom_id: int,
    request: schemas.PublishChapterCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """按章节发布课程（一键发布同章节下的所有未发布课程）"""
    try:
        # 验证截止时间
        classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        if request.settings.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        settings = request.settings.model_dump()
        updated_count = crud.publish_chapter_courses(
            db=db,
            classroom_id=classroom_id,
            chapter_title=request.chapter_title,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if updated_count is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功发布章节 '{request.chapter_title}' 下的 {updated_count} 个课程",
            data={
                "success_count": updated_count,
                "chapter_title": request.chapter_title,
                "message": f"章节 '{request.chapter_title}' 下的课程已成功发布" if updated_count > 0 else f"章节 '{request.chapter_title}' 下没有需要发布的课程"
            }
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
            trace_id=str(uuid.uuid4())
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/courses/publish-all", response_model=schemas.ApiResponse)
def publish_all_courses(
    classroom_id: int,
    request: schemas.PublishAllCoursesRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """全部发布（发布课堂中所有未发布的课程）"""
    try:
        # 验证截止时间
        classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
        if not classroom:
            return schemas.ApiResponse(
                code="1002",
                message="课堂不存在",
                trace_id=str(uuid.uuid4())
            )
        
        if request.settings.deadline_at.date() > classroom.end_date:
            return schemas.ApiResponse(
                code="1003",
                message="课程截止时间不能超过课堂结束时间",
                trace_id=str(uuid.uuid4())
            )
        
        settings = request.settings.model_dump()
        updated_count = crud.publish_all_courses(
            db=db,
            classroom_id=classroom_id,
            teacher_id=teacher_id,
            settings=settings
        )
        
        if updated_count is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功发布 {updated_count} 个课程",
            data={
                "success_count": updated_count,
                "message": "所有未发布的课程已成功发布" if updated_count > 0 else "没有需要发布的课程"
            }
        )
    except ValueError as ve:
        return schemas.ApiResponse(
            code="1003",
            message=str(ve),
            trace_id=str(uuid.uuid4())
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 增强版课堂课程列表（带统计信息）
@app.get("/api/v1/classrooms/{classroom_id}/courses/enhanced", response_model=schemas.ApiResponse)
def get_classroom_courses_enhanced(
    classroom_id: int,
    status: Optional[str] = Query(None, description="状态筛选：all, unpublished, learning, makeup, completed"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID（用于权限验证）"),
    db: Session = Depends(get_db)
):
    """获取带统计信息的课堂课程列表"""
    try:
        # 检查权限（如果提供了teacher_id）
        if teacher_id and not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="无权限访问该课堂",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        courses, total = crud.get_classroom_courses_with_stats(
            db=db,
            classroom_id=classroom_id,
            status=status,
            keyword=keyword,
            skip=skip,
            limit=page_size
        )
        
        # 获取状态统计
        summary = crud.get_classroom_course_status_summary(db, classroom_id)
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "list": courses,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "summary": summary
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/classrooms/{classroom_id}/chapters", response_model=schemas.ApiResponse)
def get_classroom_chapters(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂章节列表（用于一键发布）"""
    try:
        chapters = crud.get_classroom_chapters(db, classroom_id, teacher_id)
        
        if chapters is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "chapters": chapters,
                "total_chapters": len(chapters),
                "publishable_chapters": len([c for c in chapters if c["can_publish"]])
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课堂管理API ====================

@app.get("/api/v1/classrooms/{classroom_id}/management", response_model=schemas.ApiResponse)
def get_classroom_management(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂管理页面数据（包含目录结构、统计信息等）"""
    try:
        management_data = crud.get_classroom_management_data(db, classroom_id, teacher_id)
        
        if management_data is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=management_data
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/classrooms/{classroom_id}/catalog", response_model=schemas.ApiResponse)
def get_classroom_catalog(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂目录结构（章节和课程的层级关系）"""
    try:
        catalog = crud.get_classroom_catalog(db, classroom_id, teacher_id)
        
        if catalog is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"catalog": catalog}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.1.1 添加章节
@app.post("/api/v1/classrooms/{classroom_id}/chapters", response_model=schemas.ApiResponse)
def create_classroom_chapter(
    classroom_id: int,
    title: str = Query(..., description="章节标题"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """添加课堂章节"""
    try:
        chapter = crud.create_classroom_chapter(db, classroom_id, title, teacher_id)
        
        if chapter is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        chapter_data = schemas.ClassroomChapterResponse.model_validate(chapter)
        
        return schemas.ApiResponse(
            code="0000",
            message="章节添加成功",
            data=chapter_data.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.1.2 重命名章节
@app.patch("/api/v1/chapters/{chapter_id}", response_model=schemas.ApiResponse)
def update_classroom_chapter(
    chapter_id: int,
    title: str = Query(..., description="新章节标题"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """重命名课堂章节"""
    try:
        chapter = crud.update_classroom_chapter(db, chapter_id, title, teacher_id)
        
        if chapter is None:
            return schemas.ApiResponse(
                code="1002",
                message="章节不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        chapter_data = schemas.ClassroomChapterResponse.model_validate(chapter)
        
        return schemas.ApiResponse(
            code="0000",
            message="章节重命名成功",
            data=chapter_data.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.1.3 删除章节
@app.delete("/api/v1/chapters/{chapter_id}", response_model=schemas.ApiResponse)
def delete_classroom_chapter(
    chapter_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除课堂章节（同时删除章节下的课程）"""
    try:
        success = crud.delete_classroom_chapter(db, chapter_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="章节不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="章节删除成功",
            data={"message": "章节及其下的课程已删除"}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.4 调整排序
@app.patch("/api/v1/classrooms/{classroom_id}/order", response_model=schemas.ApiResponse)
def update_course_order(
    classroom_id: int,
    request: schemas.CourseOrderRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """调整课程和章节的排序"""
    try:
        success = crud.update_course_order(db, classroom_id, request.items, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="排序调整成功",
            data={"message": "课程和章节排序已更新"}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.5 课程重命名
@app.patch("/api/v1/classroom-courses/{classroom_course_id}/title", response_model=schemas.ApiResponse)
def rename_classroom_course(
    classroom_course_id: int,
    title: str = Query(..., description="新课程标题"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """重命名课堂中的课程"""
    try:
        classroom_course = crud.rename_classroom_course(db, classroom_course_id, title, teacher_id)
        
        if classroom_course is None:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(classroom_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程重命名成功",
            data=course_data.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.6 课程设置
@app.patch("/api/v1/classroom-courses/{classroom_course_id}/settings", response_model=schemas.ApiResponse)
def update_course_settings(
    classroom_course_id: int,
    settings: schemas.CourseSettingsUpdate,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """更新课程设置"""
    try:
        # 验证截止时间不能早于当前时间（如果课程已发布）
        classroom_course = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if classroom_course and classroom_course.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED:
            if settings.deadline_at and settings.deadline_at < datetime.now(timezone.utc):
                return schemas.ApiResponse(
                    code="1003",
                    message="已发布课程的截止时间不能早于当前时间",
                    trace_id=str(uuid.uuid4())
                )
        
        updated_course = crud.update_course_settings(
            db, 
            classroom_course_id, 
            settings.model_dump(exclude_unset=True), 
            teacher_id
        )
        
        if updated_course is None:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        course_data = schemas.ClassroomCourseResponse.model_validate(updated_course)
        
        return schemas.ApiResponse(
            code="0000",
            message="课程设置更新成功",
            data=course_data.model_dump()
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 4.7.1.7 课程删除
@app.delete("/api/v1/classroom-courses/{classroom_course_id}", response_model=schemas.ApiResponse)
def delete_classroom_course(
    classroom_course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除课堂中的课程"""
    try:
        success = crud.delete_classroom_course(db, classroom_course_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在、无权限或课程已完成无法删除",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="课程删除成功",
            data={"message": "课程已从课堂中删除"}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# 获取课程设置详情
@app.get("/api/v1/classroom-courses/{classroom_course_id}/settings", response_model=schemas.ApiResponse)
def get_course_settings(
    classroom_course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课程设置详情"""
    try:
        classroom_course = db.query(models.ClassroomCourse).options(
            joinedload(models.ClassroomCourse.course)
        ).filter(
            models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if not classroom_course:
            return schemas.ApiResponse(
                code="1002",
                message="课程不存在",
                trace_id=str(uuid.uuid4())
            )
        
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="无权限访问",
                trace_id=str(uuid.uuid4())
            )
        
        # 构建设置数据
        settings_data = {
            "id": classroom_course.id,
            "classroom_course_id": classroom_course.id,
            "deadline_at": classroom_course.deadline_at,
            "is_mandatory": classroom_course.is_mandatory,
            "allow_late_submission": classroom_course.allow_late_submission,
            "late_submission_deduction_points": classroom_course.late_submission_deduction_points,
            "total_score": classroom_course.total_score,
            "publicize_grades": classroom_course.publicize_grades,
            "publicize_answers_after_completion": classroom_course.publicize_answers_after_completion,
            "course_type": classroom_course.course.course_type.value,
            "published_at": classroom_course.published_at,
            "status": classroom_course.teacher_publish_status.value
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=settings_data
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 成绩查看和作业点评相关API ====================

@app.get("/api/v1/classrooms/{classroom_id}/courses/{classroom_course_id}/grades", response_model=schemas.ApiResponse)
def get_course_grades(
    classroom_id: int,
    classroom_course_id: int,
    status: Optional[str] = Query(None, description="作业状态筛选：not_started, not_completed, completed_on_time, completed_late（实践课程）或 not_started, not_submitted, submitted, late_submitted（实训课程）"),
    keyword: Optional[str] = Query(None, description="学生姓名或学号搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课程成绩列表"""
    try:
        # 先检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课程")
        
        skip = (page - 1) * page_size
        grade_list, total = crud.get_course_grades(
            db, classroom_id, classroom_course_id, teacher_id, status, keyword, skip, page_size
        )
        
        if grade_list is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 构建统计信息
        stats = {
            "total_students": total,
            "not_started": 0,
            "in_progress": 0,
            "completed": 0,
            "late_completed": 0
        }
        
        # 统计各状态学生数量
        for grade in grade_list:
            status_key = grade["assignment_status"]
            if status_key == "not_started":
                stats["not_started"] += 1
            elif status_key in ["not_completed", "not_submitted"]:
                stats["in_progress"] += 1
            elif status_key in ["completed_on_time", "submitted"]:
                stats["completed"] += 1
            elif status_key in ["completed_late", "late_submitted"]:
                stats["late_completed"] += 1
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": grade_list,
                "meta": meta,
                "stats": stats
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程成绩列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课程成绩列表失败: {str(e)}")

@app.get("/api/v1/classroom-courses/{classroom_course_id}/statistics", response_model=schemas.ApiResponse)
def get_course_grade_statistics(
    classroom_course_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课程成绩统计信息"""
    try:
        statistics = crud.get_course_grade_statistics(db, classroom_course_id, teacher_id)
        
        if statistics is None:
            raise HTTPException(status_code=404, detail="课程不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程成绩统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取课程成绩统计失败: {str(e)}")

@app.patch("/api/v1/student-progress/{progress_id}/penalty", response_model=schemas.ApiResponse)
def update_student_penalty(
    progress_id: int,
    request: schemas.PenaltyUpdateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """更新学生奖惩扣分"""
    try:
        updated_progress = crud.update_student_penalty(
            db, progress_id, teacher_id, request.penalty_score, request.reason
        )
        
        if updated_progress is None:
            raise HTTPException(status_code=404, detail="学生进度记录不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="奖惩调整成功",
            data={
                "id": updated_progress.id,
                "penalty_score": updated_progress.teacher_penalties,
                "final_score": updated_progress.final_calculated_score
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学生奖惩扣分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新学生奖惩扣分失败: {str(e)}")

@app.patch("/api/v1/classroom-courses/{classroom_course_id}/batch-penalty", response_model=schemas.ApiResponse)
def batch_update_student_penalty(
    classroom_course_id: int,
    request: schemas.BatchPenaltyUpdateRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """批量更新学生奖惩扣分"""
    try:
        if not request.student_ids:
            raise HTTPException(status_code=400, detail="学生ID列表不能为空")
        
        updated_records = crud.batch_update_student_penalty(
            db, classroom_course_id, teacher_id, request.student_ids, request.penalty_score, request.reason
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"成功更新 {len(updated_records)} 名学生的奖惩扣分",
            data={
                "updated_count": len(updated_records),
                "penalty_score": request.penalty_score
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新学生奖惩扣分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量更新学生奖惩扣分失败: {str(e)}")

@app.get("/api/v1/classroom-courses/{classroom_course_id}/assignments", response_model=schemas.ApiResponse)
def get_training_assignments(
    classroom_course_id: int,
    keyword: Optional[str] = Query(None, description="学生姓名或学号搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取实训作业列表"""
    try:
        skip = (page - 1) * page_size
        assignment_list, total = crud.get_training_assignments(
            db, classroom_course_id, teacher_id, keyword, skip, page_size
        )
        
        if assignment_list is None:
            raise HTTPException(status_code=404, detail="课程不存在、不是实训课程或无权限访问")
        
        # 构建统计信息
        stats = {
            "total_students": total,
            "not_started": 0,
            "not_submitted": 0,
            "submitted": 0,
            "late_submitted": 0,
            "graded": 0,
            "not_graded": 0
        }
        
        # 统计各状态学生数量
        for assignment in assignment_list:
            submission_status = assignment["submission_status"]
            grading_status = assignment["grading_status"]
            
            if submission_status == models.SubmissionStatusEnum.NOT_STARTED:
                stats["not_started"] += 1
            elif submission_status == models.SubmissionStatusEnum.IN_PROGRESS:
                stats["not_submitted"] += 1
            elif submission_status == models.SubmissionStatusEnum.SUBMITTED:
                stats["submitted"] += 1
            elif submission_status == models.SubmissionStatusEnum.LATE_SUBMISSION:
                stats["late_submitted"] += 1
            
            if grading_status == models.GradingStatusEnum.GRADED:
                stats["graded"] += 1
            else:
                stats["not_graded"] += 1
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": assignment_list,
                "meta": meta,
                "stats": stats
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实训作业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实训作业列表失败: {str(e)}")

@app.post("/api/v1/classroom-courses/{classroom_course_id}/students/{student_id}/grade", response_model=schemas.ApiResponse)
def grade_training_assignment(
    classroom_course_id: int,
    student_id: int,
    request: schemas.TrainingGradingRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """实训作业点评"""
    try:
        if request.score < 0 or request.score > 100:
            raise HTTPException(status_code=400, detail="评分必须在0-100之间")
        
        graded_progress = crud.grade_training_assignment(
            db, classroom_course_id, student_id, teacher_id, 
            request.score, request.feedback, request.is_excellent
        )
        
        if graded_progress is None:
            raise HTTPException(status_code=404, detail="学生作业不存在、未提交或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="作业点评成功",
            data={
                "student_id": student_id,
                "score": graded_progress.overall_score,
                "final_score": graded_progress.final_calculated_score,
                "feedback": graded_progress.teacher_feedback,
                "is_excellent": graded_progress.is_excellent_work,
                "graded_at": graded_progress.graded_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实训作业点评失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"实训作业点评失败: {str(e)}")

@app.patch("/api/v1/student-progress/{progress_id}/excellent", response_model=schemas.ApiResponse)
def set_excellent_work(
    progress_id: int,
    request: schemas.ExcellentWorkRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """设置优秀作业"""
    try:
        updated_progress = crud.set_excellent_work(
            db, progress_id, teacher_id, request.is_excellent
        )
        
        if updated_progress is None:
            raise HTTPException(status_code=404, detail="学生进度记录不存在、未点评或无权限访问")
        
        action = "设置为优秀作业" if request.is_excellent else "取消优秀作业"
        
        return schemas.ApiResponse(
            code="0000",
            message=f"{action}成功",
            data={
                "id": updated_progress.id,
                "is_excellent": updated_progress.is_excellent_work
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置优秀作业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"设置优秀作业失败: {str(e)}")

@app.post("/api/v1/classroom-courses/{classroom_course_id}/submit-assignment", response_model=schemas.ApiResponse)
def submit_training_assignment(
    classroom_course_id: int,
    request: schemas.AssignmentSubmissionRequest,
    student_id: int = Query(..., description="学生ID"),
    db: Session = Depends(get_db)
):
    """学生提交实训作业"""
    try:
        if not request.design_files and not request.experiment_reports:
            raise HTTPException(status_code=400, detail="至少需要提交一个文件")
        
        # 转换文件格式
        design_files = [file.dict() for file in request.design_files]
        experiment_reports = [file.dict() for file in request.experiment_reports]
        
        submitted_progress = crud.submit_training_assignment(
            db, classroom_course_id, student_id, design_files, experiment_reports
        )
        
        if submitted_progress is None:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        return schemas.ApiResponse(
            code="0000",
            message="作业提交成功",
            data={
                "student_id": student_id,
                "submission_status": submitted_progress.training_submission_status.value,
                "submission_time": submitted_progress.last_submission_at,
                "design_files_count": len(design_files),
                "experiment_reports_count": len(experiment_reports)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生提交实训作业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"学生提交实训作业失败: {str(e)}")

@app.get("/api/v1/classroom-courses/{classroom_course_id}/export-grades", response_model=schemas.ApiResponse)
def export_course_grades(
    classroom_course_id: int,
    format: str = Query("excel", description="导出格式：excel, csv"),
    include_details: bool = Query(True, description="是否包含详细信息"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """导出课程成绩"""
    try:
        # 获取课堂课程信息以获取classroom_id
        classroom_course = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.id == classroom_course_id
        ).first()
        
        if not classroom_course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 检查教师权限
        if not crud.check_classroom_teacher_permission(db, classroom_course.classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此课程")
        
        # 获取所有成绩数据
        grade_list, total = crud.get_course_grades(
            db, classroom_course.classroom_id, classroom_course_id, teacher_id, None, None, 0, 1000
        )
        
        if grade_list is None:
            raise HTTPException(status_code=404, detail="课程不存在或无权限访问")
        
        # 这里应该实现实际的导出逻辑，生成Excel或CSV文件
        # 为了演示，我们返回数据结构
        export_data = {
            "format": format,
            "total_records": len(grade_list),
            "export_time": datetime.now(timezone.utc),
            "include_details": include_details,
            "download_url": f"/api/v1/downloads/grades-{classroom_course_id}-{int(datetime.now().timestamp())}.{format}"
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="成绩导出准备完成",
            data=export_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出课程成绩失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出课程成绩失败: {str(e)}")

# 学生端API：查看自己的作业详情
@app.get("/api/v1/classroom-courses/{classroom_course_id}/my-assignment", response_model=schemas.ApiResponse)
def get_my_assignment_detail(
    classroom_course_id: int,
    student_id: int = Query(..., description="学生ID"),
    db: Session = Depends(get_db)
):
    """学生查看自己的作业详情"""
    try:
        # 获取学生进度记录
        progress = db.query(models.StudentCourseProgress).options(
            joinedload(models.StudentCourseProgress.classroom_course),
            joinedload(models.StudentCourseProgress.graded_by_teacher)
        ).filter(
            models.StudentCourseProgress.classroom_course_id == classroom_course_id,
            models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not progress:
            # 如果没有进度记录，返回初始状态
            classroom_course = db.query(models.ClassroomCourse).options(
                joinedload(models.ClassroomCourse.course)
            ).filter(
                models.ClassroomCourse.id == classroom_course_id
            ).first()
            
            if not classroom_course:
                raise HTTPException(status_code=404, detail="课程不存在")
            
            return schemas.ApiResponse(
                code="0000",
                message="获取成功",
                data={
                    "submission_status": "NOT_STARTED",
                    "submission_time": None,
                    "design_files": [],
                    "experiment_reports": [],
                    "grading_status": "NOT_GRADED",
                    "score": None,
                    "teacher_feedback": None,
                    "is_excellent": False,
                    "graded_at": None,
                    "can_submit": True
                }
            )
        
        # 解析作业文件
        design_files = []
        experiment_reports = []
        
        if progress.training_assignment_files:
            try:
                import json
                files_data = json.loads(progress.training_assignment_files)
                design_files = files_data.get("design_files", [])
                experiment_reports = files_data.get("experiment_reports", [])
            except:
                pass
        
        # 判断是否可以继续提交（点评前可以重复提交）
        can_submit = not progress.graded_at
        
        assignment_detail = {
            "submission_status": progress.training_submission_status.value,
            "submission_time": progress.last_submission_at,
            "design_files": design_files,
            "experiment_reports": experiment_reports,
            "grading_status": "GRADED" if progress.graded_at else "NOT_GRADED",
            "score": progress.final_calculated_score if progress.graded_at else None,
            "teacher_feedback": progress.teacher_feedback,
            "is_excellent": progress.is_excellent_work,
            "graded_at": progress.graded_at,
            "graded_by_teacher_name": progress.graded_by_teacher.full_name if progress.graded_by_teacher else None,
            "can_submit": can_submit
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data=assignment_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生作业详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取学生作业详情失败: {str(e)}")

# ==================== 考试阅卷相关API ====================

@app.get("/api/v1/exams/{exam_id}/papers", response_model=schemas.UnmarkedStudentsResponse)
def get_exam_unmarked_papers(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    unmarked: bool = Query(False, description="是否只显示未阅卷的"),
    db: Session = Depends(get_db)
):
    """
    获取考试的待阅卷学生列表
    
    从课程考核中进入阅卷：在课程考核页面中，对于考试中或者已完成的考试，
    点击"阅卷"按钮，可跳转至未阅卷学生试卷详情页中，进行阅卷
    """
    try:
        result = crud.get_exam_unmarked_students(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        # 如果只显示未阅卷的，过滤已阅卷的学生
        if unmarked:
            result["students"] = [s for s in result["students"] if s["status"] == "submitted"]
            result["total_students"] = len(result["students"])
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取待阅卷学生列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/api/v1/exams/{exam_id}/papers/{student_id}", response_model=schemas.ExamPaperDetail)
def get_student_exam_paper(
    exam_id: int,
    student_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    获取学生试卷详情（用于阅卷）
    
    从考试详情中进入阅卷：
    1. 在考试详情页面中，点击右上角"阅卷"按钮，可跳转至未阅卷学生试卷详情页中，进行阅卷
    2. 在考试详情页面中，点击列表中对应学生后方的"阅卷"按钮，可跳转至该学生试卷详情页中，进行阅卷
    """
    try:
        result = crud.get_student_exam_paper(db, exam_id, student_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取学生试卷详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.post("/api/v1/exams/{exam_id}/papers/{student_id}/marks", response_model=schemas.SubmitMarksResponse)
def submit_exam_marks(
    exam_id: int,
    student_id: int,
    request: schemas.SubmitMarksRequest,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    提交试卷评分
    
    试卷评阅：
    1. 试卷评阅时区分主观题和客观题，简答题属于主观题，除简答外的单选、多选、判断题属于客观题；
       主观题需要教师进行评分，客观题自动判题得分，点击左侧题目标号可跳转至对应题目处
    2. 对于主观题，教师可根据题目总分及学生答题情况赋予对应的分值，可选填教师评语；
       左侧悬浮窗及试题底色都通过颜色区分试题状态，可快速找到未评分题目进行评分
    3. 所有主观题目完成评分后，点击右侧悬浮栏中"提交评分"按钮即可提交评分，完成试卷评阅
    """
    try:
        marks_data = {
            "marks": [mark.model_dump() for mark in request.marks],
            "overall_comments": request.overall_comments
        }
        
        result = crud.submit_exam_marks(db, exam_id, student_id, teacher_id, marks_data)
        
        if result is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "code": "0000",
            "message": "评分提交成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"提交试卷评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/api/v1/exams/{exam_id}/papers/{student_id}/view")
def view_student_exam_paper(
    exam_id: int,
    student_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    查看学生试卷（只读模式）
    
    查看学生试卷：在考试详情页中，点击学生列表中对应学生后的"查看试卷"按钮，
    即可查看该学生的试卷答题情况
    """
    try:
        result = crud.get_student_exam_paper(db, exam_id, student_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="试卷不存在或无权限访问")
        
        # 添加只读标识
        result["readonly"] = True
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"查看学生试卷失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/api/v1/exams/{exam_id}/statistics", response_model=schemas.ExamStatistics)
def get_exam_statistics(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    获取考试统计信息
    """
    try:
        result = crud.get_exam_statistics(db, exam_id, teacher_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="考试不存在或无权限访问")
        
        return {
            "code": "0000",
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取考试统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.post("/api/v1/exams/{exam_id}/auto-grade")
def auto_grade_exam_objective_questions(
    exam_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """
    自动评分客观题
    
    对考试中的单选题、多选题进行自动评分
    """
    try:
        # 检查教师权限
        exam = db.query(models.ClassroomExam).filter(
            models.ClassroomExam.id == exam_id
        ).first()
        
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        
        if not crud.check_classroom_teacher_permission(db, exam.classroom_id, teacher_id):
            raise HTTPException(status_code=403, detail="无权限访问此考试")
        
        success = crud.auto_grade_objective_questions(db, exam_id)
        
        if success:
            return {
                "code": "0000",
                "message": "客观题自动评分完成",
                "data": {"success": True}
            }
        else:
            raise HTTPException(status_code=500, detail="自动评分失败")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"自动评分客观题失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

# ==================== 教学资源管理API ====================

@app.get("/api/v1/classrooms/{classroom_id}/resources", response_model=schemas.ApiResponse)
def get_classroom_resources(
    classroom_id: int,
    resource_type: Optional[str] = Query(None, description="资源类型筛选：video, ppt, pdf, document"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂教学资源列表"""
    try:
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        resources, total = crud.get_classroom_resources(
            db, classroom_id, resource_type, keyword, skip, page_size
        )
        
        # 构建响应数据
        resource_list = []
        for resource in resources:
            resource_data = {
                "id": resource.id,
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "file_size": getattr(resource, 'file_size', None),
                "upload_time": resource.created_at,
                "uploader_name": getattr(resource, 'uploader_name', '教师'),
                "view_count": getattr(resource, 'view_count', 0),
                "download_count": getattr(resource, 'download_count', 0)
            }
            resource_list.append(resource_data)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": resource_list,
                "meta": meta
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/resources", response_model=schemas.ApiResponse)
def upload_classroom_resource(
    classroom_id: int,
    title: str = Query(..., description="资源标题"),
    resource_type: str = Query(..., description="资源类型：video, ppt, pdf, document"),
    url: str = Query(..., description="资源URL"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """上传教学资源"""
    try:
        resource = crud.create_classroom_resource(
            db, classroom_id, title, url, resource_type, teacher_id
        )
        
        if resource is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        resource_data = {
            "id": resource.id,
            "title": resource.title,
            "url": resource.url,
            "resource_type": resource.resource_type,
            "upload_time": resource.created_at
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="资源上传成功",
            data=resource_data
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.delete("/api/v1/classrooms/{classroom_id}/resources/{resource_id}", response_model=schemas.ApiResponse)
def delete_classroom_resource(
    classroom_id: int,
    resource_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """删除教学资源"""
    try:
        success = crud.delete_classroom_resource(db, classroom_id, resource_id, teacher_id)
        
        if not success:
            return schemas.ApiResponse(
                code="1002",
                message="资源不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        return schemas.ApiResponse(
            code="0000",
            message="资源删除成功",
            data={"message": "教学资源已删除"}
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 课堂云盘API ====================

@app.get("/api/v1/classrooms/{classroom_id}/cloud-disk", response_model=schemas.ApiResponse)
def get_classroom_cloud_disk(
    classroom_id: int,
    folder_path: str = Query("", description="文件夹路径"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    file_type: Optional[str] = Query(None, description="文件类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取课堂云盘文件列表"""
    try:
        # 检查权限
        if not crud.check_classroom_teacher_permission(db, classroom_id, teacher_id):
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        skip = (page - 1) * page_size
        files, total = crud.get_classroom_cloud_files(
            db, classroom_id, folder_path, keyword, file_type, skip, page_size
        )
        
        # 构建响应数据
        file_list = []
        for file in files:
            file_data = {
                "id": file.id,
                "name": file.name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "folder_path": file.folder_path,
                "url": file.url,
                "upload_time": file.created_at,
                "uploader_name": getattr(file, 'uploader_name', '教师'),
                "download_count": getattr(file, 'download_count', 0),
                "is_shared": getattr(file, 'is_shared', True)
            }
            file_list.append(file_data)
        
        meta = {
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="获取成功",
            data={
                "list": file_list,
                "meta": meta,
                "current_path": folder_path
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.post("/api/v1/classrooms/{classroom_id}/cloud-disk/upload", response_model=schemas.ApiResponse)
def upload_to_classroom_cloud_disk(
    classroom_id: int,
    file_name: str = Query(..., description="文件名"),
    file_type: str = Query(..., description="文件类型"),
    file_size: int = Query(..., description="文件大小（字节）"),
    folder_path: str = Query("", description="上传到的文件夹路径"),
    url: str = Query(..., description="文件URL"),
    is_shared: bool = Query(True, description="是否共享给学生"),
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """上传文件到课堂云盘"""
    try:
        file = crud.upload_classroom_cloud_file(
            db, classroom_id, file_name, file_type, file_size, 
            folder_path, url, is_shared, teacher_id
        )
        
        if file is None:
            return schemas.ApiResponse(
                code="1001",
                message="课堂不存在或无权限",
                trace_id=str(uuid.uuid4())
            )
        
        file_data = {
            "id": file.id,
            "name": file.name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "folder_path": file.folder_path,
            "url": file.url,
            "upload_time": file.created_at,
            "is_shared": file.is_shared
        }
        
        return schemas.ApiResponse(
            code="0000",
            message="文件上传成功",
            data=file_data
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

# ==================== 学情分析API ====================

@app.get("/api/v1/classrooms/{classroom_id}/analytics/overview", response_model=schemas.ApiResponse)
def get_classroom_analytics_overview(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取学情分析总览"""
    try:
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/classrooms/{classroom_id}/analytics/mandatory-courses", response_model=schemas.ApiResponse)
def get_mandatory_courses_analytics(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取必修课程统计"""
    try:
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@app.get("/api/v1/classrooms/{classroom_id}/analytics/elective-courses", response_model=schemas.ApiResponse)
def get_elective_courses_analytics(
    classroom_id: int,
    teacher_id: int = Query(..., description="教师ID"),
    db: Session = Depends(get_db)
):
    """获取拓展课程统计"""
    try:
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
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"服务器内部异常: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 