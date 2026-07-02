from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import models
from app.schemas import schemas


# ==================== 教学资源管理相关CRUD操作 ====================

def get_practice_environments_for_admin(
    db: Session,
    environment_type: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取实践环境列表（管理员）"""
    query = db.query(models.PracticeEnvironment)
    
    # 环境类型筛选
    if environment_type:
        query = query.filter(models.PracticeEnvironment.environment_type == environment_type)
    
    # 名称关键词搜索
    if keyword:
        query = query.filter(models.PracticeEnvironment.name.ilike(f"%{keyword}%"))
    
    # 只显示可用的环境
    query = query.filter(models.PracticeEnvironment.is_active == True)
    
    total = query.count()
    skip = (page - 1) * page_size
    environments = query.offset(skip).limit(page_size).all()
    
    # 获取每个环境的配置信息
    result_list = []
    for env in environments:
        config = db.query(models.PracticeEnvironmentConfig).filter(
            models.PracticeEnvironmentConfig.environment_id == env.id
        ).first()
        
        env_dict = {
            "id": env.id,
            "name": env.name,
            "environment_type": env.environment_type,
            "docker_image": env.docker_image,
            "description": env.description,
            "is_active": env.is_active,
            "created_at": env.created_at,
            "config": {
                "min_storage": config.min_storage if config else "100Mi",
                "max_storage": config.max_storage if config else "1Gi",
                "default_storage": config.default_storage if config else "500Mi",
                "min_memory": config.min_memory if config else "128Mi",
                "max_memory": config.max_memory if config else "2Gi",
                "default_memory": config.default_memory if config else "1Gi",
                "min_cpu": config.min_cpu if config else "0.1",
                "max_cpu": config.max_cpu if config else "2",
                "default_cpu": config.default_cpu if config else "1"
            } if config else None
        }
        result_list.append(env_dict)
    
    return {
        "list": result_list,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


def get_practice_environment_detail(db: Session, environment_id: int):
    """获取实践环境详情"""
    environment = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.id == environment_id
    ).first()
    
    if not environment:
        return None
    
    config = db.query(models.PracticeEnvironmentConfig).filter(
        models.PracticeEnvironmentConfig.environment_id == environment_id
    ).first()
    
    return {
        "id": environment.id,
        "name": environment.name,
        "environment_type": environment.environment_type,
        "docker_image": environment.docker_image,
        "description": environment.description,
        "is_active": environment.is_active,
        "created_at": environment.created_at,
        "config": config
    }


def update_practice_environment_config(
    db: Session,
    environment_id: int,
    config_update: dict
):
    """更新实践环境配置"""
    # 检查环境是否存在
    environment = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.id == environment_id
    ).first()
    
    if not environment:
        return None
    
    # 查找或创建配置
    config = db.query(models.PracticeEnvironmentConfig).filter(
        models.PracticeEnvironmentConfig.environment_id == environment_id
    ).first()
    
    if not config:
        config = models.PracticeEnvironmentConfig(environment_id=environment_id)
        db.add(config)
    
    # 更新配置
    for field, value in config_update.items():
        if hasattr(config, field):
            setattr(config, field, value)
    
    config.updated_at = datetime.now()
    
    db.commit()
    db.refresh(config)
    
    return config


def update_practice_environment(
    db: Session,
    environment_id: int,
    environment_update: dict
):
    """更新实践环境基本信息"""
    environment = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.id == environment_id
    ).first()
    
    if not environment:
        return None
    
    # 更新基本信息
    for field, value in environment_update.items():
        if field != "config" and hasattr(environment, field):
            setattr(environment, field, value)
    
    # 更新配置（如果提供）
    if "config" in environment_update and environment_update["config"]:
        config = db.query(models.PracticeEnvironmentConfig).filter(
            models.PracticeEnvironmentConfig.environment_id == environment_id
        ).first()
        
        if not config:
            config = models.PracticeEnvironmentConfig(environment_id=environment_id)
            db.add(config)
        
        config_data = environment_update["config"]
        for field, value in config_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        config.updated_at = datetime.now()
    
    db.commit()
    db.refresh(environment)
    
    return get_practice_environment_detail(db, environment_id)


def get_server_nodes_overview(db: Session):
    """获取服务器节点概览"""
    # 获取应用服务器
    application_servers = db.query(models.ServerNode).filter(
        models.ServerNode.node_type == "application",
        models.ServerNode.is_active == True
    ).all()
    
    # 获取计算节点
    compute_nodes = db.query(models.ServerNode).filter(
        models.ServerNode.node_type == "compute",
        models.ServerNode.is_active == True
    ).all()
    
    def add_status_colors(nodes):
        result = []
        for node in nodes:
            node_dict = {
                "id": node.id,
                "node_name": node.node_name,
                "node_type": node.node_type,
                "ip_address": node.ip_address,
                "total_cpu_cores": node.total_cpu_cores,
                "total_memory_gb": node.total_memory_gb,
                "total_storage_gb": node.total_storage_gb,
                "cpu_usage_percent": node.cpu_usage_percent,
                "memory_usage_percent": node.memory_usage_percent,
                "storage_usage_percent": node.storage_usage_percent,
                "status": node.status,
                "last_heartbeat": node.last_heartbeat,
                "is_active": node.is_active,
                "created_at": node.created_at,
                "updated_at": node.updated_at,
                # 根据使用率确定颜色状态
                "cpu_status_color": _get_usage_color(node.cpu_usage_percent),
                "memory_status_color": _get_usage_color(node.memory_usage_percent),
                "storage_status_color": _get_usage_color(node.storage_usage_percent)
            }
            result.append(node_dict)
        return result
    
    return {
        "application_servers": add_status_colors(application_servers),
        "compute_nodes": add_status_colors(compute_nodes),
        "last_updated": datetime.now()
    }


def _get_usage_color(usage_percent: float) -> str:
    """根据使用率获取颜色状态"""
    if usage_percent < 70:
        return "green"  # 正常
    elif usage_percent < 85:
        return "orange"  # 警告
    else:
        return "red"  # 危险


def get_resource_usage_trend(db: Session, hours: int = 24):
    """获取资源使用趋势数据"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # 查询监控记录
    records = db.query(models.ResourceMonitorRecord).filter(
        models.ResourceMonitorRecord.recorded_at >= start_time,
        models.ResourceMonitorRecord.recorded_at <= end_time
    ).order_by(models.ResourceMonitorRecord.recorded_at).all()
    
    # 按时间聚合数据
    timestamps = []
    cpu_usage = []
    memory_usage = []
    storage_usage = []
    
    # 按小时分组计算平均值
    time_groups = {}
    for record in records:
        hour_key = record.recorded_at.replace(minute=0, second=0, microsecond=0)
        if hour_key not in time_groups:
            time_groups[hour_key] = []
        time_groups[hour_key].append(record)
    
    for time_key in sorted(time_groups.keys()):
        group_records = time_groups[time_key]
        avg_cpu = sum(r.cpu_usage_percent for r in group_records) / len(group_records)
        avg_memory = sum(r.memory_usage_percent for r in group_records) / len(group_records)
        avg_storage = sum(r.storage_usage_percent for r in group_records) / len(group_records)
        
        timestamps.append(time_key)
        cpu_usage.append(round(avg_cpu, 2))
        memory_usage.append(round(avg_memory, 2))
        storage_usage.append(round(avg_storage, 2))
    
    return {
        "timestamps": timestamps,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "storage_usage": storage_usage
    }


def get_container_processes(
    db: Session,
    keyword: Optional[str] = None,
    environment_type: Optional[str] = None,
    start_time_range: Optional[List[datetime]] = None,
    running_duration_range: Optional[List[int]] = None,
    cpu_range: Optional[List[float]] = None,
    memory_range: Optional[List[float]] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取容器进程列表"""
    query = db.query(models.ContainerProcess).join(
        models.User, models.ContainerProcess.user_id == models.User.id
    ).outerjoin(
        models.Course, models.ContainerProcess.course_id == models.Course.id
    ).filter(
        models.ContainerProcess.status == "running"
    )
    
    # 关键词搜索（姓名、账号、课程名）
    if keyword:
        query = query.filter(
            or_(
                models.User.full_name.ilike(f"%{keyword}%"),
                models.User.username.ilike(f"%{keyword}%"),
                models.Course.title.ilike(f"%{keyword}%")
            )
        )
    
    # 实验类型筛选
    if environment_type:
        query = query.filter(models.ContainerProcess.environment_type == environment_type)
    
    # 开启时间范围筛选
    if start_time_range and len(start_time_range) == 2:
        query = query.filter(
            models.ContainerProcess.start_time >= start_time_range[0],
            models.ContainerProcess.start_time <= start_time_range[1]
        )
    
    # CPU使用率范围筛选
    if cpu_range and len(cpu_range) == 2:
        query = query.filter(
            models.ContainerProcess.cpu_usage >= cpu_range[0],
            models.ContainerProcess.cpu_usage <= cpu_range[1]
        )
    
    # 内存使用率范围筛选
    if memory_range and len(memory_range) == 2:
        memory_usage_percent = (models.ContainerProcess.memory_usage / models.ContainerProcess.memory_limit) * 100
        query = query.filter(
            memory_usage_percent >= memory_range[0],
            memory_usage_percent <= memory_range[1]
        )
    
    # 按开始时间倒序排列
    query = query.order_by(models.ContainerProcess.start_time.desc())
    
    total = query.count()
    skip = (page - 1) * page_size
    containers = query.offset(skip).limit(page_size).all()
    
    # 构建响应数据
    result_list = []
    for container in containers:
        user = db.query(models.User).filter(models.User.id == container.user_id).first()
        course = db.query(models.Course).filter(models.Course.id == container.course_id).first() if container.course_id else None
        
        # 计算运行时长
        running_duration = datetime.now() - container.start_time
        duration_str = _format_duration(running_duration)
        
        # 计算内存使用率
        memory_usage_percent = (container.memory_usage / container.memory_limit) * 100 if container.memory_limit > 0 else 0
        
        # 检查是否在运行时长范围内
        if running_duration_range and len(running_duration_range) == 2:
            duration_minutes = running_duration.total_seconds() / 60
            if not (running_duration_range[0] <= duration_minutes <= running_duration_range[1]):
                continue
        
        container_dict = {
            "id": container.id,
            "container_id": container.container_id,
            "container_name": container.container_name,
            "user_id": container.user_id,
            "user_name": user.full_name if user else "未知用户",
            "user_account": user.username if user else "未知账号",
            "course_id": container.course_id,
            "course_name": course.title if course else "无关联课程",
            "environment_type": container.environment_type,
            "cpu_usage": container.cpu_usage,
            "memory_usage": container.memory_usage,
            "memory_limit": container.memory_limit,
            "memory_usage_percent": round(memory_usage_percent, 2),
            "start_time": container.start_time,
            "running_duration": duration_str,
            "last_activity": container.last_activity,
            "status": container.status,
            "ip_address": container.ip_address,
            "port": container.port,
            "created_at": container.created_at,
            "updated_at": container.updated_at
        }
        result_list.append(container_dict)
    
    return {
        "list": result_list,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


def _format_duration(duration: timedelta) -> str:
    """格式化时长显示"""
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}小时{minutes}分钟"
    elif minutes > 0:
        return f"{minutes}分钟{seconds}秒"
    else:
        return f"{seconds}秒"


def stop_container_process(
    db: Session,
    container_id: str,
    reason: Optional[str] = None,
    operator_id: Optional[int] = None
):
    """停止单个容器进程"""
    # 查找容器
    container = db.query(models.ContainerProcess).filter(
        models.ContainerProcess.container_id == container_id
    ).first()
    
    if not container:
        return False
    
    try:
        # 模拟调用容器停止API
        success = _call_container_stop_api(container_id)
        
        if success:
            # 更新容器状态
            container.status = "stopped"
            container.updated_at = datetime.now()
            
            # 记录操作日志
            log = models.ContainerOperationLog(
                container_id=container_id,
                operation_type="stop",
                operator_id=operator_id,
                operator_type="manual",
                operation_reason=reason,
                operation_result="success"
            )
            db.add(log)
            
            db.commit()
            return True
        else:
            # 记录失败日志
            log = models.ContainerOperationLog(
                container_id=container_id,
                operation_type="stop",
                operator_id=operator_id,
                operator_type="manual",
                operation_reason=reason,
                operation_result="failed",
                error_message="容器停止API调用失败"
            )
            db.add(log)
            db.commit()
            return False
            
    except Exception as e:
        # 记录错误日志
        log = models.ContainerOperationLog(
            container_id=container_id,
            operation_type="stop",
            operator_id=operator_id,
            operator_type="manual",
            operation_reason=reason,
            operation_result="failed",
            error_message=str(e)
        )
        db.add(log)
        db.commit()
        return False


def batch_stop_containers(
    db: Session,
    container_ids: List[str],
    reason: Optional[str] = None,
    operator_id: Optional[int] = None
):
    """批量停止容器进程"""
    success_count = 0
    failed_count = 0
    
    for container_id in container_ids:
        if stop_container_process(db, container_id, reason, operator_id):
            success_count += 1
        else:
            failed_count += 1
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total_count": len(container_ids)
    }


def _call_container_stop_api(container_id: str) -> bool:
    """模拟调用容器停止API"""
    # 这里应该调用实际的容器管理API
    # 目前返回模拟结果
    import random
    return random.choice([True, True, True, False])  # 75%成功率


def get_concurrent_experiment_setting(db: Session):
    """获取并发实验设置"""
    setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "concurrent_experiment_enabled"
    ).first()
    
    enable = True  # 默认允许
    if setting:
        enable = setting.value.lower() == "true"
    
    return {
        "enable": enable,
        "updated_at": setting.updated_at if setting else datetime.now()
    }


def update_concurrent_experiment_setting(db: Session, enable: bool):
    """更新并发实验设置"""
    setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "concurrent_experiment_enabled"
    ).first()
    
    if not setting:
        setting = models.SystemSetting(
            key="concurrent_experiment_enabled",
            value=str(enable).lower(),
            description="是否允许同一用户同时开启多个实验",
            setting_type="boolean"
        )
        db.add(setting)
    else:
        setting.value = str(enable).lower()
        setting.updated_at = datetime.now()
    
    db.commit()
    db.refresh(setting)
    
    return {
        "enable": enable,
        "updated_at": setting.updated_at
    }


def handle_concurrent_experiment_disable(db: Session, operator_id: Optional[int] = None):
    """处理并发实验关闭时的容器清理"""
    # 查找每个用户的多个运行中容器
    user_containers = db.query(
        models.ContainerProcess.user_id,
        func.count(models.ContainerProcess.id).label('container_count')
    ).filter(
        models.ContainerProcess.status == "running"
    ).group_by(
        models.ContainerProcess.user_id
    ).having(
        func.count(models.ContainerProcess.id) > 1
    ).all()
    
    stopped_count = 0
    
    for user_id, container_count in user_containers:
        # 获取该用户的所有容器，按开始时间排序，保留最新的一个
        containers = db.query(models.ContainerProcess).filter(
            models.ContainerProcess.user_id == user_id,
            models.ContainerProcess.status == "running"
        ).order_by(models.ContainerProcess.start_time.desc()).all()
        
        # 停止除第一个外的所有容器
        for container in containers[1:]:
            if stop_container_process(
                db, 
                container.container_id, 
                "系统自动停止：关闭并发实验功能", 
                operator_id
            ):
                stopped_count += 1
    
    return stopped_count


def get_resource_management_stats(db: Session):
    """获取教学资源管理统计信息"""
    # 实践环境统计
    total_environments = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.is_active == True
    ).count()
    
    normal_practice_count = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.environment_type == "普通实践",
        models.PracticeEnvironment.is_active == True
    ).count()
    
    jupyter_count = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.environment_type == "jupyter",
        models.PracticeEnvironment.is_active == True
    ).count()
    
    cloud_desktop_count = db.query(models.PracticeEnvironment).filter(
        models.PracticeEnvironment.environment_type == "云桌面",
        models.PracticeEnvironment.is_active == True
    ).count()
    
    # 容器统计
    total_containers = db.query(models.ContainerProcess).count()
    running_containers = db.query(models.ContainerProcess).filter(
        models.ContainerProcess.status == "running"
    ).count()
    stopped_containers = total_containers - running_containers
    
    # 服务器统计
    total_nodes = db.query(models.ServerNode).filter(
        models.ServerNode.is_active == True
    ).count()
    
    online_nodes = db.query(models.ServerNode).filter(
        models.ServerNode.status == "online",
        models.ServerNode.is_active == True
    ).count()
    
    offline_nodes = total_nodes - online_nodes
    
    # 资源使用统计
    avg_stats = db.query(
        func.avg(models.ServerNode.cpu_usage_percent).label('avg_cpu'),
        func.avg(models.ServerNode.memory_usage_percent).label('avg_memory'),
        func.avg(models.ServerNode.storage_usage_percent).label('avg_storage')
    ).filter(
        models.ServerNode.is_active == True,
        models.ServerNode.status == "online"
    ).first()
    
    return {
        "total_environments": total_environments,
        "normal_practice_count": normal_practice_count,
        "jupyter_count": jupyter_count,
        "cloud_desktop_count": cloud_desktop_count,
        "total_containers": total_containers,
        "running_containers": running_containers,
        "stopped_containers": stopped_containers,
        "total_nodes": total_nodes,
        "online_nodes": online_nodes,
        "offline_nodes": offline_nodes,
        "avg_cpu_usage": round(avg_stats.avg_cpu or 0, 2),
        "avg_memory_usage": round(avg_stats.avg_memory or 0, 2),
        "avg_storage_usage": round(avg_stats.avg_storage or 0, 2)
    }


def create_mock_data_for_resource_management(db: Session):
    """创建教学资源管理模拟数据"""
    import random
    from datetime import datetime, timedelta
    
    # 创建模拟服务器节点
    if db.query(models.ServerNode).count() == 0:
        # 应用服务器
        app_servers = [
            {
                "node_name": "应用服务器-01",
                "node_type": "application",
                "ip_address": "192.168.1.10",
                "total_cpu_cores": 16,
                "total_memory_gb": 64.0,
                "total_storage_gb": 1000.0,
                "cpu_usage_percent": random.uniform(30, 80),
                "memory_usage_percent": random.uniform(40, 85),
                "storage_usage_percent": random.uniform(20, 70),
                "status": "online"
            },
            {
                "node_name": "应用服务器-02",
                "node_type": "application",
                "ip_address": "192.168.1.11",
                "total_cpu_cores": 16,
                "total_memory_gb": 64.0,
                "total_storage_gb": 1000.0,
                "cpu_usage_percent": random.uniform(25, 75),
                "memory_usage_percent": random.uniform(35, 80),
                "storage_usage_percent": random.uniform(15, 65),
                "status": "online"
            }
        ]
        
        # 计算节点
        compute_nodes = [
            {
                "node_name": "计算节点-01",
                "node_type": "compute",
                "ip_address": "192.168.2.10",
                "total_cpu_cores": 32,
                "total_memory_gb": 128.0,
                "total_storage_gb": 2000.0,
                "cpu_usage_percent": random.uniform(50, 90),
                "memory_usage_percent": random.uniform(60, 95),
                "storage_usage_percent": random.uniform(30, 80),
                "status": "online"
            },
            {
                "node_name": "计算节点-02",
                "node_type": "compute",
                "ip_address": "192.168.2.11",
                "total_cpu_cores": 32,
                "total_memory_gb": 128.0,
                "total_storage_gb": 2000.0,
                "cpu_usage_percent": random.uniform(45, 85),
                "memory_usage_percent": random.uniform(55, 90),
                "storage_usage_percent": random.uniform(25, 75),
                "status": "online"
            },
            {
                "node_name": "计算节点-03",
                "node_type": "compute",
                "ip_address": "192.168.2.12",
                "total_cpu_cores": 32,
                "total_memory_gb": 128.0,
                "total_storage_gb": 2000.0,
                "cpu_usage_percent": random.uniform(40, 80),
                "memory_usage_percent": random.uniform(50, 85),
                "storage_usage_percent": random.uniform(20, 70),
                "status": "online"
            }
        ]
        
        all_nodes = app_servers + compute_nodes
        for node_data in all_nodes:
            node = models.ServerNode(**node_data)
            node.last_heartbeat = datetime.now()
            db.add(node)
    
    # 创建模拟容器进程
    if db.query(models.ContainerProcess).count() == 0:
        # 获取一些用户和课程
        users = db.query(models.User).limit(10).all()
        courses = db.query(models.Course).limit(5).all()
        
        if users:
            environment_types = ["普通实践", "jupyter", "云桌面"]
            
            for i in range(15):
                user = random.choice(users)
                course = random.choice(courses) if courses and random.choice([True, False]) else None
                env_type = random.choice(environment_types)
                
                start_time = datetime.now() - timedelta(
                    hours=random.randint(0, 48),
                    minutes=random.randint(0, 59)
                )
                
                container = models.ContainerProcess(
                    container_id=f"container_{i+1:03d}",
                    container_name=f"{env_type}_container_{i+1}",
                    user_id=user.id,
                    course_id=course.id if course else None,
                    environment_type=env_type,
                    cpu_usage=random.uniform(10, 80),
                    memory_usage=random.uniform(100, 800),
                    memory_limit=1024.0,
                    start_time=start_time,
                    last_activity=datetime.now() - timedelta(minutes=random.randint(1, 30)),
                    status="running",
                    ip_address=f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    port=random.randint(8000, 9000)
                )
                db.add(container)
    
    # 创建系统设置
    concurrent_setting = db.query(models.SystemSetting).filter(
        models.SystemSetting.key == "concurrent_experiment_enabled"
    ).first()
    
    if not concurrent_setting:
        setting = models.SystemSetting(
            key="concurrent_experiment_enabled",
            value="true",
            description="是否允许同一用户同时开启多个实验",
            setting_type="boolean"
        )
        db.add(setting)
    
    db.commit()
    return True 