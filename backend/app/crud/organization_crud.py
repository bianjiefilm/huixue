"""
组织架构和用户管理CRUD操作
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.models import models as db_models
from app.schemas import schemas
from app.core.database import get_db

# ==================== 学校信息CRUD ====================

def get_school(db: Session, school_id: int) -> Optional[db_models.School]:
    """获取学校信息"""
    return db.query(db_models.School).filter(db_models.School.id == school_id).first()

def get_schools(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.School]:
    """获取学校列表"""
    return db.query(db_models.School).filter(db_models.School.is_active == True).offset(skip).limit(limit).all()

def create_school(db: Session, school: schemas.SchoolCreate) -> db_models.School:
    """创建学校"""
    db_school = db_models.School(**school.model_dump())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

def update_school(db: Session, school_id: int, school_update: schemas.SchoolUpdate) -> Optional[db_models.School]:
    """更新学校信息"""
    db_school = get_school(db, school_id)
    if not db_school:
        return None
    
    update_data = school_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_school, field, value)
    
    db.commit()
    db.refresh(db_school)
    return db_school

def delete_school(db: Session, school_id: int) -> bool:
    """删除学校（软删除）"""
    db_school = get_school(db, school_id)
    if not db_school:
        return False
    
    db_school.is_active = False
    db.commit()
    return True

# ==================== 组织架构CRUD ====================

def get_organization(db: Session, org_id: int) -> Optional[db_models.Organization]:
    """获取组织信息"""
    return db.query(db_models.Organization).filter(
        and_(db_models.Organization.id == org_id, db_models.Organization.is_active == True)
    ).first()

def get_organizations_by_school(db: Session, school_id: int, parent_id: Optional[int] = None) -> List[db_models.Organization]:
    """获取学校下的组织列表"""
    query = db.query(db_models.Organization).filter(
        and_(
            db_models.Organization.school_id == school_id,
            db_models.Organization.is_active == True
        )
    )
    
    if parent_id is not None:
        query = query.filter(db_models.Organization.parent_id == parent_id)
    else:
        query = query.filter(db_models.Organization.parent_id.is_(None))
    
    return query.order_by(db_models.Organization.order_index, db_models.Organization.id).all()

def get_organization_tree(db: Session, school_id: int) -> List[Dict[str, Any]]:
    """获取组织架构树"""
    def build_tree(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        orgs = get_organizations_by_school(db, school_id, parent_id)
        result = []
        
        for org in orgs:
            # 统计子组织和用户数量
            children_count = db.query(db_models.Organization).filter(
                and_(
                    db_models.Organization.parent_id == org.id,
                    db_models.Organization.is_active == True
                )
            ).count()
            
            user_count = db.query(db_models.UserProfile).filter(
                and_(
                    db_models.UserProfile.organization_id == org.id,
                    db_models.UserProfile.status == db_models.UserStatusEnum.ACTIVE
                )
            ).count()
            
            org_dict = {
                "id": org.id,
                "name": org.name,
                "code": org.code,
                "org_type": org.org_type.value,
                "level": org.level,
                "is_active": org.is_active,
                "children_count": children_count,
                "user_count": user_count,
                "children": build_tree(org.id)
            }
            result.append(org_dict)
        
        return result
    
    return build_tree()

def create_organization(db: Session, org: schemas.OrganizationCreate) -> db_models.Organization:
    """创建组织"""
    # 计算层级
    level = 1
    if org.parent_id:
        parent = get_organization(db, org.parent_id)
        if parent:
            level = parent.level + 1
    
    db_org = db_models.Organization(
        **org.model_dump(),
        level=level
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

def update_organization(db: Session, org_id: int, org_update: schemas.OrganizationUpdate) -> Optional[db_models.Organization]:
    """更新组织信息"""
    db_org = get_organization(db, org_id)
    if not db_org:
        return None
    
    update_data = org_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_org, field, value)
    
    db.commit()
    db.refresh(db_org)
    return db_org

def delete_organization(db: Session, org_id: int) -> bool:
    """删除组织（需要检查是否有子组织和用户）"""
    db_org = get_organization(db, org_id)
    if not db_org:
        return False
    
    # 检查是否有子组织
    children_count = db.query(db_models.Organization).filter(
        and_(
            db_models.Organization.parent_id == org_id,
            db_models.Organization.is_active == True
        )
    ).count()
    
    if children_count > 0:
        raise ValueError("该组织下还有子组织，无法删除")
    
    # 检查是否有用户
    user_count = db.query(db_models.UserProfile).filter(
        db_models.UserProfile.organization_id == org_id
    ).count()
    
    if user_count > 0:
        raise ValueError("该组织下还有用户，无法删除")
    
    db_org.is_active = False
    db.commit()
    return True

def batch_update_organization_status(db: Session, org_ids: List[int], is_active: bool) -> int:
    """批量更新组织状态"""
    updated_count = db.query(db_models.Organization).filter(
        db_models.Organization.id.in_(org_ids)
    ).update({"is_active": is_active}, synchronize_session=False)
    
    db.commit()
    return updated_count

def search_organizations(db: Session, school_id: int, search_request: schemas.OrganizationSearchRequest) -> tuple:
    """搜索组织"""
    query = db.query(db_models.Organization).filter(
        db_models.Organization.school_id == school_id
    )
    
    # 关键词搜索
    if search_request.keyword:
        keyword = f"%{search_request.keyword}%"
        query = query.filter(
            or_(
                db_models.Organization.name.like(keyword),
                db_models.Organization.code.like(keyword)
            )
        )
    
    # 组织类型筛选
    if search_request.org_type:
        query = query.filter(db_models.Organization.org_type == search_request.org_type)
    
    # 父级组织筛选
    if search_request.parent_id is not None:
        query = query.filter(db_models.Organization.parent_id == search_request.parent_id)
    
    # 状态筛选
    if search_request.is_active is not None:
        query = query.filter(db_models.Organization.is_active == search_request.is_active)
    
    # 总数
    total = query.count()
    
    # 分页
    organizations = query.order_by(
        db_models.Organization.level,
        db_models.Organization.order_index,
        db_models.Organization.id
    ).offset((search_request.page - 1) * search_request.page_size).limit(search_request.page_size).all()
    
    return organizations, total

# ==================== 用户详细信息CRUD ====================

def get_user_profile(db: Session, user_id: int) -> Optional[db_models.UserProfile]:
    """获取用户详细信息"""
    return db.query(db_models.UserProfile).filter(db_models.UserProfile.user_id == user_id).first()

def get_user_profile_by_employee_id(db: Session, employee_id: str) -> Optional[db_models.UserProfile]:
    """根据工号/学号获取用户信息"""
    return db.query(db_models.UserProfile).filter(db_models.UserProfile.employee_id == employee_id).first()

def create_user_profile(db: Session, profile: schemas.UserProfileCreate) -> db_models.UserProfile:
    """创建用户详细信息"""
    db_profile = db_models.UserProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_user_profile(db: Session, user_id: int, profile_update: schemas.UserProfileUpdate) -> Optional[db_models.UserProfile]:
    """更新用户详细信息"""
    db_profile = get_user_profile(db, user_id)
    if not db_profile:
        return None
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

def delete_user_profile(db: Session, user_id: int) -> bool:
    """删除用户详细信息"""
    db_profile = get_user_profile(db, user_id)
    if not db_profile:
        return False
    
    db.delete(db_profile)
    db.commit()
    return True

# ==================== 教师管理CRUD ====================

def create_teacher(db: Session, teacher: schemas.TeacherCreate, school_id: int) -> tuple:
    """创建教师用户"""
    # 检查用户名和邮箱是否已存在
    existing_user = db.query(db_models.User).filter(
        or_(
            db_models.User.username == teacher.username,
            db_models.User.email == teacher.email
        )
    ).first()
    
    if existing_user:
        if existing_user.username == teacher.username:
            raise ValueError("用户名已存在")
        if existing_user.email == teacher.email:
            raise ValueError("邮箱已存在")
    
    # 检查工号是否已存在
    if teacher.employee_id:
        existing_profile = get_user_profile_by_employee_id(db, teacher.employee_id)
        if existing_profile:
            raise ValueError("工号已存在")
    
    # 创建基础用户
    db_user = db_models.User(
        username=teacher.username,
        email=teacher.email,
        full_name=teacher.full_name
    )
    db.add(db_user)
    db.flush()  # 获取用户ID
    
    # 创建用户详细信息
    db_profile = db_models.UserProfile(
        user_id=db_user.id,
        school_id=school_id,
        organization_id=teacher.organization_id,
        user_type=db_models.UserTypeEnum.TEACHER,
        real_name=teacher.real_name,
        employee_id=teacher.employee_id,
        gender=teacher.gender,
        birth_date=teacher.birth_date,
        id_card=teacher.id_card,
        phone=teacher.phone,
        title=teacher.title,
        department=teacher.department,
        research_direction=teacher.research_direction
    )
    db.add(db_profile)
    
    db.commit()
    db.refresh(db_user)
    db.refresh(db_profile)
    
    return db_user, db_profile

def get_teachers_by_organization(db: Session, school_id: int, organization_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取组织下的教师列表"""
    query = db.query(
        db_models.UserProfile,
        db_models.User,
        db_models.Organization.name.label('organization_name')
    ).join(
        db_models.User, db_models.UserProfile.user_id == db_models.User.id
    ).outerjoin(
        db_models.Organization, db_models.UserProfile.organization_id == db_models.Organization.id
    ).filter(
        and_(
            db_models.UserProfile.school_id == school_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.TEACHER
        )
    )
    
    if organization_id:
        query = query.filter(db_models.UserProfile.organization_id == organization_id)
    
    results = query.order_by(db_models.UserProfile.created_at.desc()).all()
    
    teachers = []
    for profile, user, org_name in results:
        teacher_dict = {
            "id": profile.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "real_name": profile.real_name,
            "employee_id": profile.employee_id,
            "gender": profile.gender,
            "phone": profile.phone,
            "title": profile.title,
            "department": profile.department,
            "organization_id": profile.organization_id,
            "organization_name": org_name,
            "status": profile.status,
            "is_admin": profile.is_admin,
            "last_login_at": profile.last_login_at,
            "created_at": profile.created_at
        }
        teachers.append(teacher_dict)
    
    return teachers

