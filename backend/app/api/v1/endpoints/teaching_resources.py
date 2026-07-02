"""
教学资源管理API端点
包含实践环境管理、实验资源监控等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
import psutil
import logging

from app.core.database import get_db
from app.schemas import schemas
from app.models.models import (
    PracticeEnvironmentConfig,
    SystemSetting,
    ContainerProcess as ContainerProcessModel,
    ServerNode,
    User
)
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id

logger = logging.getLogger(__name__)
router = APIRouter()

# 尝试导入docker，如果不可用则设置为None
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Docker操作线程池（限制并发）
docker_executor = ThreadPoolExecutor(max_workers=2)
DOCKER_TIMEOUT = 5  # Docker操作超时时间（秒）

try:
    import docker
    from app.core.config import settings
    # 支持远程Docker Host（当DOCKER_HOST配置为TCP时）
    if settings.DOCKER_HOST and not settings.DOCKER_HOST.startswith("unix://"):
        docker_client = docker.DockerClient(base_url=settings.DOCKER_HOST, timeout=DOCKER_TIMEOUT)
        logger.info(f"Docker远程连接: {settings.DOCKER_HOST}")
    else:
        docker_client = docker.from_env(timeout=DOCKER_TIMEOUT)
    DOCKER_AVAILABLE = True
    logger.info("Docker集成已启用")
except HTTPException:
    raise
except Exception as e:
    logger.warning(f"Docker不可用: {e}")
    docker_client = None
    DOCKER_AVAILABLE = False


def safe_docker_call(func, *args, default=None, timeout=DOCKER_TIMEOUT, **kwargs):
    """安全的Docker调用，带超时保护"""
    if not DOCKER_AVAILABLE or docker_client is None:
        return default
    try:
        future = docker_executor.submit(func, *args, **kwargs)
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        logger.warning(f"Docker调用超时: {func.__name__}")
        return default
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Docker调用失败: {func.__name__} - {e}")
        return default


# ==================== 数据模型 ====================

class ResourceRange(BaseModel):
    min: int
    max: int
    default: int


class EnvironmentConfigResponse(BaseModel):
    id: str
    name: str
    type: str  # 'normal', 'jupyter', 'desktop'
    storage: ResourceRange
    memory: ResourceRange
    cpu: ResourceRange
    docker_image: Optional[str] = None
    docker_port: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class EnvironmentConfigCreate(BaseModel):
    name: str
    type: str = "normal"
    storage: ResourceRange
    memory: ResourceRange
    cpu: ResourceRange
    docker_image: Optional[str] = None
    docker_port: int = 8888
    description: Optional[str] = None


class EnvironmentConfigUpdate(BaseModel):
    storage: Optional[ResourceRange] = None
    memory: Optional[ResourceRange] = None
    cpu: Optional[ResourceRange] = None
    docker_image: Optional[str] = None
    docker_port: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PaginatedEnvironmentResponse(BaseModel):
    items: List[EnvironmentConfigResponse]
    total: int
    page: int
    page_size: int


class ServerNodeInfo(BaseModel):
    id: str
    name: str
    type: str  # 'application' or 'compute'
    status: str  # 'online', 'offline', 'busy'
    cpu_usage: float
    memory_usage: float
    memory_total: int
    disk_usage: float
    disk_total: int
    container_count: int


class ServerNodesOverview(BaseModel):
    application_servers: List[ServerNodeInfo]
    compute_servers: List[ServerNodeInfo]


class ContainerProcess(BaseModel):
    id: str
    user_name: str
    user_id: str
    course_name: str
    environment_type: str
    start_time: str
    running_time: int  # 运行时长（秒）
    cpu_usage: float
    memory_usage: float
    memory_limit: float  # 内存限制（MB）
    status: str  # 'running', 'stopped', 'paused'


class PaginatedContainerResponse(BaseModel):
    items: List[ContainerProcess]
    total: int


class ConcurrentExperimentSetting(BaseModel):
    enabled: bool


# ==================== 辅助函数 ====================

def db_config_to_response(config: PracticeEnvironmentConfig) -> EnvironmentConfigResponse:
    """将数据库模型转换为响应模型"""
    return EnvironmentConfigResponse(
        id=str(config.id),
        name=config.name,
        type=str(config.environment_type) if config.environment_type else "normal",
        storage=ResourceRange(
            min=config.storage_min or 256,
            max=config.storage_max or 2048,
            default=config.storage_default or 512
        ),
        memory=ResourceRange(
            min=config.memory_min or 128,
            max=config.memory_max or 1024,
            default=config.memory_default or 256
        ),
        cpu=ResourceRange(
            min=config.cpu_min or 1,
            max=config.cpu_max or 4,
            default=config.cpu_default or 1
        ),
        docker_image=config.docker_image,
        docker_port=config.docker_port or 8888,
        description=config.description,
        is_active=config.is_active if config.is_active is not None else True
    )


def get_system_resources() -> ServerNodeInfo:
    """获取当前系统的资源使用情况"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 获取运行中的容器数量（使用安全调用）
    container_count = 0
    if DOCKER_AVAILABLE and docker_client:
        containers = safe_docker_call(docker_client.containers.list, default=[])
        container_count = len(containers) if containers else 0
    
    return ServerNodeInfo(
        id="local-server",
        name="本地服务器",
        type="application",
        status="online",
        cpu_usage=round(cpu_percent, 1),
        memory_usage=round(memory.percent, 1),
        memory_total=memory.total // (1024 * 1024),  # 转换为MB
        disk_usage=round(disk.percent, 1),
        disk_total=disk.total // (1024 * 1024 * 1024),  # 转换为GB
        container_count=container_count
    )


