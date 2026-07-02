"""
Pure error response factory functions.

All functions here are side-effect-free: no logging, no DB, no I/O.
They produce dicts/models suitable for FastAPI JSON responses.
"""
from typing import Optional, Dict, Any


# ==================== Error codes ====================

ERROR_CODES = {
    "SUCCESS": "0000",
    "VALIDATION": "4000",
    "UNAUTHORIZED": "4001",
    "FORBIDDEN": "4003",
    "NOT_FOUND": "4004",
    "CONFLICT": "4009",
    "INTERNAL": "5000",
}


# ==================== Factory functions ====================

def success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    """Build a success response dict."""
    return {"code": ERROR_CODES["SUCCESS"], "message": message, "data": data}


def error_response(
    code: str,
    message: str,
    data: Any = None,
) -> Dict[str, Any]:
    """Build an error response dict."""
    return {"code": code, "message": message, "data": data}


def not_found_response(entity: str = "资源", entity_id: Any = None) -> Dict[str, Any]:
    """404-style response."""
    msg = f"{entity}不存在" if entity_id is None else f"{entity} {entity_id} 不存在"
    return error_response(ERROR_CODES["NOT_FOUND"], msg)


def validation_error_response(message: str, details: Optional[Dict] = None) -> Dict[str, Any]:
    """Validation failure response."""
    return error_response(ERROR_CODES["VALIDATION"], message, data=details)


def internal_error_response(message: str = "服务器内部错误") -> Dict[str, Any]:
    """Generic 500 response."""
    return error_response(ERROR_CODES["INTERNAL"], message)


# ==================== Pagination helpers ====================

def paginate_meta(total: int, page: int, page_size: int) -> Dict[str, int]:
    """Build standard pagination metadata."""
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    }
