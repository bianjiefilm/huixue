from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Union
import secrets
import logging

# 资源目录：优先使用 ziyuan_data（包含完整的课程和实训资源）
# 如果 ziyuan_data 不存在，则回退到 ziyuan
# __file__ = backend/app/core/config.py → parents[2] = backend/
_backend_dir = Path(__file__).resolve().parents[2]
_static_resources_dir = _backend_dir / "static" / "resources"
_ziyuan_data_dir = _backend_dir.parent / "ziyuan_data"
_ziyuan_dir = _backend_dir / "ziyuan"
# Prefer static/resources (primary), then ziyuan_data (legacy), then ziyuan (fallback)
if _static_resources_dir.exists():
    DEFAULT_RESOURCE_DIR = _static_resources_dir
elif _ziyuan_data_dir.exists():
    DEFAULT_RESOURCE_DIR = _ziyuan_data_dir
else:
    DEFAULT_RESOURCE_DIR = _ziyuan_dir


class Settings(BaseSettings):
    # Application Settings
    
    APP_NAME: str = "Huixue Education Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security Settings
    SECRET_KEY: str = Field(default="development_secret_key_fixed_for_testing_12345", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours for development/testing
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: str = Field(default="http://localhost:3000", env="BACKEND_CORS_ORIGINS")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
    
    # Database Settings - 统一使用PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql://huixue:huixue123@localhost:5432/huixue",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Environment Control Settings
    ALLOW_MULTIPLE_ENVIRONMENTS: bool = Field(default=False, env="ALLOW_MULTIPLE_ENVIRONMENTS")  # 是否允许同时开启多个实验环境
    
    # Redis Settings (for caching and data consistency)
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = None
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    API_BASE_URL: str = Field(default="http://localhost:8000", env="API_BASE_URL")
    SERVER_HOST: str = Field(default="localhost", env="SERVER_HOST")
    SERVER_PORT: int = Field(default=8000, env="SERVER_PORT")
    
    # Static Files
    STATIC_FILES_PATH: str = "static"
    RESOURCE_BASE_DIR: str = Field(default=str(DEFAULT_RESOURCE_DIR), env="HUIXUE_RESOURCE_DIR")
    RESOURCE_STAGING_DIR: str = "ziyuan/staging"  # 资源同步暂存目录
    RESOURCE_PRODUCTION_DIR: str = "ziyuan/production"  # 资源生产环境目录
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".txt", ".png", ".jpg", ".jpeg"]
    
    # Security Headers
    SECURE_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # AI 功能总开关：默认关闭，需要时在部署环境 .env 设 AI_FEATURES_ENABLED=true 并重启
    AI_FEATURES_ENABLED: bool = Field(default=False, env="AI_FEATURES_ENABLED")

    ARK_API_KEY: Optional[str] = Field(default=None, env="ARK_API_KEY")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Docker Settings
    DOCKER_HOST: str = Field(default="unix:///var/run/docker.sock", env="DOCKER_HOST")
    DOCKER_NETWORK: str = Field(default="bridge", env="DOCKER_NETWORK")
    DOCKER_PORT_RANGE_START: int = Field(default=30000, env="DOCKER_PORT_RANGE_START")
    DOCKER_PORT_RANGE_END: int = Field(default=30100, env="DOCKER_PORT_RANGE_END")
    CONTAINER_TIMEOUT_HOURS: int = Field(default=2, env="CONTAINER_TIMEOUT_HOURS")
    
    # Jupyter Settings
    JUPYTER_BASE_URL: str = Field(default="http://<慧学服务器1-IP>", env="JUPYTER_BASE_URL")
    JUPYTER_TOKEN: str = Field(default="dev_token", env="JUPYTER_TOKEN")
    
    # Container Storage Paths
    CONTAINER_STUDENT_WORK_BASE: str = Field(default="./student_work", env="CONTAINER_STUDENT_WORK_BASE")
    BI_PARENT_ORIGIN: str = Field(default="http://localhost:3000", env="BI_PARENT_ORIGIN")

    # HDFS Persistence Settings
    HDFS_ENABLED: bool = Field(default=False, env="HDFS_ENABLED")
    HDFS_HOST: str = Field(default="localhost", env="HDFS_HOST")
    HDFS_PORT: int = Field(default=9000, env="HDFS_PORT")
    HDFS_WEBHDFS_PORT: int = Field(default=50070, env="HDFS_WEBHDFS_PORT")
    HDFS_USER: str = Field(default="hadoop", env="HDFS_USER")
    HDFS_BASE_PATH: str = Field(default="/huixue/student_data", env="HDFS_BASE_PATH")
    HDFS_LOCAL_CACHE_DIR: str = Field(default="./hdfs_cache", env="HDFS_LOCAL_CACHE_DIR")
    HDFS_SYNC_ON_STOP: bool = Field(default=True, env="HDFS_SYNC_ON_STOP")  # 容器停止时同步到HDFS
    BI_PROXY_ENABLED: bool = Field(default=True, env="BI_PROXY_ENABLED")
    SUPERSET_CONFIG_PATH: Optional[str] = Field(default=None, env="SUPERSET_CONFIG_PATH")
    SUPERSET_EMBED_SECRET: str = Field(default="superset-embed-secret", env="SUPERSET_EMBED_SECRET")
    SUPERSET_EMBED_USERNAME: str = Field(default="admin", env="SUPERSET_EMBED_USERNAME")
    SUPERSET_EMBED_PASSWORD: str = Field(default="admin", env="SUPERSET_EMBED_PASSWORD")
    SUPERSET_EMBED_EMAIL: str = Field(default="embed@example.com", env="SUPERSET_EMBED_EMAIL")
    SUPERSET_EMBED_FIRSTNAME: str = Field(default="Embed", env="SUPERSET_EMBED_FIRSTNAME")
    SUPERSET_EMBED_LASTNAME: str = Field(default="Service", env="SUPERSET_EMBED_LASTNAME")
    SUPERSET_GUEST_ROLE: str = Field(default="Gamma", env="SUPERSET_GUEST_ROLE")
    SUPERSET_EMBED_DASHBOARD_ID: str = Field(default="1", env="SUPERSET_EMBED_DASHBOARD_ID")

    @property
    def resource_base_path(self) -> Path:
        return Path(self.RESOURCE_BASE_DIR).expanduser().resolve()
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


# Create global settings instance
settings = Settings()


# Validate critical settings on startup
def validate_settings():
    """Validate critical settings to ensure security"""
    if settings.SECRET_KEY == "your-secret-key-here-change-in-production":
        raise ValueError(
            "CRITICAL: Default SECRET_KEY detected! "
            "Please set a secure SECRET_KEY in your .env file"
        )
    
    if not settings.cors_origins_list and not settings.DEBUG:
        raise ValueError(
            "CRITICAL: No CORS origins configured for production! "
            "Please set BACKEND_CORS_ORIGINS in your .env file"
        )
    
    if "sqlite" in settings.DATABASE_URL and not settings.DEBUG:
        print(
            "WARNING: SQLite detected in production mode. "
            "Consider using PostgreSQL for better performance and concurrency."
        )