def search_teachers(db: Session, school_id: int, search_request: schemas.UserSearchRequest) -> tuple:
    """搜索教师"""
    query = db.query(
        db_models.UserProfile,
        db_models.User,
        db_models.Organization.name.label('organization_name')
    ).join(
        db_models.User, db_models.UserProfile.user_id == db_models.User.id
    ).outerjoin(
        db_models.Organization, db_models.UserProfile.organization_id == db_models.Organization.id
    ).filter(
        and_(
            db_models.UserProfile.school_id == school_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.TEACHER
        )
    )
    
    # 关键词搜索
    if search_request.keyword:
        keyword = f"%{search_request.keyword}%"
        query = query.filter(
            or_(
                db_models.UserProfile.real_name.like(keyword),
                db_models.UserProfile.employee_id.like(keyword),
                db_models.User.username.like(keyword)
            )
        )
    
    # 组织筛选
    if search_request.organization_id:
        query = query.filter(db_models.UserProfile.organization_id == search_request.organization_id)
    
    # 状态筛选
    if search_request.status:
        query = query.filter(db_models.UserProfile.status == search_request.status)
    
    # 总数
    total = query.count()
    
    # 分页
    results = query.order_by(db_models.UserProfile.created_at.desc()).offset(
        (search_request.page - 1) * search_request.page_size
    ).limit(search_request.page_size).all()
    
    teachers = []
    for profile, user, org_name in results:
        teacher_dict = {
            "id": profile.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "real_name": profile.real_name,
            "employee_id": profile.employee_id,
            "gender": profile.gender,
            "phone": profile.phone,
            "title": profile.title,
            "department": profile.department,
            "organization_id": profile.organization_id,
            "organization_name": org_name,
            "status": profile.status,
            "is_admin": profile.is_admin,
            "last_login_at": profile.last_login_at,
            "created_at": profile.created_at
        }
        teachers.append(teacher_dict)
    
    return teachers, total

