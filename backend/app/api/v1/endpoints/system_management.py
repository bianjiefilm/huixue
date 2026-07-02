from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....crud.organization import school_crud, teacher_crud, student_crud
from ....schemas.organization import (
    SchoolResponse, SchoolUpdate, TeacherResponse, TeacherCreate,
    TeacherUpdate, BatchStatusUpdate, AdminAuth, ImportResult,
    PaginatedResponse, StudentResponse, StudentCreate, StudentUpdate
)
from .... import schemas
import base64
import io
try:
    from PIL import Image
except ImportError:
    Image = None
import pandas as pd
import tempfile
import os

router = APIRouter()

# 学校信息管理
@router.get("/school/{school_id}", response_model=schemas.ApiResponse)
async def get_school_info(
    school_id: int,
    db: Session = Depends(get_db)
):
    """获取学校信息"""
    try:
        school = school_crud.get_school(db, school_id)
        if not school:
            return schemas.ApiResponse(
                code="2001",
                message="学校不存在",
                data=None
            )
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=SchoolResponse.model_validate(school)
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"获取学校信息失败: {str(e)}",
            data=None
        )

@router.put("/school/{school_id}", response_model=schemas.ApiResponse)
async def update_school_info(
    school_id: int,
    school_update: SchoolUpdate,
    db: Session = Depends(get_db)
):
    """修改学校基础信息"""
    try:
        school = school_crud.update_school(db, school_id, school_update)
        if not school:
            return schemas.ApiResponse(
                code="2001",
                message="学校不存在",
                data=None
            )
        return schemas.ApiResponse(
            code="0000",
            message="学校信息更新成功",
            data=SchoolResponse.model_validate(school)
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"更新学校信息失败: {str(e)}",
            data=None
        )

