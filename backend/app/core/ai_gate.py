"""AI 功能总开关。

所有 AI 类路由(ai_assistant / ai_features / text_explain / generation)
共用此 dependency。关闭时动作类接口统一返回 403 + code=AI_DISABLED,
前端拦截器据此静默处理,不弹全局错误提示。
"""

from fastapi import HTTPException, status

from app.core.config import settings

AI_DISABLED_DETAIL = {"code": "AI_DISABLED", "message": "AI 功能当前未开放"}


def require_ai_enabled() -> None:
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AI_DISABLED_DETAIL)
