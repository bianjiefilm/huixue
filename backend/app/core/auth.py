"""
认证工具：JWT token 解析（canonical 入口）。

本模块是所有端点的统一认证入口。提供：
- get_current_user()      — 解析 JWT，返回 User 对象（无 token 时降级）
- require_role()          — 装饰器，要求指定角色之一
- verify_token_payload() — canonical token 解码底层函数

其他 auth 模块（security.py, permissions.py, dependencies.py）
统一 re-export 本模块，不再各自实现。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional, Callable
from functools import wraps
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User as _DbUser
from sqlalchemy import text
from sqlalchemy.orm import Session

# JWT 配置（与 security.py / permissions.py 保持一致）
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

security = HTTPBearer(auto_error=False)


class User:
    """简化用户对象，仅含 id / username / role。"""

    def __init__(self, id: Optional[int], username: str, role: str = "student"):
        self.id = id
        self.username = username
        self.role = role


def verify_token_payload(token: str, db: "Session" = None) -> dict:
    """
    Canonical token 解码。供所有 get_current_user 变体调用。

    - 解码失败 → raise JWTError
    - token 无身份（既无 user_id 又无 sub/username） → raise JWTError
    - 只有 sub 无 user_id → 从 DB 反查真实 user_id

    Args:
        token: JWT 字符串
        db: 可选数据库会话（用于 sub→user_id 反查）

    Returns: {"user_id": int, "username": str, "role": str}
    Raises JWTError: token 无效或无身份
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: Optional[int] = payload.get("user_id")
    username: str = payload.get("sub") or payload.get("username") or ""

    # 新增: 拒绝无身份的 token
    if user_id is None and not username:
        raise JWTError("Token missing both user_id and sub/username")

    # 新增: 如果只有 username 没 user_id，从 DB 反查
    if user_id is None and username and db is not None:
        tbl = _DbUser.__table__.name
        row = db.execute(text(f"SELECT id FROM {tbl} WHERE username = :username"), {"username": username}).fetchone()
        if row is None:
            raise JWTError(f"Token sub '{username}' does not match any user")
        user_id = row[0]

    return {
        "user_id": user_id,
        "username": username or "unknown",
        "role": payload.get("role") or "student",
    }


def get_current_user(
    credentials = Depends(security),
    db: "Session" = Depends(get_db),
) -> User:
    """
    解析 JWT Bearer token，返回 User 对象。

    - token 缺失或无效 → 返回匿名用户 (id=None, role=student)
      这样既不破坏向后兼容，也不让恶意 query param 绕过真实身份。
    - token 有效 → 从 payload 中提取 user_id / sub / role
    """
    if credentials is None:
        return User(id=None, username="anonymous", role="student")

    try:
        data = verify_token_payload(credentials.credentials, db=db)
        return User(id=data["user_id"], username=data["username"], role=data["role"])
    except JWTError:
        # token 无效 → 降级为匿名用户（不要 401，让端点自行决定权限）
        return User(id=None, username="anonymous", role="student")


def require_role(*allowed_roles: str):
    """
    角色检查依赖工厂。返回 FastAPI Depends-compatible 的依赖函数。

    用法（两种写法等效）：

    写法 A — 显式参数：
        @router.post("/admin-only")
        def admin_endpoint(
            current_user: User = Depends(get_current_user),
            _: None = Depends(require_role("admin")),
        ):
            ...

    写法 B — 装饰器风格：
        @router.post("/admin-only")
        @require_role("admin", "teacher")
        def admin_endpoint(current_user: User = Depends(get_current_user)):
            ...

    如果用户角色不在允许列表，返回 403 Forbidden。
    """
    from fastapi import HTTPException, status

    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要角色 {allowed_roles}，当前角色为 {current_user.role}",
            )
        return None  # 不替换 current_user，只做检查

    return role_checker


# ==================== 给 security.py / permissions.py 用的兼容别名 ====================
# 这两个模块内部已有自己的实现，此处不覆盖，只导出供依赖它们的地方使用
__all__ = ["User", "get_current_user", "verify_token_payload", "require_role", "security"]

