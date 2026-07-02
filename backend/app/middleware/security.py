"""
Security middleware for adding security headers and other protections
"""
from fastapi import Request
from fastapi.responses import Response
from app.core.config import settings
import time
from collections import defaultdict
from datetime import datetime, timedelta


class SecurityMiddleware:
    """Add security headers to all responses"""
    
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in settings.SECURE_HEADERS.items():
            response.headers[header] = value
        
        # Remove server header
        response.headers.pop("server", None)
        
        return response


class RateLimitMiddleware:
    """Simple rate limiting middleware"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_PERIOD
    
    async def __call__(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        now = datetime.now()
        
        # Clean old requests
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now + timedelta(seconds=self.window_seconds)).timestamp()))
                }
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(seconds=self.window_seconds)).timestamp()))
        
        return response


class RequestValidationMiddleware:
    """Validate request size and content"""
    
    async def __call__(self, request: Request, call_next):
        # Check content length for file uploads
        if request.url.path.startswith("/api/v1/files/upload"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.UPLOAD_MAX_SIZE:
                return Response(
                    content=f"File too large. Maximum size is {settings.UPLOAD_MAX_SIZE} bytes",
                    status_code=413
                )
        
        return await call_next(request)