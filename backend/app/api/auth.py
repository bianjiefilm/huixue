from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user
)
from app.models.models import User, UserProfile
from app.schemas.schemas import Token, UserResponse, UserLogin
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# 临时的用户认证 - 生产环境应该使用真实的认证系统
def simple_auth(username: str, password: str, db: Session = None) -> Optional[Dict]:
    """简单的用户认证，现在生成 JWT token 以确保与 API 认证一致"""
    # 这里使用硬编码的用户，生产环境应该查询数据库
    # [修复] 更新ID以匹配数据库中的实际用户ID
    users = {
        "admin": {"password": "admin123", "id": 1, "name": "管理员", "role": "admin"},
        "teacher1": {"password": "teacher123", "id": 29, "name": "教师", "role": "teacher"},
        "student1": {"password": "student123", "id": 30, "name": "学生1", "role": "student"},
        "student2": {"password": "student123", "id": 31, "name": "学生2", "role": "student"},
        "student3": {"password": "student123", "id": 32, "name": "学生3", "role": "student"}
    }

    user = users.get(username)
    if user and user["password"] == password:
        # 如果提供了数据库会话，必须使用已存在的生产用户。生产登录不得自动创建账号。
        if db is not None:
            from app.models.models import User, UserProfile
            existing_user = db.query(User).filter(User.username == username).first()
            if not existing_user:
                logger.warning(f"Simple auth user missing in database: {username}")
                return None
            # 用数据库中的真实ID覆盖硬编码ID
            user["id"] = existing_user.id

        # 生成 JWT token（在获取真实ID之后）
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={
                "sub": username,
                "user_id": user["id"],
                "role": user["role"]
            },
            expires_delta=access_token_expires
        )

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": username,
                "name": user["name"],
                "role": user["role"]
            }
        }
    return None

@router.post("/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """User login endpoint - accepts JSON data"""
    logger.info(f"Login attempt for username: {login_data.username}")

    # BUG-001 fix: reject empty username or password immediately
    if not login_data.username or not login_data.username.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username cannot be empty",
        )
    if not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password cannot be empty",
        )

    # First try simple authentication for test users (with database auto-creation)
    simple_auth_result = simple_auth(login_data.username, login_data.password, db)
    if simple_auth_result:
        logger.info(f"Simple auth successful for user: {login_data.username}")
        # Return format expected by frontend
        response_data = {
            "token": {
                "access_token": simple_auth_result["token"],
                "token_type": "bearer"
            },
            "user": {
                "id": simple_auth_result["user"]["id"],
                "username": simple_auth_result["user"]["username"],
                "name": simple_auth_result["user"]["name"],
                "role": simple_auth_result["user"]["role"]
            }
        }
        logger.info(
            "Login successful for user: %s, user_id=%s, role=%s",
            login_data.username,
            response_data["user"]["id"],
            response_data["user"]["role"],
        )
        return response_data

    # For database users, try to find user first
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        logger.warning(f"User not found: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User found: {user.username}, email: {user.email}, is_superuser: {user.is_superuser}")

    # BUG-003 fix: reject disabled users
    if not user.is_active:
        logger.warning(f"Disabled user attempted login: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # BUG-002 fix: always verify password — never silently skip on exception
    try:
        password_valid = verify_password(login_data.password, user.hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error for user: {login_data.username}, error: {e}")
        password_valid = False

    if not password_valid:
        logger.warning(f"Invalid password for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Determine role: first check user_profiles, then fallback to username prefix
    role = "student"  # Default
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if user_profile:
        user_type = user_profile.user_type
        if hasattr(user_type, 'value'):
            user_type = user_type.value
        if user_type:
            role = user_type.lower()
    else:
        if user.is_superuser:
            role = "admin"
        elif user.username.startswith("student") or "student" in user.username.lower():
            role = "student"
        elif user.username.startswith("teacher") or "teacher" in user.username.lower():
            role = "teacher"

    logger.info(f"User role determined: {role}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": role,
        },
        expires_delta=access_token_expires,
    )

    # Return format expected by frontend
    response_data = {
        "token": {
            "access_token": access_token,
            "token_type": "bearer"
        },
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "realname": user.full_name,
            "role": role
        }
    }

    logger.info("Login successful for user: %s, user_id=%s, role=%s", user.username, user.id, role)
    return response_data

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible login endpoint - for Swagger UI"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Determine role: first check user_profiles, then fallback
    role = "student"
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if user_profile:
        user_type = user_profile.user_type
        if hasattr(user_type, 'value'):
            user_type = user_type.value
        if user_type:
            role = user_type.lower()
    else:
        if user.is_superuser:
            role = "admin"
        elif user.username.startswith("student") or "student" in user.username.lower():
            role = "student"
        elif user.username.startswith("teacher") or "teacher" in user.username.lower():
            role = "teacher"

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": role,
        },
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """User logout endpoint"""
    # For JWT tokens, logout is handled client-side by removing the token
    # This endpoint can be used for logging or other cleanup tasks
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    password_data: dict,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    old_password = password_data.get("old_password", "")
    new_password = password_data.get("new_password", "")

    if not old_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both old_password and new_password are required"
        )

    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters"
        )

    user_id = current_user.get("user_id") if isinstance(current_user, dict) else current_user.id
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify old password
    try:
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.get("/user/profile")
async def get_user_profile(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    user_id = current_user.get("user_id") if isinstance(current_user, dict) else current_user.id
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "realname": user.full_name or "",
        "role": profile.user_type.lower() if profile else "student",
        "created_at": str(user.created_at) if user.created_at else "",
    }
