from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.permissions import Role, Permission, PermissionChecker

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/login/access-token"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

class PermissionDependency:
    """权限依赖类，用于在路由中检查权限"""
    
    def __init__(self, permissions: List[Permission]):
        self.permissions = permissions
    
    def __call__(self, current_user: models.User = Depends(get_current_active_user)):
        # 获取用户角色
        user_role = PermissionChecker.get_user_role(
            current_user.username, 
            current_user.is_superuser
        )
        
        # 检查权限
        if not PermissionChecker.has_any_permission(user_role, self.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有执行此操作的权限"
            )
        
        return current_user

class RoleDependency:
    """角色依赖类，用于在路由中检查角色"""
    
    def __init__(self, roles: List[Role]):
        self.roles = roles
    
    def __call__(self, current_user: models.User = Depends(get_current_active_user)):
        # 获取用户角色
        user_role = PermissionChecker.get_user_role(
            current_user.username, 
            current_user.is_superuser
        )
        
        # 检查角色
        if user_role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有执行此操作的权限"
            )
        
        return current_user

# 便捷函数
def require_permission(*permissions: Permission):
    """要求权限装饰器"""
    return Depends(PermissionDependency(list(permissions)))

def require_role(*roles: Role):
    """要求角色装饰器"""
    return Depends(RoleDependency(list(roles)))

def get_current_user_role(current_user: models.User = Depends(get_current_active_user)) -> Role:
    """获取当前用户角色"""
    return PermissionChecker.get_user_role(
        current_user.username, 
        current_user.is_superuser
    )

def check_resource_permission(
    permission: Permission,
    resource_owner_id: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user)
) -> bool:
    """检查资源权限"""
    user_role = PermissionChecker.get_user_role(
        current_user.username, 
        current_user.is_superuser
    )
    
    return PermissionChecker.check_permission(
        user_role,
        permission,
        resource_owner_id,
        str(current_user.id) if current_user.id else None
    )