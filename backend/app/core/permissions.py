"""
增强权限控制系统
提供JWT Token验证、操作审计和敏感操作二次验证
"""
import sys
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps

# 全局标志，跟踪函数是否被调用
_AUTH_CALLED_FLAG = False

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User
from app.core.cache import get_cache
from app.core.two_factor import get_two_factor_auth
from app.core.auth import verify_token_payload  # canonical token decoder

logger = logging.getLogger(__name__)

# 写入标志文件
with open("/tmp/auth_flag.txt", "w") as f:
    f.write(f"Module loaded at {datetime.now()}\n")

# JWT配置
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'your-secret-key-here-change-in-production')
ALGORITHM = getattr(settings, 'ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)

# 安全Bearer token scheme
security = HTTPBearer()

# 用户角色
class Role:
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

# 操作权限级别
class OperationLevel:
    READ = "read"      # 只读操作
    WRITE = "write"    # 写操作
    ADMIN = "admin"    # 管理员操作

# 敏感操作类型
class SensitiveOperation:
    PUBLISH_PUBLIC = "publish_public"    # 公开发布
    DELETE_PRACTICE = "delete_practice"  # 删除实践
    ADMIN_OVERRIDE = "admin_override"    # 管理员覆盖

class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self.cache = get_cache()
        self.audit_logger = logging.getLogger("audit")
        self.two_factor = get_two_factor_auth()

    def verify_jwt_token(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """
        验证JWT Token并返回用户信息。
        使用 auth.py 的 canonical decoder，但保留 expiration 检查等权限特有逻辑。
        """
        try:
            payload = jwt.decode(
                credentials.credentials,
                SECRET_KEY,
                algorithms=[ALGORITHM],
            )
            username: str = payload.get("sub")
            role: str = payload.get("role", "user")

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token无效",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 检查 token 是否过期（permissions.py 特有逻辑）
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token已过期",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return {
                "username": username,
                "role": role,
                "token_payload": payload,
            }

        except JWTError as e:
            logger.error(f"JWT验证失败: {str(e)}, token: {credentials.credentials[:50] if credentials.credentials else 'None'}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token验证失败: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token验证异常: {str(e)}, type: {type(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token验证异常: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def verify_operation_permission(
        self,
        user_info: Dict[str, Any],
        operation: str,
        resource_id: Optional[int] = None,
        resource_type: str = "practice",
        db: Session = None
    ) -> bool:
        """
        验证用户是否有权限执行特定操作

        Args:
            user_info: 用户信息
            operation: 操作类型
            resource_id: 资源ID
            resource_type: 资源类型
            db: 数据库会话

        Returns:
            bool: 是否有权限
        """
        user_id = user_info["user_id"]
        role = user_info["role"]

        # 管理员有所有权限
        if role == "admin" or user_info.get("is_superuser", False):
            return True

        # 根据操作类型检查权限
        if resource_type == "practice":
            return self._check_practice_permission(user_id, operation, resource_id, db)

        return False

    def _check_practice_permission(
        self,
        user_id: int,
        operation: str,
        practice_id: Optional[int],
        db: Session
    ) -> bool:
        """
        检查实践操作权限

        Args:
            user_id: 用户ID
            operation: 操作类型
            practice_id: 实践ID
            db: 数据库会话

        Returns:
            bool: 是否有权限
        """
        if not practice_id:
            # 创建操作，所有登录用户都可以
            return operation in ["create"]

        # 查询实践所有权
        from app.models.models import Practice
        practice = db.query(Practice).filter(Practice.id == practice_id).first()

        if not practice:
            return False

        # 所有者有所有权限
        if practice.creator_id == user_id:
            return True

        # 其他用户只能查看已发布的公开实践
        if operation in ["read", "view"]:
            return practice.publish_status == "published" and practice.visibility == "public"

        return False

    def send_two_factor_code(self, user_info: Dict[str, Any], method: str = "totp") -> tuple:
        """
        发送二次验证验证码

        Args:
            user_info: 用户信息
            method: 验证方式 (totp/sms/email)

        Returns:
            tuple: (是否成功, 验证码/错误信息)
        """
        try:
            user_id = user_info["user_id"]

            if method == "totp":
                # 生成TOTP密钥（在实际应用中应该从数据库获取已保存的密钥）
                secret = self.two_factor.generate_totp_secret(user_id)
                code = self.two_factor.generate_totp_code(secret)
                return True, code

            elif method == "sms":
                # 从用户信息中获取手机号
                phone = user_info.get("phone")
                if not phone:
                    return False, "用户未绑定手机号"

                code = f"{secrets.randbelow(900000) + 100000:06d}"  # 6位随机数
                success = self.two_factor.send_sms_code(phone, code)
                return success, code if success else "发送失败"

            elif method == "email":
                # 从用户信息中获取邮箱
                email = user_info.get("email")
                if not email:
                    return False, "用户未绑定邮箱"

                code = f"{secrets.randbelow(900000) + 100000:06d}"  # 6位随机数
                success = self.two_factor.send_email_code(email, code)
                return success, code if success else "发送失败"

            else:
                return False, f"不支持的验证方式: {method}"

        except Exception as e:
            logger.error(f"发送二次验证验证码失败: {e}")
            return False, str(e)

    def verify_two_factor_code(self, user_info: Dict[str, Any], code: str, method: str = "totp") -> bool:
        """
        验证二次验证验证码

        Args:
            user_info: 用户信息
            code: 验证码
            method: 验证方式

        Returns:
            bool: 验证码是否有效
        """
        try:
            user_id = user_info["user_id"]

            if method == "totp":
                # 使用用户ID生成相同的密钥进行验证
                secret = self.two_factor.generate_totp_secret(user_id)
                return self.two_factor.verify_totp_code(secret, code)

            elif method in ["sms", "email"]:
                # 对于短信和邮件，验证码存储在缓存中
                cache_key = f"2fa:{user_id}:{method}"
                stored_code = self.cache.redis_client.get(cache_key)

                if stored_code and stored_code.decode() == code:
                    # 验证成功后删除验证码
                    self.cache.redis_client.delete(cache_key)
                    return True

                return False

            return False

        except Exception as e:
            logger.error(f"验证二次验证验证码失败: {e}")
            return False

    def log_operation(
        self,
        user_info: Dict[str, Any],
        operation: str,
        resource_type: str,
        resource_id: Optional[int],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        记录操作审计日志

        Args:
            user_info: 用户信息
            operation: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            action: 具体动作
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            success: 操作是否成功
            error_message: 错误信息
            db: 数据库会话（如果提供则写入数据库）
        """
        import json
        from app.models.models import AuditLog

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_info["user_id"],
            "username": user_info["username"],
            "role": user_info["role"],
            "operation": operation,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "details": json.dumps(details or {}, ensure_ascii=False),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "error_message": error_message
        }

        # 记录审计日志
        log_message = f"AUDIT: {audit_entry}"
        if success:
            self.audit_logger.info(log_message)
        else:
            self.audit_logger.warning(log_message)

        # 如果提供了数据库会话，写入数据库
        if db:
            try:
                audit_log = AuditLog(
                    user_id=user_info["user_id"],
                    username=user_info["username"],
                    role=user_info["role"],
                    operation=operation,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    details=json.dumps(details or {}, ensure_ascii=False),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    error_message=error_message
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                logger.error(f"写入审计日志到数据库失败: {e}")
                # 回滚以避免影响主事务
                try:
                    db.rollback()
                except:
                    pass

        # 存储到缓存用于快速查询（可选）
        self._cache_audit_entry(audit_entry)

    def _cache_audit_entry(self, entry: Dict[str, Any]):
        """缓存审计日志条目"""
        try:
            cache_key = f"audit:{entry['user_id']}:{int(time.time())}"
            self.cache.redis_client.setex(cache_key, 3600, str(entry))  # 1小时过期
        except Exception:
            pass  # 缓存失败不影响主流程

    def check_rate_limit(
        self,
        user_id: int,
        operation: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        检查操作频率限制

        Args:
            user_id: 用户ID
            operation: 操作类型
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            bool: 是否允许操作
        """
        try:
            cache_key = f"rate_limit:{user_id}:{operation}"
            current_count = int(self.cache.redis_client.get(cache_key) or 0)

            if current_count >= max_requests:
                return False

            # 增加计数
            self.cache.redis_client.setex(cache_key, window_seconds, current_count + 1)
            return True

        except Exception:
            # Redis不可用时允许操作
            return True

    def require_two_factor(
        self,
        operation: str,
        user_info: Dict[str, Any]
    ) -> bool:
        """
        检查是否需要二次验证

        Args:
            operation: 操作类型
            user_info: 用户信息

        Returns:
            bool: 是否需要二次验证
        """
        # 敏感操作需要二次验证
        sensitive_ops = [
            SensitiveOperation.PUBLISH_PUBLIC,
            SensitiveOperation.DELETE_PRACTICE,
            SensitiveOperation.ADMIN_OVERRIDE
        ]

        return operation in sensitive_ops

# 权限类（向后兼容）
class Permission:
    """权限类"""
    pass

# 权限检查器类（向后兼容）
class PermissionChecker:
    """权限检查器"""
    pass

# 全局权限管理器实例
permission_manager = PermissionManager()

def get_permission_manager() -> PermissionManager:
    """获取权限管理器实例"""
    return permission_manager

# 装饰器：需要认证
def require_auth(operation_level: str = OperationLevel.READ):
    """
    认证装饰器

    Args:
        operation_level: 操作级别
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中提取request对象
            request = kwargs.get('request')
            if not request:
                # 尝试从args中查找Request对象
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法获取请求对象"
                )

            # 验证JWT Token
            try:
                credentials = await security(request)
                user_info = permission_manager.verify_jwt_token(credentials)
            except Exception as e:
                logger.warning(f"Token验证失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="认证失败",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 检查频率限制
            if not permission_manager.check_rate_limit(
                user_info["user_id"],
                operation_level,
                max_requests=100 if operation_level == OperationLevel.READ else 20
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁，请稍后再试"
                )

            # 将用户信息添加到kwargs
            kwargs['user_info'] = user_info
            kwargs['request'] = request

            return await func(*args, **kwargs)

        return wrapper
    return decorator

# 依赖注入：获取当前用户信息
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取当前用户信息（依赖注入方式）
    """
    global _AUTH_CALLED_FLAG
    _AUTH_CALLED_FLAG = True

    # 写入调用标志
    try:
        with open("/tmp/auth_called.txt", "w") as f:
            f.write(f"PID={os.getpid()} called at {datetime.now()}\n")
    except Exception:
        pass

    # 直接写入stderr，确保能被看到
    sys.stderr.write(f"[CRITICAL] get_current_user() CALLED! PID={os.getpid()}\n")
    sys.stderr.flush()

    from app.core.config import settings as runtime_settings
    sys.stderr.write(f"[AUTH_DEBUG] SECRET_KEY (Global): {SECRET_KEY[:20]}...\n")
    sys.stderr.write(f"[AUTH_DEBUG] SECRET_KEY (Runtime): {runtime_settings.SECRET_KEY[:20]}...\n")
    sys.stderr.flush()

    token_val = credentials.credentials if credentials and hasattr(credentials, 'credentials') else "NONE"
    sys.stderr.write(f"[AUTH_DEBUG] Token Received: {token_val[:30]}... (len: {len(token_val)})\n")
    sys.stderr.flush()

    user_info = permission_manager.verify_jwt_token(credentials)
    sys.stderr.write(f"[AUTH_DEBUG] After verify_jwt_token: {user_info}\n")
    sys.stderr.flush()

    # 从数据库获取完整的用户信息
    user = db.query(User).filter(User.username == user_info["username"]).first()
    sys.stderr.write(f"[AUTH_DEBUG] Database query result: user={user}\n")
    sys.stderr.flush()
    if not user:
        sys.stderr.write(f"[AUTH_DEBUG] User not found for username: {user_info['username']}\n")
        sys.stderr.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    sys.stderr.write(f"[AUTH_DEBUG] Before update - user.id: {user.id}, user.superuser: {user.is_superuser}\n")
    sys.stderr.flush()
    update_data = {
        "user_id": user.id,
        "id": str(user.id),  # 添加字符串类型的id以兼容前端
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        # 角色优先级: 超级用户 → admin; 否则保留 JWT 中的 role（teacher/student/admin），
        # 若 JWT 未指定则退回 "user"。修复前此处恒将非超级用户覆盖为 "user"，
        # 导致教师创建实训等接口的角色校验全部失效。
        "role": "admin" if user.is_superuser else (user_info.get("role") or "user"),
        "is_superuser": user.is_superuser,
        "created_at": user.created_at
    }
    sys.stderr.write(f"[AUTH_DEBUG] Update data: {update_data}\n")
    sys.stderr.flush()
    user_info.update(update_data)
    sys.stderr.write(f"[AUTH_DEBUG] Final user_id: {user_info.get('user_id')}\n")
    sys.stderr.flush()
    return user_info

# 依赖注入：验证操作权限
def require_permission(operation: str, resource_type: str = "practice"):
    """
    权限验证依赖注入

    Args:
        operation: 操作类型
        resource_type: 资源类型
    """
    def dependency(
        user_info: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db),
        resource_id: Optional[int] = None
    ) -> Dict[str, Any]:
        if not permission_manager.verify_operation_permission(
            user_info, operation, resource_id, resource_type, db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

        # 记录操作日志
        permission_manager.log_operation(
            user_info=user_info,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            action="access",
            details={"permission_check": True}
        )

        return user_info

    return Depends(dependency)