def update_teacher(db: Session, teacher_id: int, teacher_update: schemas.TeacherUpdate) -> Optional[Dict[str, Any]]:
    """更新教师信息"""
    db_profile = db.query(db_models.UserProfile).filter(
        and_(
            db_models.UserProfile.id == teacher_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.TEACHER
        )
    ).first()
    
    if not db_profile:
        return None
    
    # 更新基础用户信息
    if teacher_update.full_name:
        db_user = db.query(db_models.User).filter(db_models.User.id == db_profile.user_id).first()
        if db_user:
            db_user.full_name = teacher_update.full_name
    
    # 更新详细信息
    update_data = teacher_update.model_dump(exclude_unset=True, exclude={'full_name'})
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db.commit()
    db.refresh(db_profile)
    
    return get_teacher_detail(db, teacher_id)

def get_teacher_detail(db: Session, teacher_id: int) -> Optional[Dict[str, Any]]:
    """获取教师详细信息"""
    result = db.query(
        db_models.UserProfile,
        db_models.User,
        db_models.Organization.name.label('organization_name')
    ).join(
        db_models.User, db_models.UserProfile.user_id == db_models.User.id
    ).outerjoin(
        db_models.Organization, db_models.UserProfile.organization_id == db_models.Organization.id
    ).filter(
        and_(
            db_models.UserProfile.id == teacher_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.TEACHER
        )
    ).first()
    
    if not result:
        return None
    
    profile, user, org_name = result
    return {
        "id": profile.id,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "real_name": profile.real_name,
        "employee_id": profile.employee_id,
        "gender": profile.gender,
        "phone": profile.phone,
        "title": profile.title,
        "department": profile.department,
        "organization_id": profile.organization_id,
        "organization_name": org_name,
        "status": profile.status,
        "is_admin": profile.is_admin,
        "last_login_at": profile.last_login_at,
        "created_at": profile.created_at
    }

