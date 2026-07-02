"""
JWT 身份提取与归属校验的统一工具。

历史上多个端点文件各自信任客户端传入的 teacher_id/student_id/creator_id 等
query/body 参数来决定数据归属范围, 未与 JWT 中的真实身份核对, 构成 IDOR
(越权访问)。本模块把 classrooms.py 中已验证有效的修复模式抽成公共函数,
供所有端点文件复用, 避免同一 bug 在不同文件里重复出现或修复不一致。
"""

from typing import Optional

from fastapi import HTTPException, status


def get_jwt_identity(current_user: dict) -> tuple[Optional[int], str]:
    """从 get_current_user() 依赖注入的结果中提取 (user_id, role)。"""
    if not current_user:
        return None, ""

    if isinstance(current_user, dict):
        user_id = current_user.get("user_id") or current_user.get("id")
        role = current_user.get("role")
        if not role:
            roles = current_user.get("roles") or []
            role = roles[0] if roles else None
        if current_user.get("is_superuser"):
            role = role or "admin"
    else:
        user_id = getattr(current_user, "id", None)
        role = getattr(current_user, "role", None)
        if getattr(current_user, "is_superuser", False):
            role = role or "admin"

    return user_id, (role or "").lower()


def require_authenticated(current_user: dict) -> tuple[int, str]:
    """要求已登录, 返回 (user_id, role); 未登录抛 401。"""
    user_id, role = get_jwt_identity(current_user)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")
    return user_id, role


def resolve_scoped_id(
    current_user: dict,
    requested_id: Optional[int],
    *,
    allowed_roles: tuple[str, ...] = ("teacher", "student"),
    admin_roles: tuple[str, ...] = ("admin",),
    forbidden_detail: str = "无权访问该资源",
) -> int:
    """
    把 "客户端可传 teacher_id/student_id 等归属参数" 的老接口统一收口:
    - admin 角色: 可以传任意 requested_id (若不传则退回自己的 id)
    - 在 allowed_roles 内的角色: 若传了 requested_id 且与自己不一致则 403;
      不传则默认使用自己的 id。
    - 其他角色: 403。

    返回值是"最终应使用的归属 id", 调用方后续查询一律使用这个值, 不要再直接
    使用客户端传入的原始参数。
    """
    user_id, role = require_authenticated(current_user)

    if role in admin_roles:
        return requested_id if requested_id is not None else user_id

    if role in allowed_roles:
        if requested_id is not None and requested_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=forbidden_detail)
        return user_id

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=forbidden_detail)


def require_owner_or_admin(
    current_user: dict,
    owner_id: Optional[int],
    *,
    admin_roles: tuple[str, ...] = ("admin",),
    forbidden_detail: str = "无权访问该资源",
) -> tuple[int, str]:
    """
    用于"已经从 DB 查出资源、需要校验调用者是否是资源所有者"的场景
    (例如已知 classroom.teacher_id, 需要确认当前用户就是这个老师或 admin)。
    返回 (user_id, role) 供调用方按角色做进一步分支(如 student 需查是否在场)。
    """
    user_id, role = require_authenticated(current_user)

    if role in admin_roles:
        return user_id, role

    if owner_id is not None and owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=forbidden_detail)

    return user_id, role
