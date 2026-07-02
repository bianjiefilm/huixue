"""
组织架构和用户管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.models import models as db_models
from app.schemas import schemas
from app.crud import organization_crud
from app.core.security import get_current_user
from app.core.identity import require_authenticated

# 配置日志
logger = logging.getLogger(__name__)


def require_admin(current_user: dict = Depends(get_current_user)) -> int:
    """整个组织架构管理后台(学校/院系/教师/学生/管理员角色)仅限 admin 访问。

    此前这里完全没有鉴权, 任何未登录请求都能增删教师/学生/管理员角色。
    """
    user_id, role = require_authenticated(current_user)
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可访问组织架构管理接口")
    return user_id


# 创建路由器 -- 整个路由要求管理员身份, 见 require_admin
router = APIRouter(dependencies=[Depends(require_admin)])

# ==================== 学校信息管理 ====================

@router.get("/schools/{school_id}", response_model=schemas.SchoolResponse, tags=["学校信息"])
def get_school_info(school_id: int, db: Session = Depends(get_db)):
    """获取学校信息"""
    school = organization_crud.get_school(db, school_id)
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    return school

@router.put("/schools/{school_id}", response_model=schemas.SchoolResponse, tags=["学校信息"])
def update_school_info(
    school_id: int,
    school_update: schemas.SchoolUpdate,
    db: Session = Depends(get_db)
):
    """修改学校信息"""
    try:
        school = organization_crud.update_school(db, school_id, school_update)
        if not school:
            raise HTTPException(status_code=404, detail="学校不存在")
        return school
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学校信息失败: {e}")
        raise HTTPException(status_code=500, detail="更新学校信息失败")

@router.post("/schools/{school_id}/logo", response_model=schemas.LogoUploadResponse, tags=["学校信息"])
def upload_school_logo(
    school_id: int,
    logo_request: schemas.LogoUploadRequest,
    db: Session = Depends(get_db)
):
    """上传学校Logo"""
    try:
        # 更新学校Logo URL
        school_update = schemas.SchoolUpdate(logo_url=logo_request.file_url)
        school = organization_crud.update_school(db, school_id, school_update)
        
        if not school:
            raise HTTPException(status_code=404, detail="学校不存在")
        
        return schemas.LogoUploadResponse(
            logo_url=school.logo_url,
            message="学校LOGO修改成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传学校Logo失败: {e}")
        raise HTTPException(status_code=500, detail="上传Logo失败")

# ==================== 组织架构管理 ====================

@router.get("/schools/{school_id}/organizations/tree", response_model=List[schemas.OrganizationTreeNode], tags=["院系设置"])
def get_organization_tree(school_id: int, db: Session = Depends(get_db)):
    """获取组织架构树"""
    try:
        tree = organization_crud.get_organization_tree(db, school_id)
        return tree
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组织架构树失败: {e}")
        raise HTTPException(status_code=500, detail="获取组织架构树失败")

@router.get("/schools/{school_id}/organizations", response_model=schemas.OrganizationListResponse, tags=["院系设置"])
def search_organizations(
    school_id: int,
    keyword: Optional[str] = Query(None, description="名称、编码搜索"),
    org_type: Optional[schemas.OrganizationTypeEnum] = Query(None, description="组织类型"),
    parent_id: Optional[int] = Query(None, description="父级组织ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """搜索组织架构"""
    try:
        search_request = schemas.OrganizationSearchRequest(
            keyword=keyword,
            org_type=org_type,
            parent_id=parent_id,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        
        organizations, total = organization_crud.search_organizations(db, school_id, search_request)
        
        # 添加统计信息
        org_list = []
        for org in organizations:
            # 统计子组织和用户数量
            children_count = db.query(db_models.Organization).filter(
                db_models.Organization.parent_id == org.id,
                db_models.Organization.is_active == True
            ).count()
            
            user_count = db.query(db_models.UserProfile).filter(
                db_models.UserProfile.organization_id == org.id
            ).count()
            
            org_dict = schemas.OrganizationResponse(
                **org.__dict__,
                children_count=children_count,
                user_count=user_count
            )
            org_list.append(org_dict)
        
        meta = schemas.PaginationMeta(
            total=total,
            page=page,
            page_size=page_size
        )
        
        return schemas.OrganizationListResponse(list=org_list, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索组织架构失败: {e}")
        raise HTTPException(status_code=500, detail="搜索组织架构失败")

@router.post("/schools/{school_id}/organizations", response_model=schemas.OrganizationResponse, tags=["院系设置"])
def create_organization(
    school_id: int,
    org_create: schemas.OrganizationCreate,
    db: Session = Depends(get_db)
):
    """新建组织"""
    try:
        # 设置学校ID
        org_create.school_id = school_id
        
        organization = organization_crud.create_organization(db, org_create)
        return schemas.OrganizationResponse(**organization.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建组织失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建组织失败: {str(e)}")

@router.get("/organizations/{org_id}", response_model=schemas.OrganizationResponse, tags=["院系设置"])
def get_organization(org_id: int, db: Session = Depends(get_db)):
    """获取组织详情"""
    organization = organization_crud.get_organization(db, org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    # 添加统计信息
    children_count = db.query(db_models.Organization).filter(
        db_models.Organization.parent_id == org_id,
        db_models.Organization.is_active == True
    ).count()
    
    user_count = db.query(db_models.UserProfile).filter(
        db_models.UserProfile.organization_id == org_id
    ).count()
    
    return schemas.OrganizationResponse(
        **organization.__dict__,
        children_count=children_count,
        user_count=user_count
    )

@router.put("/organizations/{org_id}", response_model=schemas.OrganizationResponse, tags=["院系设置"])
def update_organization(
    org_id: int,
    org_update: schemas.OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """编辑组织信息"""
    try:
        organization = organization_crud.update_organization(db, org_id, org_update)
        if not organization:
            raise HTTPException(status_code=404, detail="组织不存在")
        
        # 添加统计信息
        children_count = db.query(db_models.Organization).filter(
            db_models.Organization.parent_id == org_id,
            db_models.Organization.is_active == True
        ).count()
        
        user_count = db.query(db_models.UserProfile).filter(
            db_models.UserProfile.organization_id == org_id
        ).count()
        
        return schemas.OrganizationResponse(
            **organization.__dict__,
            children_count=children_count,
            user_count=user_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新组织失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新组织失败: {str(e)}")

@router.delete("/organizations/{org_id}", response_model=schemas.MessageResponse, tags=["院系设置"])
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    """删除组织"""
    try:
        success = organization_crud.delete_organization(db, org_id)
        if not success:
            raise HTTPException(status_code=404, detail="组织不存在")
        
        return schemas.MessageResponse(message="组织删除成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除组织失败: {e}")
        raise HTTPException(status_code=500, detail="删除组织失败")

@router.post("/organizations/batch", response_model=schemas.MessageResponse, tags=["院系设置"])
def batch_update_organizations(
    batch_request: schemas.BatchOperationRequest,
    db: Session = Depends(get_db)
):
    """批量操作组织"""
    try:
        if batch_request.action == "enable":
            count = organization_crud.batch_update_organization_status(db, batch_request.ids, True)
            return schemas.MessageResponse(message=f"成功启用 {count} 个组织")
        elif batch_request.action == "disable":
            count = organization_crud.batch_update_organization_status(db, batch_request.ids, False)
            return schemas.MessageResponse(message=f"成功停用 {count} 个组织")
        elif batch_request.action == "delete":
            # 批量删除需要逐个检查
            deleted_count = 0
            failed_count = 0
            for org_id in batch_request.ids:
                try:
                    organization_crud.delete_organization(db, org_id)
                    deleted_count += 1
                except:
                    failed_count += 1
            
            if failed_count > 0:
                return schemas.MessageResponse(
                    message=f"成功删除 {deleted_count} 个组织，{failed_count} 个组织删除失败（可能包含子组织或用户）"
                )
            else:
                return schemas.MessageResponse(message=f"成功删除 {deleted_count} 个组织")
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作组织失败: {e}")
        raise HTTPException(status_code=500, detail="批量操作失败")

@router.post("/schools/{school_id}/organizations/import", response_model=schemas.ImportResponse, tags=["院系设置"])
def import_organizations(
    school_id: int,
    import_request: schemas.ImportRequest,
    db: Session = Depends(get_db)
):
    """组织导入"""
    try:
        # 创建导入记录
        import_record = db_models.OrganizationImportRecord(
            school_id=school_id,
            file_name=import_request.file_name,
            file_url=import_request.file_url,
            status="PROCESSING",
            imported_by=1  # TODO: 从当前用户获取
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)
        
        # TODO: 实现异步导入逻辑
        # 这里应该启动后台任务处理Excel文件导入
        
        return schemas.ImportResponse(
            import_id=import_record.id,
            status="PROCESSING",
            message="组织导入任务已启动，请稍后查看结果"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"组织导入失败: {e}")
        raise HTTPException(status_code=500, detail="组织导入失败")

@router.get("/schools/{school_id}/organizations/import/{import_id}", response_model=schemas.ImportResultResponse, tags=["院系设置"])
def get_import_result(
    school_id: int,
    import_id: int,
    db: Session = Depends(get_db)
):
    """获取导入结果"""
    import_record = db.query(db_models.OrganizationImportRecord).filter(
        db_models.OrganizationImportRecord.id == import_id,
        db_models.OrganizationImportRecord.school_id == school_id
    ).first()
    
    if not import_record:
        raise HTTPException(status_code=404, detail="导入记录不存在")
    
    return schemas.ImportResultResponse(**import_record.__dict__)

# ==================== 教师管理 ====================

@router.get("/schools/{school_id}/teachers", response_model=schemas.TeacherListResponse, tags=["教师管理"])
def search_teachers(
    school_id: int,
    keyword: Optional[str] = Query(None, description="姓名、工号搜索"),
    organization_id: Optional[int] = Query(None, description="组织ID"),
    status: Optional[schemas.UserStatusEnum] = Query(None, description="用户状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """搜索教师"""
    try:
        search_request = schemas.UserSearchRequest(
            keyword=keyword,
            user_type=schemas.UserTypeEnum.TEACHER,
            organization_id=organization_id,
            status=status,
            page=page,
            page_size=page_size
        )
        
        teachers, total = organization_crud.search_teachers(db, school_id, search_request)
        
        teacher_list = [schemas.TeacherResponse(**teacher) for teacher in teachers]
        
        meta = schemas.PaginationMeta(
            total=total,
            page=page,
            page_size=page_size
        )
        
        return schemas.TeacherListResponse(list=teacher_list, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索教师失败: {e}")
        raise HTTPException(status_code=500, detail="搜索教师失败")

@router.post("/schools/{school_id}/teachers", response_model=schemas.TeacherResponse, tags=["教师管理"])
def create_teacher(
    school_id: int,
    teacher_create: schemas.TeacherCreate,
    db: Session = Depends(get_db)
):
    """添加教师"""
    try:
        user, profile = organization_crud.create_teacher(db, teacher_create, school_id)
        
        # 获取完整的教师信息
        teacher_detail = organization_crud.get_teacher_detail(db, profile.id)
        return schemas.TeacherResponse(**teacher_detail)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建教师失败: {e}")
        raise HTTPException(status_code=500, detail="创建教师失败")

@router.get("/teachers/{teacher_id}", response_model=schemas.TeacherResponse, tags=["教师管理"])
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """获取教师详情"""
    teacher = organization_crud.get_teacher_detail(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    
    return schemas.TeacherResponse(**teacher)

@router.put("/teachers/{teacher_id}", response_model=schemas.TeacherResponse, tags=["教师管理"])
def update_teacher(
    teacher_id: int,
    teacher_update: schemas.TeacherUpdate,
    db: Session = Depends(get_db)
):
    """编辑教师信息"""
    try:
        teacher = organization_crud.update_teacher(db, teacher_id, teacher_update)
        if not teacher:
            raise HTTPException(status_code=404, detail="教师不存在")
        
        return schemas.TeacherResponse(**teacher)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新教师失败: {e}")
        raise HTTPException(status_code=500, detail="更新教师失败")

@router.delete("/teachers/{teacher_id}", response_model=schemas.MessageResponse, tags=["教师管理"])
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """删除教师"""
    try:
        success = organization_crud.delete_teacher(db, teacher_id)
        if not success:
            raise HTTPException(status_code=404, detail="教师不存在")
        
        return schemas.MessageResponse(message="删除后将清除该用户创建的课堂及优秀作业等数据，教师删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除教师失败: {e}")
        raise HTTPException(status_code=500, detail="删除教师失败")

@router.post("/teachers/batch", response_model=schemas.MessageResponse, tags=["教师管理"])
def batch_update_teachers(
    batch_request: schemas.BatchOperationRequest,
    db: Session = Depends(get_db)
):
    """批量操作教师"""
    try:
        if batch_request.action == "enable":
            count = organization_crud.batch_update_user_status(
                db, batch_request.ids, db_models.UserStatusEnum.ACTIVE
            )
            return schemas.MessageResponse(message=f"成功启用 {count} 个教师用户")
        elif batch_request.action == "disable":
            count = organization_crud.batch_update_user_status(
                db, batch_request.ids, db_models.UserStatusEnum.INACTIVE
            )
            return schemas.MessageResponse(message=f"成功停用 {count} 个教师用户")
        elif batch_request.action == "delete":
            count = organization_crud.batch_delete_users(db, batch_request.ids)
            return schemas.MessageResponse(
                message=f"删除后将清除所选用户创建的课堂及优秀作业等数据，成功删除 {count} 个教师用户"
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作教师失败: {e}")
        raise HTTPException(status_code=500, detail="批量操作失败")

@router.post("/teachers/transfer", response_model=schemas.MessageResponse, tags=["教师管理"])
def transfer_teachers(
    transfer_request: schemas.BatchTransferRequest,
    db: Session = Depends(get_db)
):
    """人员调动"""
    try:
        count = organization_crud.batch_transfer_users(
            db,
            transfer_request.user_ids,
            transfer_request.target_organization_id,
            1,  # TODO: 从当前用户获取
            transfer_request.transfer_reason
        )
        return schemas.MessageResponse(message=f"成功调动 {count} 个教师用户")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"教师调动失败: {e}")
        raise HTTPException(status_code=500, detail="教师调动失败")

@router.post("/schools/{school_id}/teachers/import", response_model=schemas.ImportResponse, tags=["教师管理"])
def import_teachers(
    school_id: int,
    import_request: schemas.ImportRequest,
    db: Session = Depends(get_db)
):
    """导入教师"""
    try:
        # 创建导入记录
        import_record = db_models.UserImportRecord(
            school_id=school_id,
            user_type=db_models.UserTypeEnum.TEACHER,
            file_name=import_request.file_name,
            file_url=import_request.file_url,
            status="PROCESSING",
            imported_by=1  # TODO: 从当前用户获取
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)
        
        # TODO: 实现异步导入逻辑
        
        return schemas.ImportResponse(
            import_id=import_record.id,
            status="PROCESSING",
            message="教师导入任务已启动，请稍后查看结果"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"教师导入失败: {e}")
        raise HTTPException(status_code=500, detail="教师导入失败")

# ==================== 学生管理 ====================

@router.get("/schools/{school_id}/students", response_model=schemas.StudentListResponse, tags=["学生管理"])
def search_students(
    school_id: int,
    keyword: Optional[str] = Query(None, description="姓名、学号搜索"),
    organization_id: Optional[int] = Query(None, description="组织ID"),
    status: Optional[schemas.UserStatusEnum] = Query(None, description="用户状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """搜索学生"""
    try:
        search_request = schemas.UserSearchRequest(
            keyword=keyword,
            user_type=schemas.UserTypeEnum.STUDENT,
            organization_id=organization_id,
            status=status,
            page=page,
            page_size=page_size
        )
        
        students, total = organization_crud.search_students(db, school_id, search_request)
        
        student_list = [schemas.StudentResponse(**student) for student in students]
        
        meta = schemas.PaginationMeta(
            total=total,
            page=page,
            page_size=page_size
        )
        
        return schemas.StudentListResponse(list=student_list, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索学生失败: {e}")
        raise HTTPException(status_code=500, detail="搜索学生失败")

@router.post("/schools/{school_id}/students", response_model=schemas.StudentResponse, tags=["学生管理"])
def create_student(
    school_id: int,
    student_create: schemas.StudentCreate,
    db: Session = Depends(get_db)
):
    """添加学生"""
    try:
        user, profile = organization_crud.create_student(db, student_create, school_id)
        
        # 获取完整的学生信息
        student_detail = organization_crud.get_student_detail(db, profile.id)
        return schemas.StudentResponse(**student_detail)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建学生失败: {e}")
        raise HTTPException(status_code=500, detail="创建学生失败")

@router.get("/students/{student_id}", response_model=schemas.StudentResponse, tags=["学生管理"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    """获取学生详情"""
    student = organization_crud.get_student_detail(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    return schemas.StudentResponse(**student)

@router.put("/students/{student_id}", response_model=schemas.StudentResponse, tags=["学生管理"])
def update_student(
    student_id: int,
    student_update: schemas.StudentUpdate,
    db: Session = Depends(get_db)
):
    """编辑学生信息"""
    try:
        student = organization_crud.update_student(db, student_id, student_update)
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")
        
        return schemas.StudentResponse(**student)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新学生失败: {e}")
        raise HTTPException(status_code=500, detail="更新学生失败")

@router.delete("/students/{student_id}", response_model=schemas.MessageResponse, tags=["学生管理"])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """删除学生"""
    try:
        success = organization_crud.delete_student(db, student_id)
        if not success:
            raise HTTPException(status_code=404, detail="学生不存在")
        
        return schemas.MessageResponse(message="删除后将清除该用户学习记录及优秀作业等数据，学生删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除学生失败: {e}")
        raise HTTPException(status_code=500, detail="删除学生失败")

@router.post("/students/batch", response_model=schemas.MessageResponse, tags=["学生管理"])
def batch_update_students(
    batch_request: schemas.BatchOperationRequest,
    db: Session = Depends(get_db)
):
    """批量操作学生"""
    try:
        if batch_request.action == "enable":
            count = organization_crud.batch_update_user_status(
                db, batch_request.ids, db_models.UserStatusEnum.ACTIVE
            )
            return schemas.MessageResponse(message=f"成功启用 {count} 个学生用户")
        elif batch_request.action == "disable":
            count = organization_crud.batch_update_user_status(
                db, batch_request.ids, db_models.UserStatusEnum.INACTIVE
            )
            return schemas.MessageResponse(message=f"成功停用 {count} 个学生用户")
        elif batch_request.action == "delete":
            count = organization_crud.batch_delete_users(db, batch_request.ids)
            return schemas.MessageResponse(
                message=f"删除后将清除所选用户学习记录及优秀作业等数据，成功删除 {count} 个学生用户"
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作学生失败: {e}")
        raise HTTPException(status_code=500, detail="批量操作失败")

@router.post("/students/transfer", response_model=schemas.MessageResponse, tags=["学生管理"])
def transfer_students(
    transfer_request: schemas.BatchTransferRequest,
    db: Session = Depends(get_db)
):
    """人员调动"""
    try:
        count = organization_crud.batch_transfer_users(
            db,
            transfer_request.user_ids,
            transfer_request.target_organization_id,
            1,  # TODO: 从当前用户获取
            transfer_request.transfer_reason
        )
        return schemas.MessageResponse(message=f"成功调动 {count} 个学生用户")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生调动失败: {e}")
        raise HTTPException(status_code=500, detail="学生调动失败")

@router.post("/schools/{school_id}/students/import", response_model=schemas.ImportResponse, tags=["学生管理"])
def import_students(
    school_id: int,
    import_request: schemas.ImportRequest,
    db: Session = Depends(get_db)
):
    """导入学生"""
    try:
        # 创建导入记录
        import_record = db_models.UserImportRecord(
            school_id=school_id,
            user_type=db_models.UserTypeEnum.STUDENT,
            file_name=import_request.file_name,
            file_url=import_request.file_url,
            status="PROCESSING",
            imported_by=1  # TODO: 从当前用户获取
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)
        
        # TODO: 实现异步导入逻辑
        
        return schemas.ImportResponse(
            import_id=import_record.id,
            status="PROCESSING",
            message="学生导入任务已启动，请稍后查看结果"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生导入失败: {e}")
        raise HTTPException(status_code=500, detail="学生导入失败")

# ==================== 角色授权 ====================

@router.get("/schools/{school_id}/admins", response_model=schemas.AdminRoleListResponse, tags=["角色授权"])
def get_admin_roles(
    school_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取管理员列表"""
    try:
        admins = organization_crud.get_admin_roles(db, school_id)
        
        # 分页
        total = len(admins)
        start = (page - 1) * page_size
        end = start + page_size
        admin_list = admins[start:end]
        
        admin_responses = [schemas.AdminRoleResponse(**admin) for admin in admin_list]
        
        meta = schemas.PaginationMeta(
            total=total,
            page=page,
            page_size=page_size
        )
        
        return schemas.AdminRoleListResponse(list=admin_responses, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取管理员列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取管理员列表失败")

@router.post("/schools/{school_id}/admins", response_model=schemas.MessageResponse, tags=["角色授权"])
def create_admin_role(
    school_id: int,
    admin_role_create: schemas.AdminRoleCreate,
    db: Session = Depends(get_db)
):
    """添加管理员"""
    try:
        # 设置学校ID
        admin_role_create.school_id = school_id
        
        organization_crud.create_admin_role(
            db, admin_role_create, 1  # TODO: 从当前用户获取
        )
        return schemas.MessageResponse(message="授权成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加管理员失败: {e}")
        raise HTTPException(status_code=500, detail="添加管理员失败")

@router.delete("/admins/{role_id}", response_model=schemas.MessageResponse, tags=["角色授权"])
def delete_admin_role(role_id: int, db: Session = Depends(get_db)):
    """移除管理员"""
    try:
        success = organization_crud.delete_admin_role(db, role_id)
        if not success:
            raise HTTPException(status_code=404, detail="管理员角色不存在")
        
        return schemas.MessageResponse(message="操作成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除管理员失败: {e}")
        raise HTTPException(status_code=500, detail="移除管理员失败")

@router.post("/admins/batch-delete", response_model=schemas.MessageResponse, tags=["角色授权"])
def batch_delete_admin_roles(
    batch_request: schemas.BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量移除管理员"""
    try:
        count = organization_crud.batch_delete_admin_roles(db, batch_request.ids)
        return schemas.MessageResponse(message=f"操作成功，已移除 {count} 个管理员角色")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量移除管理员失败: {e}")
        raise HTTPException(status_code=500, detail="批量移除管理员失败")

# ==================== 组织架构选择器 ====================

@router.get("/schools/{school_id}/organizations/selector", response_model=schemas.OrganizationSelectorResponse, tags=["组织架构选择器"])
def get_organization_selector(
    school_id: int,
    exclude_school: bool = Query(True, description="是否排除学校节点"),
    db: Session = Depends(get_db)
):
    """获取组织架构选择器（用于人员调动等场景）"""
    try:
        tree = organization_crud.get_organization_selector_tree(db, school_id, exclude_school)
        
        # 转换为选择器节点格式
        def convert_to_selector_nodes(nodes):
            result = []
            for node in nodes:
                selector_node = schemas.OrganizationSelectorNode(
                    id=node["id"],
                    name=node["name"],
                    org_type=schemas.OrganizationTypeEnum(node["org_type"]),
                    level=node["level"],
                    selectable=node["selectable"],
                    children=convert_to_selector_nodes(node["children"])
                )
                result.append(selector_node)
            return result
        
        selector_tree = convert_to_selector_nodes(tree)
        
        return schemas.OrganizationSelectorResponse(tree=selector_tree)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组织架构选择器失败: {e}")
        raise HTTPException(status_code=500, detail="获取组织架构选择器失败")

# ==================== 统计信息 ====================

@router.get("/schools/{school_id}/stats/organizations", response_model=schemas.OrganizationStatsResponse, tags=["统计信息"])
def get_organization_stats(school_id: int, db: Session = Depends(get_db)):
    """获取组织架构统计"""
    try:
        stats = organization_crud.get_organization_stats(db, school_id)
        return schemas.OrganizationStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组织架构统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取组织架构统计失败")

@router.get("/schools/{school_id}/stats/users", response_model=schemas.UserStatsResponse, tags=["统计信息"])
def get_user_stats(school_id: int, db: Session = Depends(get_db)):
    """获取用户统计"""
    try:
        stats = organization_crud.get_user_stats(db, school_id)
        return schemas.UserStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户统计失败") 