def delete_teacher(db: Session, teacher_id: int) -> bool:
    """删除教师"""
    db_profile = db.query(db_models.UserProfile).filter(
        and_(
            db_models.UserProfile.id == teacher_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.TEACHER
        )
    ).first()
    
    if not db_profile:
        return False
    
    # 删除用户详细信息
    user_id = db_profile.user_id
    db.delete(db_profile)
    
    # 删除基础用户
    db_user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
    
    db.commit()
    return True

# ==================== 学生管理CRUD ====================

def create_student(db: Session, student: schemas.StudentCreate, school_id: int) -> tuple:
    """创建学生用户"""
    # 检查用户名和邮箱是否已存在
    existing_user = db.query(db_models.User).filter(
        or_(
            db_models.User.username == student.username,
            db_models.User.email == student.email
        )
    ).first()
    
    if existing_user:
        if existing_user.username == student.username:
            raise ValueError("用户名已存在")
        if existing_user.email == student.email:
            raise ValueError("邮箱已存在")
    
    # 检查学号是否已存在
    if student.employee_id:
        existing_profile = get_user_profile_by_employee_id(db, student.employee_id)
        if existing_profile:
            raise ValueError("学号已存在")
    
    # 创建基础用户
    db_user = db_models.User(
        username=student.username,
        email=student.email,
        full_name=student.full_name
    )
    db.add(db_user)
    db.flush()  # 获取用户ID
    
    # 创建用户详细信息
    db_profile = db_models.UserProfile(
        user_id=db_user.id,
        school_id=school_id,
        organization_id=student.organization_id,
        user_type=db_models.UserTypeEnum.STUDENT,
        real_name=student.real_name,
        employee_id=student.employee_id,
        gender=student.gender,
        birth_date=student.birth_date,
        id_card=student.id_card,
        phone=student.phone,
        admission_year=student.admission_year,
        graduation_year=student.graduation_year,
        student_status=student.student_status
    )
    db.add(db_profile)
    
    db.commit()
    db.refresh(db_user)
    db.refresh(db_profile)
    
    return db_user, db_profile

