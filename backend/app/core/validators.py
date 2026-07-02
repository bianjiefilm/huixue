"""
Input validation utilities and common validators
"""
from typing import Optional, List
from pydantic import BaseModel, validator, constr, conint
import re
from datetime import datetime


# Common string constraints
SafeString = constr(strip_whitespace=True, min_length=1, max_length=255)
SafeText = constr(strip_whitespace=True, min_length=1, max_length=5000)
Username = constr(pattern=r'^[a-zA-Z0-9_-]{3,50}$', strip_whitespace=True)
Email = constr(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$', strip_whitespace=True)
PhoneNumber = constr(pattern=r'^1[3-9]\d{9}$', strip_whitespace=True)

# Common integer constraints  
PositiveInt = conint(gt=0)
NonNegativeInt = conint(ge=0)
PageSize = conint(ge=1, le=100)
PageNumber = conint(ge=1)


class PaginationParams(BaseModel):
    """Common pagination parameters"""
    page: PageNumber = 1
    page_size: PageSize = 20
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class SearchParams(BaseModel):
    """Common search parameters"""
    q: Optional[SafeString] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be either "asc" or "desc"')
        return v


class DateRangeParams(BaseModel):
    """Date range parameters for filtering"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML tags"""
    if not text:
        return text
    
    # Remove script tags and their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove style tags and their content
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove iframe tags
    text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    text = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    
    return text


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension against allowed list"""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return f".{ext}" in allowed_extensions


def validate_sql_identifier(identifier: str) -> bool:
    """Validate SQL identifier to prevent injection"""
    if not identifier:
        return False
    
    # Only allow alphanumeric, underscore
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', identifier))


class BaseResponseModel(BaseModel):
    """Base model for API responses"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }


class ErrorResponseModel(BaseModel):
    """Model for error responses"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "An error occurred",
                "error_code": "VALIDATION_ERROR",
                "details": {"field": "username", "error": "Username already exists"}
            }
        }