@router.post("/school/{school_id}/logo")
async def upload_school_logo(
    school_id: int,
    file: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    db: Session = Depends(get_db)
):
    """上传并裁剪学校Logo"""
    # 验证文件格式
    if not file.content_type in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="只支持JPG和PNG格式")
    
    # 验证文件大小 (2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过2MB")
    
    try:
        # 图片裁剪
        image = Image.open(io.BytesIO(contents))
        cropped_image = image.crop((x, y, x + width, y + height))
        
        # 保存处理后的图片
        img_io = io.BytesIO()
        cropped_image.save(img_io, format='PNG')
        img_data = img_io.getvalue()
        
        # 生成文件名并保存
        logo_filename = f"school_{school_id}_logo.png"
        logo_path = f"/app/static/logos/{logo_filename}"
        os.makedirs(os.path.dirname(logo_path), exist_ok=True)
        
        with open(logo_path, "wb") as f:
            f.write(img_data)
        
        # 更新数据库
        logo_url = f"/static/logos/{logo_filename}"
        school = school_crud.update_school_logo(db, school_id, logo_url, img_data)
        
        if not school:
            raise HTTPException(status_code=404, detail="学校不存在")
        
        return {"message": "学校LOGO修改成功", "logo_url": logo_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logo处理失败: {str(e)}")

# 教师管理
@router.get("/teachers")
async def get_teachers(
    school_id: Optional[int] = None,
    college_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取教师列表"""
    try:
        skip = (page - 1) * page_size
        teachers = teacher_crud.get_teachers(
            db, school_id=school_id, college_id=college_id,
            search=search, skip=skip, limit=page_size
        )

        # 获取总数
        total = len(teacher_crud.get_teachers(db, school_id=school_id, college_id=college_id, search=search))

        # 转换 ORM 对象为 Pydantic 模型
        teacher_responses = [TeacherResponse.model_validate(t) for t in teachers]

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "items": teacher_responses,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"获取教师列表失败: {str(e)}",
            data=None
        )

@router.post("/teachers")
async def create_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_db)
):
    """添加教师"""
    # 检查工号是否已存在
    existing_teacher = teacher_crud.get_teacher_by_job_number(db, teacher.job_number)
    if existing_teacher:
        raise HTTPException(status_code=400, detail="工号已存在")
    
    new_teacher = teacher_crud.create_teacher(db, teacher)
    return schemas.ApiResponse(
        code="0000",
        message="添加成功",
        data=TeacherResponse.model_validate(new_teacher)
    )

@router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):
    """获取教师详情"""
    teacher = teacher_crud.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher

@router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    teacher_update: TeacherUpdate,
    db: Session = Depends(get_db)
):
    """编辑教师信息"""
    teacher = teacher_crud.update_teacher(db, teacher_id, teacher_update)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher

@router.delete("/teachers/{teacher_id}")
async def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db)
):
    """删除教师"""
    success = teacher_crud.delete_teacher(db, teacher_id)
    if not success:
        raise HTTPException(status_code=404, detail="教师不存在")
    return {"message": "教师删除成功"}

@router.post("/teachers/batch-status")
async def batch_update_teacher_status(
    batch_update: BatchStatusUpdate,
    db: Session = Depends(get_db)
):
    """批量启用/停用教师"""
    updated_count = teacher_crud.batch_update_status(db, batch_update.ids, batch_update.is_active)
    action = "启用" if batch_update.is_active else "停用"
    return {"message": f"已{action} {updated_count} 位教师"}

@router.delete("/teachers/batch")
async def batch_delete_teachers(
    teacher_ids: List[int],
    db: Session = Depends(get_db)
):
    """批量删除教师"""
    deleted_count = 0
    for teacher_id in teacher_ids:
        if teacher_crud.delete_teacher(db, teacher_id):
            deleted_count += 1
    return {"message": f"已删除 {deleted_count} 位教师"}

@router.post("/teachers/import")
async def import_teachers(
    file: UploadFile = File(...),
    school_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """批量导入教师"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件")
    
    try:
        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        success_count = 0
        error_count = 0
        errors = []
        
        required_columns = ['工号', '姓名']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"缺少必需列: {col}")
        
        for index, row in df.iterrows():
            try:
                # 检查工号是否已存在
                if teacher_crud.get_teacher_by_job_number(db, str(row['工号'])):
                    errors.append({
                        "row": index + 2,
                        "error": f"该工号{row['工号']}已存在，不可重复导入"
                    })
                    error_count += 1
                    continue
                
                teacher_data = TeacherCreate(
                    job_number=str(row['工号']),
                    name=str(row['姓名']),
                    gender=str(row.get('性别', '')),
                    phone=str(row.get('联系电话', '')),
                    email=str(row.get('邮箱', '')),
                    title=str(row.get('职称', '')),
                    department=str(row.get('部门', '')),
                    school_id=school_id
                )
                
                teacher_crud.create_teacher(db, teacher_data)
                success_count += 1
                
            except Exception as e:
                errors.append({
                    "row": index + 2,
                    "error": str(e)
                })
                error_count += 1
        
        # 生成错误报告文件
        error_file_url = None
        if errors:
            error_df = pd.DataFrame(errors)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                error_df.to_excel(tmp.name, index=False)
                error_file_url = f"/static/import_errors/{os.path.basename(tmp.name)}"
        
        return ImportResult(
            success_count=success_count,
            error_count=error_count,
            errors=errors,
            file_url=error_file_url
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.get("/teachers/export/template")
async def download_teacher_template():
    """下载教师导入模板"""
    template_data = {
        '工号': ['T001', 'T002'],
        '姓名': ['张三', '李四'],
        '性别': ['男', '女'],
        '联系电话': ['13800138001', '13800138002'],
        '邮箱': ['zhangsan@example.com', 'lisi@example.com'],
        '职称': ['教授', '副教授'],
        '部门': ['计算机学院', '信息学院']
    }
    
    df = pd.DataFrame(template_data)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        df.to_excel(tmp.name, index=False)
        return FileResponse(
            tmp.name,
            filename="教师导入模板.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 角色授权管理
@router.get("/admins", response_model=List[TeacherResponse])
async def get_admin_teachers(
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取管理员列表"""
    teachers = teacher_crud.get_teachers(db, search=search)
    # 过滤出管理员，排除系统保留账户
    admin_teachers = [
        t for t in teachers 
        if t.is_admin and t.job_number not in ['ttadmin', 'admin']
    ]
    return admin_teachers

@router.post("/admins")
async def add_admin_teachers(
    admin_auth: AdminAuth,
    db: Session = Depends(get_db)
):
    """添加管理员"""
    updated_count = teacher_crud.set_admin_status(db, admin_auth.teacher_ids, True)
    return {"message": f"已授权 {updated_count} 位教师为管理员"}

@router.delete("/admins")
async def remove_admin_teachers(
    teacher_ids: List[int],
    db: Session = Depends(get_db)
):
    """移除管理员"""
    # 过滤系统保留账户
    filtered_ids = []
    for teacher_id in teacher_ids:
        teacher = teacher_crud.get_teacher(db, teacher_id)
        if teacher and teacher.job_number not in ['ttadmin', 'admin']:
            filtered_ids.append(teacher_id)
    
    updated_count = teacher_crud.set_admin_status(db, filtered_ids, False)
    return {"message": f"已移除 {updated_count} 位管理员授权"}

# ==================== 系统配置管理 ====================

@router.get("/system-config", response_model=schemas.ApiResponse)
async def get_system_config(db: Session = Depends(get_db)):
    """获取系统配置"""
    try:
        # 从数据库或配置文件获取系统配置
        from app.core.config import settings

        config = {
            "allow_multiple_environments": getattr(settings, 'ALLOW_MULTIPLE_ENVIRONMENTS', True),
            "max_environments_per_user": getattr(settings, 'MAX_ENVIRONMENTS_PER_USER', 3),
            "environment_timeout_minutes": getattr(settings, 'ENVIRONMENT_TIMEOUT_MINUTES', 120),
        }

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=config
        )

    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"获取系统配置失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )

@router.put("/system-config", response_model=schemas.ApiResponse)
async def update_system_config(
    config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新系统配置"""
    try:
        # 这里可以保存到数据库或配置文件
        # 暂时只返回成功响应
        updated_config = {
            "allow_multiple_environments": config.get("allow_multiple_environments", True),
            "max_environments_per_user": config.get("max_environments_per_user", 3),
            "environment_timeout_minutes": config.get("environment_timeout_minutes", 120),
        }

        return schemas.ApiResponse(
            code="0000",
            message="系统配置已更新",
            data=updated_config
        )

    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"更新系统配置失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 学生管理 ====================

@router.get("/students")
async def get_students(
    school_id: Optional[int] = None,
    college_id: Optional[int] = None,
    major_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    class_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取学生列表"""
    try:
        skip = (page - 1) * page_size
        students = student_crud.get_students(
            db, school_id=school_id, college_id=college_id,
            major_id=major_id, grade_id=grade_id, class_id=class_id,
            search=search, skip=skip, limit=page_size
        )

        # 获取总数
        total = len(student_crud.get_students(
            db, school_id=school_id, college_id=college_id,
            major_id=major_id, grade_id=grade_id, class_id=class_id, search=search
        ))

        # 转换 ORM 对象为 Pydantic 模型
        student_responses = [StudentResponse.model_validate(s) for s in students]

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "items": student_responses,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        )
    except Exception as e:
        return schemas.ApiResponse(
            code="2000",
            message=f"获取学生列表失败: {str(e)}",
            data=None
        )

@router.post("/students")
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    """添加学生"""
    # 检查学号是否已存在
    existing_student = student_crud.get_student_by_number(db, student.student_number)
    if existing_student:
        raise HTTPException(status_code=400, detail="学号已存在")

    new_student = student_crud.create_student(db, student)
    return schemas.ApiResponse(
        code="0000",
        message="添加成功",
        data=StudentResponse.model_validate(new_student)
    )

# 批量操作路由放在单个操作路由前面，避免路由匹配问题
@router.post("/students/batch-status")
async def batch_update_student_status(
    batch_update: BatchStatusUpdate,
    db: Session = Depends(get_db)
):
    """批量启用/停用学生"""
    updated_count = student_crud.batch_update_status(db, batch_update.ids, batch_update.is_active)
    action = "启用" if batch_update.is_active else "停用"
    return schemas.ApiResponse(
        code="0000",
        message=f"已{action} {updated_count} 名学生",
        data={"updated_count": updated_count}
    )

@router.post("/students/batch-delete")
async def batch_delete_students(
    batch_update: BatchStatusUpdate,
    db: Session = Depends(get_db)
):
    """批量删除学生"""
    deleted_count = 0
    for student_id in batch_update.ids:
        if student_crud.delete_student(db, student_id):
            deleted_count += 1
    return schemas.ApiResponse(
        code="0000",
        message=f"已删除 {deleted_count} 名学生",
        data={"deleted_count": deleted_count}
    )

@router.get("/students/{student_id}", response_model=schemas.ApiResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    """获取学生详情"""
    student = student_crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return schemas.ApiResponse(
        code="0000",
        message="success",
        data=StudentResponse.model_validate(student)
    )

@router.put("/students/{student_id}", response_model=schemas.ApiResponse)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: Session = Depends(get_db)
):
    """编辑学生信息"""
    student = student_crud.update_student(db, student_id, student_update)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return schemas.ApiResponse(
        code="0000",
        message="更新成功",
        data=StudentResponse.model_validate(student)
    )

@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db)
):
    """删除学生"""
    success = student_crud.delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="学生不存在")
    return schemas.ApiResponse(
        code="0000",
        message="学生删除成功",
        data=None
    )

@router.post("/students/batch-transfer")
async def batch_transfer_students(
    student_ids: List[int],
    target_class_id: int,
    db: Session = Depends(get_db)
):
    """批量调动学生"""
    updated_count = student_crud.batch_transfer(db, student_ids, class_id=target_class_id)
    return schemas.ApiResponse(
        code="0000",
        message=f"已调动 {updated_count} 名学生",
        data={"updated_count": updated_count}
    )

@router.post("/students/import")
async def import_students(
    file: UploadFile = File(...),
    school_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """批量导入学生"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件")

    try:
        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        success_count = 0
        error_count = 0
        errors = []

        required_columns = ['学号', '姓名']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"缺少必需列: {col}")

        for index, row in df.iterrows():
            try:
                # 检查学号是否已存在
                if student_crud.get_student_by_number(db, str(row['学号'])):
                    errors.append({
                        "row": index + 2,
                        "error": f"该学号{row['学号']}已存在，不可重复导入"
                    })
                    error_count += 1
                    continue

                # 处理班级信息
                class_id = None
                if '班级' in df.columns and pd.notna(row.get('班级')):
                    # 可以根据班级名称查找class_id
                    pass

                student_data = StudentCreate(
                    student_number=str(row['学号']),
                    name=str(row['姓名']),
                    gender=str(row.get('性别', '')) if pd.notna(row.get('性别')) else None,
                    phone=str(row.get('手机号', '')) if pd.notna(row.get('手机号')) else None,
                    email=str(row.get('邮箱', '')) if pd.notna(row.get('邮箱')) else None,
                    entrance_year=int(row.get('年级', 0)) if pd.notna(row.get('年级')) else None,
                    school_id=school_id,
                    class_id=class_id
                )

                student_crud.create_student(db, student_data)
                success_count += 1

            except Exception as e:
                errors.append({
                    "row": index + 2,
                    "error": str(e)
                })
                error_count += 1

        # 生成错误报告文件
        error_file_url = None
        if errors:
            error_df = pd.DataFrame(errors)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                error_df.to_excel(tmp.name, index=False)
                error_file_url = f"/static/import_errors/{os.path.basename(tmp.name)}"

        return ImportResult(
            success_count=success_count,
            error_count=error_count,
            errors=errors,
            file_url=error_file_url
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.get("/students/export/template")
async def download_student_template():
    """下载学生导入模板"""
    template_data = {
        '学号': ['S001', 'S002'],
        '姓名': ['张三', '李四'],
        '性别': ['男', '女'],
        '年级': ['2024', '2024'],
        '班级': ['计算机1班', '计算机2班'],
        '手机号': ['13800138001', '13800138002'],
        '邮箱': ['zhangsan@example.com', 'lisi@example.com']
    }

    df = pd.DataFrame(template_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        df.to_excel(tmp.name, index=False)
        return FileResponse(
            tmp.name,
            filename="学生导入模板.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==================== 仪表盘统计 ====================
@router.get("/dashboard/statistics")
async def get_dashboard_statistics(db: Session = Depends(get_db)):
    """获取系统仪表盘核心统计数据"""
    try:
        from ....models.models import User, Course, ClassroomExam
        from sqlalchemy import text
        
        # 计算总用户数
        total_users = db.query(User).count()
        
        # 计算总课程数
        total_courses = db.query(Course).count()
        
        # 计算总实训项目数 (trainings 表可能没有模型，使用原生SQL)
        try:
            total_projects_result = db.execute(text("SELECT COUNT(*) FROM trainings"))
            total_projects = total_projects_result.scalar() or 0
        except Exception:
            total_projects = 0
            
        # 计算总考试数
        total_exams = db.query(ClassroomExam).count()

        # 返回与前端期望的 dashboardData 类似的基础数据块
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={
                "totalUsers": total_users,
                "userIncrease": 0,
                "totalCourses": total_courses,
                "courseIncrease": 0,
                "totalProjects": total_projects,
                "projectIncrease": 0,
                "totalExams": total_exams,
                "examIncrease": 0
            }
        )
    except Exception as e:
        import traceback
        return schemas.ApiResponse(
            code="2000",
            message=f"获取统计数据失败: {str(e)}",
            data={"trace": traceback.format_exc()}
        )