def search_students(db: Session, school_id: int, search_request: schemas.UserSearchRequest) -> tuple:
    """搜索学生"""
    query = db.query(
        db_models.UserProfile,
        db_models.User,
        db_models.Organization.name.label('organization_name')
    ).join(
        db_models.User, db_models.UserProfile.user_id == db_models.User.id
    ).outerjoin(
        db_models.Organization, db_models.UserProfile.organization_id == db_models.Organization.id
    ).filter(
        and_(
            db_models.UserProfile.school_id == school_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.STUDENT
        )
    )
    
    # 关键词搜索
    if search_request.keyword:
        keyword = f"%{search_request.keyword}%"
        query = query.filter(
            or_(
                db_models.UserProfile.real_name.like(keyword),
                db_models.UserProfile.employee_id.like(keyword),
                db_models.User.username.like(keyword)
            )
        )
    
    # 组织筛选
    if search_request.organization_id:
        query = query.filter(db_models.UserProfile.organization_id == search_request.organization_id)
    
    # 状态筛选
    if search_request.status:
        query = query.filter(db_models.UserProfile.status == search_request.status)
    
    # 总数
    total = query.count()
    
    # 分页
    results = query.order_by(db_models.UserProfile.created_at.desc()).offset(
        (search_request.page - 1) * search_request.page_size
    ).limit(search_request.page_size).all()
    
    students = []
    for profile, user, org_name in results:
        student_dict = {
            "id": profile.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "real_name": profile.real_name,
            "employee_id": profile.employee_id,
            "gender": profile.gender,
            "phone": profile.phone,
            "admission_year": profile.admission_year,
            "graduation_year": profile.graduation_year,
            "student_status": profile.student_status,
            "organization_id": profile.organization_id,
            "organization_name": org_name,
            "status": profile.status,
            "last_login_at": profile.last_login_at,
            "created_at": profile.created_at
        }
        students.append(student_dict)
    
    return students, total

def update_student(db: Session, student_id: int, student_update: schemas.StudentUpdate) -> Optional[Dict[str, Any]]:
    """更新学生信息"""
    db_profile = db.query(db_models.UserProfile).filter(
        and_(
            db_models.UserProfile.id == student_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.STUDENT
        )
    ).first()
    
    if not db_profile:
        return None
    
    # 更新基础用户信息
    if student_update.full_name:
        db_user = db.query(db_models.User).filter(db_models.User.id == db_profile.user_id).first()
        if db_user:
            db_user.full_name = student_update.full_name
    
    # 更新详细信息
    update_data = student_update.model_dump(exclude_unset=True, exclude={'full_name'})
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db.commit()
    db.refresh(db_profile)
    
    return get_student_detail(db, student_id)

def get_student_detail(db: Session, student_id: int) -> Optional[Dict[str, Any]]:
    """获取学生详细信息"""
    result = db.query(
        db_models.UserProfile,
        db_models.User,
        db_models.Organization.name.label('organization_name')
    ).join(
        db_models.User, db_models.UserProfile.user_id == db_models.User.id
    ).outerjoin(
        db_models.Organization, db_models.UserProfile.organization_id == db_models.Organization.id
    ).filter(
        and_(
            db_models.UserProfile.id == student_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.STUDENT
        )
    ).first()
    
    if not result:
        return None
    
    profile, user, org_name = result
    return {
        "id": profile.id,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "real_name": profile.real_name,
        "employee_id": profile.employee_id,
        "gender": profile.gender,
        "phone": profile.phone,
        "admission_year": profile.admission_year,
        "graduation_year": profile.graduation_year,
        "student_status": profile.student_status,
        "organization_id": profile.organization_id,
        "organization_name": org_name,
        "status": profile.status,
        "last_login_at": profile.last_login_at,
        "created_at": profile.created_at
    }

def delete_student(db: Session, student_id: int) -> bool:
    """删除学生"""
    db_profile = db.query(db_models.UserProfile).filter(
        and_(
            db_models.UserProfile.id == student_id,
            db_models.UserProfile.user_type == db_models.UserTypeEnum.STUDENT
        )
    ).first()
    
    if not db_profile:
        return False
    
    # 删除用户详细信息
    user_id = db_profile.user_id
    db.delete(db_profile)
    
    # 删除基础用户
    db_user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
    
    db.commit()
    return True

# ==================== 管理员角色CRUD ====================

