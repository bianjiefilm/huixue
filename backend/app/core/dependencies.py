"""
依赖注入模块。

所有 get_current_user 变体现在统一从 auth.py canonical 入口 re-export。
不要再在此文件中实现认证逻辑。
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, User, require_role

# 可选版本：直接 re-export get_current_user，调用方自行判断 id is None
get_current_user_optional = get_current_user

__all__ = ["get_db", "get_current_user", "User", "require_role", "get_current_user_optional"] 