def init_default_environments(db: Session):
    """初始化默认环境配置（如果不存在）"""
    default_configs = [
        {
            "name": "Jupyter Python",
            "environment_type": "jupyter",
            "storage_min": 512, "storage_max": 4096, "storage_default": 1024,
            "memory_min": 256, "memory_max": 2048, "memory_default": 512,
            "cpu_min": 1, "cpu_max": 4, "cpu_default": 1,
            "docker_image": "jupyter/datascience-notebook:latest",
            "docker_port": 8888,
            "description": "Python数据科学Jupyter环境"
        },
        {
            "name": "Jupyter R",
            "environment_type": "jupyter",
            "storage_min": 512, "storage_max": 4096, "storage_default": 1024,
            "memory_min": 256, "memory_max": 2048, "memory_default": 512,
            "cpu_min": 1, "cpu_max": 4, "cpu_default": 1,
            "docker_image": "jupyter/r-notebook:latest",
            "docker_port": 8888,
            "description": "R语言Jupyter环境"
        },
        {
            "name": "Ubuntu云桌面",
            "environment_type": "desktop",
            "storage_min": 1024, "storage_max": 8192, "storage_default": 2048,
            "memory_min": 512, "memory_max": 4096, "memory_default": 1024,
            "cpu_min": 1, "cpu_max": 8, "cpu_default": 2,
            "docker_image": "consol/ubuntu-xfce-vnc:latest",
            "docker_port": 6901,
            "description": "Ubuntu图形化云桌面环境"
        },
        {
            "name": "Python基础环境",
            "environment_type": "normal",
            "storage_min": 256, "storage_max": 2048, "storage_default": 512,
            "memory_min": 128, "memory_max": 1024, "memory_default": 256,
            "cpu_min": 1, "cpu_max": 2, "cpu_default": 1,
            "docker_image": "python:3.11-slim",
            "docker_port": 8000,
            "description": "轻量级Python运行环境"
        },
        {
            "name": "Java开发环境",
            "environment_type": "normal",
            "storage_min": 512, "storage_max": 4096, "storage_default": 1024,
            "memory_min": 256, "memory_max": 2048, "memory_default": 512,
            "cpu_min": 1, "cpu_max": 4, "cpu_default": 2,
            "docker_image": "openjdk:17-slim",
            "docker_port": 8080,
            "description": "Java 17开发环境"
        }
    ]
    
    for config_data in default_configs:
        existing = db.query(PracticeEnvironmentConfig).filter(
            PracticeEnvironmentConfig.name == config_data["name"]
        ).first()
        
        if not existing:
            config = PracticeEnvironmentConfig(**config_data)
            db.add(config)
    
    db.commit()