def get_admin_roles(db: Session, school_id: int) -> List[Dict[str, Any]]:
    """获取管理员列表"""
    results = db.query(
        db_models.AdminRole,
        db_models.User,
        db_models.UserProfile,
        db_models.Organization.name.label('organization_name')
    ).join(
        db_models.User, db_models.AdminRole.user_id == db_models.User.id
    ).join(
        db_models.UserProfile, db_models.AdminRole.user_id == db_models.UserProfile.user_id
    ).outerjoin(
        db_models.Organization, db_models.UserProfile.organization_id == db_models.Organization.id
    ).filter(
        and_(
            db_models.AdminRole.school_id == school_id,
            db_models.AdminRole.is_active == True
        )
    ).order_by(db_models.AdminRole.granted_at.desc()).all()
    
    admins = []
    for role, user, profile, org_name in results:
        admin_dict = {
            "id": role.id,
            "user_id": user.id,
            "school_id": role.school_id,
            "granted_by": role.granted_by,
            "granted_at": role.granted_at,
            "is_active": role.is_active,
            "username": user.username,
            "real_name": profile.real_name,
            "employee_id": profile.employee_id,
            "organization_name": org_name
        }
        admins.append(admin_dict)
    
    return admins

def create_admin_role(db: Session, admin_role: schemas.AdminRoleCreate, granted_by: int) -> db_models.AdminRole:
    """授权管理员"""
    # 检查是否已经是管理员
    existing_role = db.query(db_models.AdminRole).filter(
        and_(
            db_models.AdminRole.user_id == admin_role.user_id,
            db_models.AdminRole.school_id == admin_role.school_id,
            db_models.AdminRole.is_active == True
        )
    ).first()
    
    if existing_role:
        raise ValueError("该用户已经是管理员")
    
    db_role = db_models.AdminRole(
        user_id=admin_role.user_id,
        school_id=admin_role.school_id,
        granted_by=granted_by
    )
    db.add(db_role)
    
    # 更新用户详细信息中的管理员标识
    db_profile = get_user_profile(db, admin_role.user_id)
    if db_profile:
        db_profile.is_admin = True
    
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_admin_role(db: Session, role_id: int) -> bool:
    """取消管理员授权"""
    db_role = db.query(db_models.AdminRole).filter(db_models.AdminRole.id == role_id).first()
    if not db_role:
        return False
    
    # 更新用户详细信息中的管理员标识
    db_profile = get_user_profile(db, db_role.user_id)
    if db_profile:
        db_profile.is_admin = False
    
    db_role.is_active = False
    db.commit()
    return True

def batch_delete_admin_roles(db: Session, role_ids: List[int]) -> int:
    """批量取消管理员授权"""
    # 获取要取消的角色
    roles = db.query(db_models.AdminRole).filter(db_models.AdminRole.id.in_(role_ids)).all()
    
    # 更新用户详细信息中的管理员标识
    for role in roles:
        db_profile = get_user_profile(db, role.user_id)
        if db_profile:
            db_profile.is_admin = False
    
    # 批量更新角色状态
    updated_count = db.query(db_models.AdminRole).filter(
        db_models.AdminRole.id.in_(role_ids)
    ).update({"is_active": False}, synchronize_session=False)
    
    db.commit()
    return updated_count

# ==================== 批量操作CRUD ====================

def batch_update_user_status(db: Session, user_ids: List[int], status: db_models.UserStatusEnum) -> int:
    """批量更新用户状态"""
    updated_count = db.query(db_models.UserProfile).filter(
        db_models.UserProfile.id.in_(user_ids)
    ).update({"status": status}, synchronize_session=False)
    
    db.commit()
    return updated_count

def batch_transfer_users(db: Session, user_ids: List[int], target_organization_id: int, transferred_by: int, transfer_reason: Optional[str] = None) -> int:
    """批量调动用户"""
    # 记录调动历史
    for user_id in user_ids:
        db_profile = db.query(db_models.UserProfile).filter(db_models.UserProfile.id == user_id).first()
        if db_profile:
            # 创建调动记录
            transfer_record = db_models.UserTransferRecord(
                user_id=db_profile.user_id,
                from_organization_id=db_profile.organization_id,
                to_organization_id=target_organization_id,
                transfer_reason=transfer_reason,
                transferred_by=transferred_by
            )
            db.add(transfer_record)
    
    # 批量更新组织
    updated_count = db.query(db_models.UserProfile).filter(
        db_models.UserProfile.id.in_(user_ids)
    ).update({"organization_id": target_organization_id}, synchronize_session=False)
    
    db.commit()
    return updated_count

