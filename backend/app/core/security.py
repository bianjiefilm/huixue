from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
from app.core.config import settings

# 统一：使用 auth.py 的 canonical token decoder
from app.core.auth import verify_token_payload, User as AuthUser

# Security configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing - use pbkdf2
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """Verify a JWT token — delegates to canonical auth.py decoder."""
    try:
        data = verify_token_payload(token)
        return {"user_id": data["user_id"], "username": data["username"], "role": data["role"]}
    except JWTError as e:
        print(f"Token validation error: {e}")
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token验证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    
    user = None
    if token_data.get("user_id"):
        user = db.query(User).filter(User.id == token_data["user_id"]).first()
    elif token_data.get("username"):
        user = db.query(User).filter(User.username == token_data["username"]).first()
        
    if user is None:
        raise credentials_exception
        
    # Add role to user object for convenience if not present (optional)
    if not hasattr(user, "role_name") and token_data.get("role"):
        user.role_name = token_data["role"]
        
    return {"id": user.id, "user_id": user.id, "username": user.username, "email": user.email, "roles": [token_data.get("role", "student")], "is_superuser": user.is_superuser, "is_active": user.is_active}

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get the current active user"""
    # BUG-004 fix: get_current_user returns a dict, use dict-key access
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user