def init_default_settings(db: Session):
    """初始化默认系统设置（如果不存在）"""
    default_settings = [
        {
            "key": "concurrent_experiment_enabled",
            "value": "false",
            "value_type": "bool",
            "description": "是否允许同时开启多个实验",
            "category": "experiment"
        },
        {
            "key": "container_timeout_hours",
            "value": "2",
            "value_type": "int",
            "description": "容器自动超时时间（小时）",
            "category": "experiment"
        },
        {
            "key": "max_containers_per_user",
            "value": "1",
            "value_type": "int",
            "description": "每个用户最大容器数",
            "category": "experiment"
        }
    ]
    
    for setting_data in default_settings:
        existing = db.query(SystemSetting).filter(
            SystemSetting.key == setting_data["key"]
        ).first()
        
        if not existing:
            setting = SystemSetting(**setting_data)
            db.add(setting)
    
    db.commit()


# ==================== API端点 ====================

@router.get("/practice-environments", response_model=schemas.ApiResponse)
async def get_practice_environments(
    environment_type: Optional[str] = Query(None, description="环境类型"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取实践环境列表"""
    # 初始化默认配置
    init_default_environments(db)
    
    # 构建查询
    query = db.query(PracticeEnvironmentConfig).filter(
        PracticeEnvironmentConfig.is_active == True
    )
    
    # 按环境类型筛选
    if environment_type:
        if environment_type in ["normal", "jupyter", "desktop"]:
            query = query.filter(PracticeEnvironmentConfig.environment_type == environment_type)
    
    # 按关键词搜索
    if keyword:
        query = query.filter(
            PracticeEnvironmentConfig.name.ilike(f"%{keyword}%")
        )
    
    # 获取总数
    total = query.count()
    
    # 分页
    configs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 转换为响应格式
    items = [db_config_to_response(config) for config in configs]
    
    return schemas.ApiResponse(
        code="0000",
        message="success",
        data=PaginatedEnvironmentResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        ).model_dump()
    )


@router.get("/practice-environments/{environment_id}", response_model=schemas.ApiResponse)
async def get_practice_environment_detail(
    environment_id: str,
    db: Session = Depends(get_db)
):
    """获取实践环境详情"""
    try:
        env_id = int(environment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    config = db.query(PracticeEnvironmentConfig).filter(
        PracticeEnvironmentConfig.id == env_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    return schemas.ApiResponse(
        code="0000",
        message="success",
        data=db_config_to_response(config).model_dump()
    )


@router.put("/practice-environments/{environment_id}", response_model=schemas.ApiResponse)
async def update_practice_environment(
    environment_id: str,
    update_data: EnvironmentConfigUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """更新实践环境配置"""
    try:
        env_id = int(environment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    config = db.query(PracticeEnvironmentConfig).filter(
        PracticeEnvironmentConfig.id == env_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    # 更新存储配置
    if update_data.storage:
        config.storage_min = update_data.storage.min
        config.storage_max = update_data.storage.max
        config.storage_default = update_data.storage.default
    
    # 更新内存配置
    if update_data.memory:
        config.memory_min = update_data.memory.min
        config.memory_max = update_data.memory.max
        config.memory_default = update_data.memory.default
    
    # 更新CPU配置
    if update_data.cpu:
        config.cpu_min = update_data.cpu.min
        config.cpu_max = update_data.cpu.max
        config.cpu_default = update_data.cpu.default
    
    # 更新其他字段
    if update_data.docker_image is not None:
        config.docker_image = update_data.docker_image
    if update_data.docker_port is not None:
        config.docker_port = update_data.docker_port
    if update_data.description is not None:
        config.description = update_data.description
    if update_data.is_active is not None:
        config.is_active = update_data.is_active
    
    db.commit()
    db.refresh(config)
    
    return schemas.ApiResponse(
        code="0000",
        message="环境配置更新成功",
        data=db_config_to_response(config).model_dump()
    )


@router.post("/practice-environments", response_model=schemas.ApiResponse)
async def create_practice_environment(
    create_data: EnvironmentConfigCreate = Body(...),
    db: Session = Depends(get_db)
):
    """创建新的实践环境配置"""
    # 检查名称是否已存在
    existing = db.query(PracticeEnvironmentConfig).filter(
        PracticeEnvironmentConfig.name == create_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="环境名称已存在")
    
    # 解析环境类型
    env_type = create_data.type if create_data.type in ["normal", "jupyter", "desktop"] else "normal"
    
    config = PracticeEnvironmentConfig(
        name=create_data.name,
        environment_type=env_type,
        storage_min=create_data.storage.min,
        storage_max=create_data.storage.max,
        storage_default=create_data.storage.default,
        memory_min=create_data.memory.min,
        memory_max=create_data.memory.max,
        memory_default=create_data.memory.default,
        cpu_min=create_data.cpu.min,
        cpu_max=create_data.cpu.max,
        cpu_default=create_data.cpu.default,
        docker_image=create_data.docker_image,
        docker_port=create_data.docker_port,
        description=create_data.description
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return schemas.ApiResponse(
        code="0000",
        message="环境配置创建成功",
        data=db_config_to_response(config).model_dump()
    )


@router.delete("/practice-environments/{environment_id}", response_model=schemas.ApiResponse)
async def delete_practice_environment(
    environment_id: str,
    db: Session = Depends(get_db)
):
    """删除实践环境配置（软删除）"""
    try:
        env_id = int(environment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的环境ID")
    
    config = db.query(PracticeEnvironmentConfig).filter(
        PracticeEnvironmentConfig.id == env_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="环境不存在")
    
    # 软删除
    config.is_active = False
    db.commit()
    
    return schemas.ApiResponse(
        code="0000",
        message="环境配置已删除",
        data={"id": environment_id}
    )


@router.get("/server-nodes/overview", response_model=schemas.ApiResponse)
async def get_server_nodes_overview(db: Session = Depends(get_db)):
    """获取服务器节点概览"""
    # 获取本地服务器资源信息
    local_server = get_system_resources()
    
    # 如果Docker可用，尝试获取Docker主机信息
    compute_servers = []
    if DOCKER_AVAILABLE and docker_client:
        try:
            info = docker_client.info()
            compute_servers.append(ServerNodeInfo(
                id="docker-host",
                name="Docker计算节点",
                type="compute",
                status="online",
                cpu_usage=local_server.cpu_usage,  # 共享主机CPU
                memory_usage=local_server.memory_usage,  # 共享主机内存
                memory_total=info.get('MemTotal', 0) // (1024 * 1024),
                disk_usage=local_server.disk_usage,
                disk_total=local_server.disk_total,
                container_count=info.get('ContainersRunning', 0)
            ))
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"获取Docker信息失败: {e}")
    
    return schemas.ApiResponse(
        code="0000",
        message="success",
        data=ServerNodesOverview(
            application_servers=[local_server],
            compute_servers=compute_servers
        ).model_dump()
    )


@router.post("/server-nodes/refresh", response_model=schemas.ApiResponse)
async def refresh_server_nodes(db: Session = Depends(get_db)):
    """刷新服务器节点数据"""
    local_server = get_system_resources()
    
    compute_servers = []
    if DOCKER_AVAILABLE and docker_client:
        try:
            info = docker_client.info()
            compute_servers.append(ServerNodeInfo(
                id="docker-host",
                name="Docker计算节点",
                type="compute",
                status="online",
                cpu_usage=local_server.cpu_usage,
                memory_usage=local_server.memory_usage,
                memory_total=info.get('MemTotal', 0) // (1024 * 1024),
                disk_usage=local_server.disk_usage,
                disk_total=local_server.disk_total,
                container_count=info.get('ContainersRunning', 0)
            ))
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"获取Docker信息失败: {e}")
    
    return schemas.ApiResponse(
        code="0000",
        message="刷新成功",
        data=ServerNodesOverview(
            application_servers=[local_server],
            compute_servers=compute_servers
        ).model_dump()
    )


@router.get("/container-processes", response_model=schemas.ApiResponse)
async def get_container_processes(
    keyword: Optional[str] = Query(None),
    environment_type: Optional[str] = Query(None),
    start_time_begin: Optional[str] = Query(None),
    start_time_end: Optional[str] = Query(None),
    duration_min: Optional[int] = Query(None),
    duration_max: Optional[int] = Query(None),
    cpu_min: Optional[float] = Query(None),
    cpu_max: Optional[float] = Query(None),
    memory_min: Optional[float] = Query(None),
    memory_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """获取容器进程列表"""
    containers_list = []

    try:
        # 从数据库获取活动容器记录
        query = db.query(ContainerProcessModel).filter(
            ContainerProcessModel.status == "running"
        )

        # 按关键词搜索（搜索容器名称）
        if keyword:
            query = query.filter(
                ContainerProcessModel.container_name.ilike(f"%{keyword}%")
            )

        # 按环境类型筛选
        if environment_type:
            query = query.filter(ContainerProcessModel.environment_type == environment_type)

        # 获取数据库中的容器记录
        db_containers = query.all()

        now = datetime.now(timezone.utc)

        for container in db_containers:
            try:
                # 计算运行时长
                if container.start_time:
                    # 处理时区问题：确保 start_time 有时区信息
                    start_time = container.start_time
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    duration = int((now - start_time).total_seconds())
                else:
                    duration = 0

                # 应用筛选条件
                if duration_min is not None and duration < duration_min:
                    continue
                if duration_max is not None and duration > duration_max:
                    continue
                if cpu_min is not None and (container.cpu_usage or 0) < cpu_min:
                    continue
                if cpu_max is not None and (container.cpu_usage or 0) > cpu_max:
                    continue
                if memory_min is not None and (container.memory_usage or 0) < memory_min:
                    continue
                if memory_max is not None and (container.memory_usage or 0) > memory_max:
                    continue

                # 获取用户名（通过关系）
                user_name = "未知用户"
                if container.user:
                    user_name = container.user.full_name or container.user.username or f"用户{container.user_id}"

                # 获取课程名称（通过关系）
                course_name = container.container_name or "未知课程"
                if container.course:
                    course_name = getattr(container.course, 'name', None) or course_name
                elif container.training:
                    course_name = getattr(container.training, 'name', None) or course_name

                containers_list.append(ContainerProcess(
                    id=container.container_id,
                    user_name=user_name,
                    user_id=str(container.user_id),
                    course_name=course_name,
                    environment_type=container.environment_type,
                    start_time=container.start_time.isoformat() if container.start_time else "",
                    running_time=duration,
                    cpu_usage=round(container.cpu_usage or 0.0, 2),
                    memory_usage=round(container.memory_usage or 0.0, 2),
                    memory_limit=round(container.memory_limit or 1024.0, 2),
                    status=container.status
                ))
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"处理容器 {container.container_id} 时出错: {e}")
                continue

        # 如果数据库为空，尝试从Docker获取实际运行的容器（不获取stats以避免阻塞）
        if not containers_list and DOCKER_AVAILABLE and docker_client:
            docker_containers = safe_docker_call(docker_client.containers.list, default=[])
            if docker_containers:
                for dc in docker_containers:
                    try:
                        # 只显示huixue相关的容器
                        if not dc.name.startswith("huixue-"):
                            continue

                        # 获取启动时间（不调用stats以避免阻塞）
                        created = dc.attrs.get('Created', '')
                        if created:
                            try:
                                start_time = datetime.fromisoformat(created.replace('Z', '+00:00'))
                                duration = int((now - start_time).total_seconds())
                            except:
                                start_time = now
                                duration = 0
                        else:
                            start_time = now
                            duration = 0

                        containers_list.append(ContainerProcess(
                            id=dc.short_id,
                            user_name="系统容器",
                            user_id="0",
                            course_name=dc.name,
                            environment_type="system",
                            start_time=start_time.isoformat(),
                            running_time=duration,
                            cpu_usage=0.0,  # 不获取stats以避免阻塞
                            memory_usage=0.0,  # 不获取stats以避免阻塞
                            memory_limit=1024.0,  # 默认1GB
                            status=dc.status
                        ))
                    except HTTPException:
                        raise
                    except Exception as e:
                        logger.warning(f"处理Docker容器时出错: {e}")
                        continue

        total = len(containers_list)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=PaginatedContainerResponse(
                items=containers_list,
                total=total
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取容器进程列表失败: {e}")
        # 返回空列表而不是报错
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=PaginatedContainerResponse(
                items=[],
                total=0
            ).model_dump()
        )


@router.post("/container-processes/refresh", response_model=schemas.ApiResponse)
async def refresh_container_processes(db: Session = Depends(get_db)):
    """刷新容器进程数据 - 同步Docker容器状态到数据库"""
    updated_count = 0
    
    if DOCKER_AVAILABLE and docker_client:
        # 获取所有运行中的容器（使用安全调用）
        running_containers = safe_docker_call(docker_client.containers.list, default=[])
        if running_containers:
            running_ids = set(c.id for c in running_containers)
            
            # 更新数据库中的容器状态
            db_containers = db.query(ContainerProcessModel).all()
            for container in db_containers:
                if container.container_id not in running_ids:
                    container.status = "stopped"
                    updated_count += 1
            
            db.commit()
    
    # 重新获取列表
    containers_list = []
    query = db.query(ContainerProcessModel).filter(ContainerProcessModel.status == "running")
    db_containers = query.all()
    
    now = datetime.now(timezone.utc)
    for container in db_containers:
        # 获取用户名
        user_name = "未知用户"
        if container.user:
            user_name = container.user.full_name or container.user.username or f"用户{container.user_id}"

        # 获取课程名称
        course_name = container.container_name or "未知课程"
        if container.course:
            course_name = getattr(container.course, 'name', None) or course_name
        elif container.training:
            course_name = getattr(container.training, 'name', None) or course_name
        
        duration = int((now - container.start_time).total_seconds()) if container.start_time else 0
        
        containers_list.append(ContainerProcess(
            id=container.container_id,
            user_name=user_name,
            user_id=str(container.user_id),
            course_name=course_name,
            environment_type=container.environment_type,
            start_time=container.start_time.isoformat() if container.start_time else "",
            running_time=duration,
            cpu_usage=round(container.cpu_usage or 0.0, 2),
            memory_usage=round(container.memory_usage or 0.0, 2),
            memory_limit=round(container.memory_limit or 1024.0, 2),
            status=container.status
        ))
    
    return schemas.ApiResponse(
        code="0000",
        message=f"刷新成功，更新了{updated_count}个容器状态",
        data=PaginatedContainerResponse(
            items=containers_list,
            total=len(containers_list)
        ).model_dump()
    )


@router.post("/containers/{container_id}/stop", response_model=schemas.ApiResponse)
async def stop_container(
    container_id: str,
    reason: Optional[str] = Body(None),
    operator_id: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    """停止容器"""
    # 更新数据库状态
    container_record = db.query(ContainerProcessModel).filter(
        ContainerProcessModel.container_id == container_id
    ).first()
    
    if container_record:
        container_record.status = "stopped"
        db.commit()
    
    # 尝试停止Docker容器（使用安全调用）
    if DOCKER_AVAILABLE and docker_client:
        def stop_container_task():
            try:
                container = docker_client.containers.get(container_id)
                container.stop(timeout=10)
                return True
            except docker.errors.NotFound:
                return True  # 容器不存在也算成功
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"停止容器 {container_id} 失败: {e}")
                return False
        
        result = safe_docker_call(stop_container_task, default=True, timeout=15)
        if result:
            logger.info(f"容器 {container_id} 已停止，原因: {reason}")
    
    return schemas.ApiResponse(
        code="0000",
        message="容器已停止",
        data={"container_id": container_id, "stopped": True}
    )


@router.post("/containers/batch-stop", response_model=schemas.ApiResponse)
async def batch_stop_containers(
    container_ids: List[str] = Body(...),
    reason: Optional[str] = Body(None),
    operator_id: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    """批量停止容器"""
    results = []
    success_count = 0
    
    for container_id in container_ids:
        # 更新数据库状态
        container_record = db.query(ContainerProcessModel).filter(
            ContainerProcessModel.container_id == container_id
        ).first()
        
        if container_record:
            container_record.status = "stopped"
        
        success = True
        if DOCKER_AVAILABLE and docker_client:
            def stop_task():
                try:
                    c = docker_client.containers.get(container_id)
                    c.stop(timeout=10)
                    return True
                except docker.errors.NotFound:
                    return True
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"停止容器 {container_id} 失败: {e}")
                    return False
            
            success = safe_docker_call(stop_task, default=True, timeout=15)
        
        results.append({"container_id": container_id, "success": success})
        if success:
            success_count += 1
    
    db.commit()
    
    return schemas.ApiResponse(
        code="0000",
        message=f"已停止 {success_count}/{len(container_ids)} 个容器",
        data={"results": results, "stopped_count": success_count}
    )


@router.get("/concurrent-experiment-setting", response_model=schemas.ApiResponse)
async def get_concurrent_experiment_setting(db: Session = Depends(get_db)):
    """获取并发实验设置"""
    init_default_settings(db)
    
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "concurrent_experiment_enabled"
    ).first()
    
    enabled = False
    if setting:
        enabled = setting.value.lower() == "true"
    
    return schemas.ApiResponse(
        code="0000",
        message="success",
        data=ConcurrentExperimentSetting(enabled=enabled).model_dump()
    )


@router.put("/concurrent-experiment-setting", response_model=schemas.ApiResponse)
async def update_concurrent_experiment_setting(
    enable: bool = Body(..., embed=True),
    operator_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """更新并发实验设置"""
    init_default_settings(db)
    
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "concurrent_experiment_enabled"
    ).first()
    
    stopped_count = 0
    
    if setting:
        setting.value = "true" if enable else "false"
    else:
        setting = SystemSetting(
            key="concurrent_experiment_enabled",
            value="true" if enable else "false",
            value_type="bool",
            description="是否允许同时开启多个实验",
            category="experiment"
        )
        db.add(setting)
    
    # 如果禁用多实验，需要停止每个用户的多余容器
    if not enable:
        # 查找每个用户的多余容器
        from sqlalchemy import func as sql_func
        
        # 获取每个用户运行中的容器数
        user_containers = db.query(
            ContainerProcessModel.user_id,
            sql_func.count(ContainerProcessModel.id).label('count')
        ).filter(
            ContainerProcessModel.status == "running"
        ).group_by(ContainerProcessModel.user_id).having(
            sql_func.count(ContainerProcessModel.id) > 1
        ).all()
        
        for user_id, count in user_containers:
            # 保留最新的容器，停止其他的
            containers = db.query(ContainerProcessModel).filter(
                ContainerProcessModel.user_id == user_id,
                ContainerProcessModel.status == "running"
            ).order_by(ContainerProcessModel.start_time.desc()).all()
            
            for container in containers[1:]:  # 跳过第一个（最新的）
                container.status = "stopped"
                stopped_count += 1
                
                if DOCKER_AVAILABLE and docker_client:
                    cid = container.container_id
                    def stop_task():
                        try:
                            dc = docker_client.containers.get(cid)
                            dc.stop(timeout=10)
                        except:
                            pass
                    safe_docker_call(stop_task, timeout=15)
    
    db.commit()
    
    message = "设置已更新"
    if stopped_count > 0:
        message += f"，已停止 {stopped_count} 个多余容器"
    
    return schemas.ApiResponse(
        code="0000",
        message=message,
        data={
            "enabled": enable,
            "stopped_count": stopped_count
        }
    )


# ==================== HDFS持久化管理 ====================

@router.get("/hdfs/status", response_model=schemas.ApiResponse)
async def get_hdfs_status():
    """获取HDFS服务状态"""
    try:
        from app.services.hdfs_persistence import hdfs_service

        status = {
            "enabled": hdfs_service.enabled,
            "host": hdfs_service.hdfs_host if hdfs_service.enabled else None,
            "port": hdfs_service.hdfs_port if hdfs_service.enabled else None,
            "base_path": hdfs_service.hdfs_base_path if hdfs_service.enabled else None,
            "sync_on_stop": hdfs_service.sync_on_stop if hdfs_service.enabled else None
        }

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取HDFS状态失败: {e}")
        return schemas.ApiResponse(
            code="0000",
            message="success",
            data={"enabled": False, "error": str(e)}
        )


@router.get("/hdfs/storage/{user_id}", response_model=schemas.ApiResponse)
async def get_user_hdfs_storage(user_id: int, current_user: dict = Depends(get_current_user)):
    """获取用户的HDFS存储使用情况"""
    user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("teacher", "student"))
    try:
        from app.services.hdfs_persistence import hdfs_service

        if not hdfs_service.enabled:
            return schemas.ApiResponse(
                code="0000",
                message="HDFS未启用",
                data={"enabled": False}
            )

        usage = hdfs_service.get_user_storage_usage(user_id)

        return schemas.ApiResponse(
            code="0000",
            message="success",
            data=usage
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户HDFS存储使用情况失败: {e}")
        return schemas.ApiResponse(
            code="5000",
            message=f"获取存储使用情况失败: {str(e)}",
            data=None
        )


@router.post("/hdfs/sync", response_model=schemas.ApiResponse)
async def sync_to_hdfs(
    user_id: int = Query(..., description="[已忽略客户端值，使用真实 token 归属]"),
    training_id: int = Query(..., description="实训ID"),
    current_user: dict = Depends(get_current_user)
):
    """手动触发数据同步到HDFS"""
    try:
        user_id = resolve_scoped_id(current_user, user_id, allowed_roles=("student", "teacher"))
        from app.services.hdfs_persistence import hdfs_service
        from app.core.config import settings
        from pathlib import Path

        if not hdfs_service.enabled:
            return schemas.ApiResponse(
                code="4000",
                message="HDFS未启用",
                data=None
            )

        # 获取本地工作目录
        work_dir = Path(settings.CONTAINER_STUDENT_WORK_BASE) / str(user_id) / str(training_id)

        if not work_dir.exists():
            return schemas.ApiResponse(
                code="4004",
                message="本地工作目录不存在",
                data={"path": str(work_dir)}
            )

        # 执行同步
        success = hdfs_service.sync_to_hdfs(user_id, training_id, work_dir)

        if success:
            return schemas.ApiResponse(
                code="0000",
                message="数据已同步到HDFS",
                data={
                    "user_id": user_id,
                    "training_id": training_id,
                    "hdfs_path": hdfs_service._get_hdfs_path(user_id, training_id)
                }
            )
        else:
            return schemas.ApiResponse(
                code="5000",
                message="同步失败",
                data=None
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步到HDFS失败: {e}")
        return schemas.ApiResponse(
            code="5000",
            message=f"同步失败: {str(e)}",
            data=None
        )