def batch_delete_users(db: Session, user_ids: List[int]) -> int:
    """批量删除用户"""
    # 获取要删除的用户详细信息
    profiles = db.query(db_models.UserProfile).filter(db_models.UserProfile.id.in_(user_ids)).all()
    
    # 删除用户详细信息
    deleted_count = db.query(db_models.UserProfile).filter(
        db_models.UserProfile.id.in_(user_ids)
    ).delete(synchronize_session=False)
    
    # 删除基础用户
    user_ids_to_delete = [profile.user_id for profile in profiles]
    db.query(db_models.User).filter(
        db_models.User.id.in_(user_ids_to_delete)
    ).delete(synchronize_session=False)
    
    db.commit()
    return deleted_count

# ==================== 统计信息CRUD ====================

def get_organization_stats(db: Session, school_id: int) -> Dict[str, int]:
    """获取组织架构统计"""
    stats = {}
    
    # 总组织数
    stats['total_organizations'] = db.query(db_models.Organization).filter(
        and_(
            db_models.Organization.school_id == school_id,
            db_models.Organization.is_active == True
        )
    ).count()
    
    # 各类型组织数量
    for org_type in db_models.OrganizationTypeEnum:
        count = db.query(db_models.Organization).filter(
            and_(
                db_models.Organization.school_id == school_id,
                db_models.Organization.org_type == org_type,
                db_models.Organization.is_active == True
            )
        ).count()
        
        if org_type == db_models.OrganizationTypeEnum.COLLEGE:
            stats['college_count'] = count
        elif org_type == db_models.OrganizationTypeEnum.MAJOR:
            stats['major_count'] = count
        elif org_type == db_models.OrganizationTypeEnum.GRADE:
            stats['grade_count'] = count
        elif org_type == db_models.OrganizationTypeEnum.CLASS:
            stats['class_count'] = count
    
    return stats

def get_user_stats(db: Session, school_id: int) -> Dict[str, int]:
    """获取用户统计"""
    stats = {}
    
    # 总用户数
    stats['total_users'] = db.query(db_models.UserProfile).filter(
        db_models.UserProfile.school_id == school_id
    ).count()
    
    # 各类型用户数量
    for user_type in db_models.UserTypeEnum:
        count = db.query(db_models.UserProfile).filter(
            and_(
                db_models.UserProfile.school_id == school_id,
                db_models.UserProfile.user_type == user_type
            )
        ).count()
        
        if user_type == db_models.UserTypeEnum.TEACHER:
            stats['teacher_count'] = count
        elif user_type == db_models.UserTypeEnum.STUDENT:
            stats['student_count'] = count
    
    # 管理员数量
    stats['admin_count'] = db.query(db_models.AdminRole).filter(
        and_(
            db_models.AdminRole.school_id == school_id,
            db_models.AdminRole.is_active == True
        )
    ).count()
    
    # 各状态用户数量
    for status in db_models.UserStatusEnum:
        count = db.query(db_models.UserProfile).filter(
            and_(
                db_models.UserProfile.school_id == school_id,
                db_models.UserProfile.status == status
            )
        ).count()
        
        if status == db_models.UserStatusEnum.ACTIVE:
            stats['active_count'] = count
        elif status == db_models.UserStatusEnum.INACTIVE:
            stats['inactive_count'] = count
    
    return stats

# ==================== 组织架构选择器CRUD ====================

def get_organization_selector_tree(db: Session, school_id: int, exclude_school: bool = True) -> List[Dict[str, Any]]:
    """获取组织架构选择器树（用于人员调动等场景）"""
    def build_selector_tree(parent_id: Optional[int] = None, level: int = 1) -> List[Dict[str, Any]]:
        orgs = get_organizations_by_school(db, school_id, parent_id)
        result = []
        
        for org in orgs:
            # 学校节点通常不可选择
            selectable = not (exclude_school and org.org_type == db_models.OrganizationTypeEnum.SCHOOL)
            
            org_dict = {
                "id": org.id,
                "name": org.name,
                "org_type": org.org_type.value,
                "level": org.level,
                "selectable": selectable,
                "children": build_selector_tree(org.id, level + 1)
            }
            result.append(org_dict)
        
        return result
    
    return build_selector_tree() 