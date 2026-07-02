"""
容器管理服务

负责Docker容器的生命周期管理：启动、停止、状态查询等
"""
import docker
import docker.types
import logging
import random
import secrets
import io
import json
import shlex
import tarfile
import textwrap
from typing import Optional, Dict, Tuple, Any, List
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.core.database import get_db
from app.models import models
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 延迟导入HDFS服务，避免循环导入
_hdfs_service = None

def get_hdfs_service():
    """获取HDFS服务实例（延迟加载）"""
    global _hdfs_service
    if _hdfs_service is None:
        from app.services.hdfs_persistence import hdfs_service
        _hdfs_service = hdfs_service
    return _hdfs_service
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUPERSET_CONFIG = PROJECT_ROOT / "superset" / "superset_config_embed.py"


class ContainerManager:
    """Docker容器管理器"""

    def __init__(self):
        """初始化（延迟初始化Docker客户端）"""
        self.client = None
        self._initialized = False
        self._swarm_initialized = False
        self._docker_fallback = False  # Docker不可用时的fallback模式
        # NFS共享存储配置
        # 物理IP: 172.16.100.41 (Server 1内网IP)
        self.NFS_STORAGE_BASE = "/data/huixue_storage"
        self.NFS_SERVER_IP = "172.16.100.41"  # 使用物理网卡内网IP，非VPN地址

    def _ensure_swarm_initialized(self):
        """Swarm已弃用，直接调用普通初始化"""
        self._ensure_initialized()

    def _ensure_initialized(self):
        """确保Docker客户端已初始化（支持远程Docker Host）"""
        if not self._initialized:
            try:
                docker_host = settings.DOCKER_HOST
                # 判断是否远程连接（TCP而非默认Unix socket）
                is_remote = docker_host and not docker_host.startswith("unix://")
                if is_remote:
                    self.client = docker.DockerClient(base_url=docker_host)
                    logger.info(f"Docker远程连接: {docker_host}")
                else:
                    self.client = docker.from_env()
                    logger.info("Docker本地直连接口初始化成功")
                # 测试连接
                self.client.ping()
                self._initialized = True
            except Exception as e:
                logger.error(f"Docker客户端初始化失败: {e}")
                # 设置fallback模式，允许继续运行
                self._docker_fallback = True
                logger.warning("启用Docker fallback模式 - 使用模拟容器")
    
    def _get_available_port(self) -> int:
        """获取一个可用的动态端口"""
        # 简单的端口分配策略：从范围内随机选择一个
        # 实际生产环境应该查询已使用的端口
        port = random.randint(
            settings.DOCKER_PORT_RANGE_START,
            settings.DOCKER_PORT_RANGE_START + 100  # 限制范围避免冲突
        )
        return port

    def _prepare_swarm_volumes(
        self,
        env_type: str,
        user_id: int,
        training_id: int,
        training_name: Optional[str] = None
    ) -> List[dict]:
        """
        准备Swarm服务卷挂载配置 - 使用NFS共享存储
        支持跨节点挂载，使用物理IP 172.16.100.41
        """
        mounts = []

        # 1. 学生工作目录 - 使用NFS实现跨节点共享存储
        # NFS服务器使用物理IP (172.16.100.41)，避免VPN导致的权限问题
        # 使用volume driver实现NFS挂载
        student_workspace = f"{self.NFS_STORAGE_BASE}/student_workspaces/{user_id}"
        nfs_server = self.NFS_SERVER_IP  # 172.16.100.41

        # 确保在manager节点上创建必要的目录
        try:
            import os
            os.makedirs(student_workspace, exist_ok=True)
        except Exception as e:
            logger.warning(f"创建本地目录失败: {e}")

        # 使用NFS volume实现跨节点挂载
        # Docker Swarm会自动在各个节点上挂载NFS
        volume_name = f"huixue-student-{user_id}"
        mounts.append({
            "type": "volume",
            "source": volume_name,
            "target": "/home/jovyan/work",
            "driver": "local",
            "driver_opts": {
                "type": "nfs",
                "o": f"addr={nfs_server},rw,nolock,soft,timeo=30",
                "device": f":{student_workspace}"
            }
        })

        # 2. 如果有实训资源，挂载数据集
        if training_name:
            resource_dir = self._resolve_training_resource_dir(training_name)
            if resource_dir and resource_dir.exists():
                datasets_dir = resource_dir / "datasets"
                if datasets_dir.exists():
                    mounts.append({
                        "type": "bind",
                        "source": str(datasets_dir.resolve()),
                        "target": "/datasets",
                        "read_only": True
                    })

                # Jupyter模板目录
                if env_type.upper() == "JUPYTER":
                    jupyter_dir = resource_dir / "jupyter"
                    if jupyter_dir.exists():
                        mounts.append({
                            "type": "bind",
                            "source": str(jupyter_dir.resolve()),
                            "target": "/templates",
                            "read_only": True
                        })

        return mounts

    def start_swarm_service(
        self,
        env_type: str,
        user_id: int,
        training_id: int,
        training_name: Optional[str] = None,
        db: Optional[Session] = None,
        training_metadata: Optional[Dict[str, Any]] = None,
        init_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        使用Docker Swarm创建学生实训容器服务

        特点：
        1. 强制调度到worker节点（高算力服务器2/3）
        2. 使用NFS共享存储挂载学生工作目录
        3. 动态分配宿主机端口
        4. 资源限制（CPU/内存）

        Returns:
            tuple: (service_id, host_port)
        """
        from app.core.database import SessionLocal
        import os

        # 确保Swarm已初始化
        self._ensure_swarm_initialized()

        # 创建NFS存储目录（如果不存在）
        student_workspace = f"{self.NFS_STORAGE_BASE}/student_workspaces/{user_id}"
        try:
            os.makedirs(student_workspace, exist_ok=True)
            logger.info(f"NFS存储目录已准备: {student_workspace}")
        except Exception as e:
            logger.warning(f"创建NFS目录失败: {e}")

        # 检查是否已有运行中的Swarm服务
        service_name = f"jupyter_stu_{user_id}_{training_id}"

        # 使用新的数据库会话
        db_session = db or SessionLocal()
        try:
            # 检查并复用已存在的服务，绝不删除！
            try:
                existing_service = self.client.services.get(service_name)
                # 从 Swarm 属性中提取已分配的端口
                ports = existing_service.attrs.get('Endpoint', {}).get('Ports', [])
                for p in ports:
                    if p.get('TargetPort') == container_port:
                        existing_port = p.get('PublishedPort')
                        logger.info(f"发现已存在的服务 {service_name}，复用端口: {existing_port}")
                        return service_name, existing_port
                # 如果端口异常，删除重建
                logger.warning(f"服务 {service_name} 端口异常，删除重建...")
                existing_service.remove()
            except Exception as e:
                # 服务不存在，这是正常的
                pass

            existing_id = self.get_existing_container(user_id, training_id, env_type, db_session)
            if existing_id:
                # 查找服务
                try:
                    service = self.client.services.get(existing_id)
                    # 获取端口
                    endpoint = service.attrs.get('Endpoint', {})
                    ports = endpoint.get('Ports', [])
                    if ports:
                        host_port = ports[0].get('PublishedPort')
                        if host_port:
                            logger.info(f"复用现有Swarm服务 {existing_id}, 端口: {host_port}")
                            return existing_id, host_port
                except:
                    pass

            # 获取镜像名称
            if not db_session:
                raise ValueError("数据库会话是必需的")

            image_name = self._get_image_name(env_type, db_session)
            if not image_name:
                # 如果数据库没有配置，使用各环境类型的默认镜像
                env_upper = env_type.upper()
                if env_upper == "JUPYTER":
                    image_name = "huixue-jupyter:latest"
                elif env_upper == "TEMPO_BI":
                    # 优先使用本地镜像，失败时回退到Docker Hub
                    image_name = "huixue-superset:latest"
                elif env_upper == "TEMPO_AI":
                    image_name = "cfprot/knime:latest"
                elif env_upper in ("DESKTOP", "VDI"):
                    image_name = "consol/ubuntu-xfce-vnc:latest"
                else:
                    raise ValueError(f"未找到环境类型 {env_type} 的Docker镜像配置")
                logger.warning(f"TrainingEnvironment表无{env_type}配置，使用默认镜像: {image_name}")

            # 准备环境变量
            env_vars = self._prepare_env_vars(
                env_type,
                user_id,
                training_id,
                training_metadata=training_metadata,
                init_config=init_config,
            )

            # 准备卷挂载
            mounts = self._prepare_swarm_volumes(
                env_type, user_id, training_id, training_name
            )

            # 获取容器内部端口
            container_port = self._get_container_port(env_type)

            # 为Jupyter容器准备自定义命令（包含CSP配置）
            command = None
            if env_type.upper() == "JUPYTER":
                csp_origins = "'self' http://localhost:3000 http://100.74.141.3:3000 http://172.16.100.41:3000 http://localhost:3001"
                command = [
                    "jupyter", "notebook",
                    "--ip=0.0.0.0",
                    "--port=8888",
                    f"--NotebookApp.token={env_vars.get('JUPYTER_TOKEN', 'huixue_token')}",
                    "--allow-root",
                    "--NotebookApp.disable_check_xsrf=True",
                    f"--ServerApp.tornado_settings={{'headers': {{'Content-Security-Policy': \"frame-ancestors {csp_origins}\"}}}}"
                ]

            # 构建EndpointSpec - 使用随机端口避免冲突
            # Docker Swarm格式: {target_port: published_port}
            # target_port = 容器内部端口 (如 8888 for Jupyter)
            # published_port = 映射到主机的端口 (如 30000)
            import random
            published_port = random.randint(30000, 32000)
            # 正确格式: {container_port: published_port} 即 {8888: 300xx}
            endpoint_spec = docker.types.EndpointSpec(
                ports={container_port: published_port}  # {8888: 300xx} 是正确的！
            )

            # 构建服务规格
            service_spec = {
                'name': service_name,
                'image': image_name,
                'networks': ['huixue-net'],
                'endpoint_spec': endpoint_spec,
                'mounts': mounts,
                'env': [f"{k}={v}" for k, v in env_vars.items()],
                # 测试阶段，先移除约束
                # 'constraints': ['node.labels.compute==true', 'node.role==manager'],
                'resources': docker.types.Resources(
                    cpu_limit=1500000000,  # 1.5核
                    mem_limit=4 * 1024 * 1024 * 1024,  # 4GB
                    mem_reservation=512 * 1024 * 1024  # 512MB 预留
                ),
                'restart_policy': docker.types.RestartPolicy(
                    condition='on-failure',
                    delay=5,
                    max_attempts=3
                )
            }

            if command:
                service_spec['command'] = command

            # 创建Swarm服务
            logger.info(f"创建Swarm服务: {service_name}, 镜像: {image_name}")
            service = self.client.services.create(**service_spec)

            # 等待服务分配端口
            service.reload()
            assigned_port = None
            max_wait = 30
            for i in range(max_wait):
                service.reload()
                ports = service.attrs.get('Endpoint', {}).get('Ports', [])
                if ports and ports[0].get('PublishedPort'):
                    assigned_port = ports[0].get('PublishedPort')
                    logger.info(f"Swarm服务 {service_name} 分配端口: {assigned_port}")
                    break
                import time
                time.sleep(1)

            if not assigned_port:
                # 如果无法获取端口，使用创建时指定的端口
                assigned_port = published_port
                logger.warning(f"无法获取Swarm分配的端口，使用预设端口: {assigned_port}")

            # 记录到数据库
            if db_session:
                container_process = models.ContainerProcess(
                    container_id=service.id,
                    container_name=service_name,
                    user_id=user_id,
                    training_id=training_id,
                    environment_type=env_type.upper(),
                    status="running",
                    port=published_port,
                    start_time=datetime.now(timezone.utc),
                    last_activity=datetime.now(timezone.utc),
                )
                db_session.add(container_process)
                db_session.commit()
                logger.info(f"Swarm服务创建成功: {service.id}, 端口: {published_port}")

            return service.id, published_port

        except Exception as e:
            logger.error(f"创建Swarm服务失败: {e}")
            raise
        finally:
            if not db:
                db_session.close()

    def _generate_container_name(
        self, 
        env_type: str, 
        user_id: int, 
        training_id: int
    ) -> str:
        """生成容器名称"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"huixue-{env_type.lower()}-{user_id}-{training_id}-{timestamp}"
    
    def _ensure_image_available(self, image_name: str) -> str:
        """
        确保指定镜像在本地可用，如不存在则尝试拉取

        Args:
            image_name: 镜像名称

        Returns:
            可用的镜像名称
        """
        try:
            self.client.images.get(image_name)
            logger.debug(f"镜像已存在: {image_name}")
            return image_name
        except docker.errors.ImageNotFound:
            logger.info(f"镜像不存在，尝试拉取: {image_name}")
            self.client.images.pull(image_name)
            logger.info(f"镜像拉取成功: {image_name}")
            return image_name
        except docker.errors.APIError as e:
            logger.error(f"检查/拉取镜像失败: {image_name}, 错误: {e}")
            raise

    def _get_image_name(self, env_type: str, db: Session) -> Optional[str]:
        """从数据库获取环境类型对应的Docker镜像名称"""
        env = db.query(models.TrainingEnvironment).filter(
            models.TrainingEnvironment.environment_type == env_type.upper(),
            models.TrainingEnvironment.is_active == True
        ).first()
        
        if not env:
            logger.error(f"未找到环境类型 {env_type} 的配置")
            return None
        
        return env.docker_image
    
    def _get_or_create_named_volume(self, env_type: str, user_id: int, training_id: int) -> str:
        """
        获取或创建命名卷用于学生工作目录

        Args:
            env_type: 环境类型
            user_id: 用户ID
            training_id: 实训ID

        Returns:
            命名卷名称
        """
        volume_name = f"huixue-{env_type.lower()}-u{user_id}-t{training_id}"

        try:
            self._ensure_initialized()

            # 检查卷是否存在
            try:
                self.client.volumes.get(volume_name)
                logger.debug(f"命名卷已存在: {volume_name}")
            except docker.errors.NotFound:
                # 创建新卷
                self.client.volumes.create(
                    name=volume_name,
                    driver="local",
                    labels={
                        "huixue.env_type": env_type,
                        "huixue.user_id": str(user_id),
                        "huixue.training_id": str(training_id),
                        "huixue.created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                logger.info(f"创建命名卷: {volume_name}")

            return volume_name

        except Exception as e:
            logger.warning(f"创建命名卷失败，回退到临时卷: {e}")
            # 回退：返回临时卷名称
            import uuid
            return f"huixue-temp-{uuid.uuid4().hex[:8]}"

    def _prepare_volumes(
        self,
        env_type: str,
        user_id: int,
        training_id: int,
        training_name: Optional[str] = None,
        training_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, str]]:
        """准备卷挂载配置"""
        volumes = {}
        dataset_sql_rel_files = []

        # 使用命名卷代替绑定挂载（避免Docker Desktop文件共享问题）
        # 挂载到 /home/jovyan/work 因为这是Jupyter的默认工作目录
        volume_name = self._get_or_create_named_volume(env_type, user_id, training_id)
        volumes[volume_name] = {"bind": "/home/jovyan/work", "mode": "rw"}
        
        resource_dir: Optional[Path] = None
        if training_name:
            resource_dir = self._resolve_training_resource_dir(training_name)
            if training_metadata is not None:
                training_metadata["resource_dir"] = resource_dir
        
        # 如果是实训环境，挂载数据集和模板
        if resource_dir and resource_dir.exists():
            # 数据集目录
            datasets_dir = resource_dir / "datasets"
            if datasets_dir.exists():
                volumes[str(datasets_dir.resolve())] = {"bind": "/datasets", "mode": "ro"}
                dataset_sql_rel_files = [
                    str(Path("datasets") / sql_file.name)
                    for sql_file in sorted(datasets_dir.glob("*.sql"))
                ]
                
                # 如果训练元数据中指定了数据集引用，优先匹配这些文件
                if training_metadata is not None:
                    preferred_refs = training_metadata.get("superset_dataset_refs") or []
                    normalized_map = {
                        Path(rel_path).as_posix(): rel_path for rel_path in dataset_sql_rel_files
                    }
                    
                    if preferred_refs:
                        filtered: List[str] = []
                        missing: List[str] = []
                        for ref in preferred_refs:
                            if not isinstance(ref, str):
                                continue
                            ref_key = Path(ref).as_posix()
                            matched = normalized_map.get(ref_key) or normalized_map.get(ref_key.lstrip("./"))
                            if matched:
                                filtered.append(matched)
                            else:
                                missing.append(ref_key)
                        if filtered:
                            dataset_sql_rel_files = filtered
                        if missing:
                            logger.warning(
                                "实训 %s 指定的数据集文件不存在: %s",
                                training_metadata.get("training_id"),
                                ", ".join(missing),
                            )
                    training_metadata["bi_dataset_sql_rel_files"] = dataset_sql_rel_files
            
            # Jupyter模板目录（仅Jupyter环境）
            if env_type.upper() == "JUPYTER":
                jupyter_dir = resource_dir / "jupyter"
                if jupyter_dir.exists():
                    volumes[str(jupyter_dir.resolve())] = {"bind": "/templates", "mode": "ro"}
            
            # AI设计器模板目录（KNIME/Orange）
            if env_type.upper() in ["TEMPO_AI", "VDI", "VDI_PYCHARM"]:
                ai_templates_dir = resource_dir / "ai_templates"
                if ai_templates_dir.exists():
                    volumes[str(ai_templates_dir.resolve())] = {"bind": "/templates", "mode": "ro"}
                
                # KNIME工作流文件
                knime_dir = resource_dir / "knime"
                if knime_dir.exists():
                    volumes[str(knime_dir.resolve())] = {"bind": "/knime-workspace", "mode": "rw"}
        
        if env_type.upper() == "TEMPO_BI":
            superset_config_path = None
            if settings.SUPERSET_CONFIG_PATH:
                candidate = Path(settings.SUPERSET_CONFIG_PATH).expanduser()
                if candidate.exists():
                    superset_config_path = candidate
                else:
                    logger.warning(f"Superset配置文件未找到: {candidate}")
            if not superset_config_path and DEFAULT_SUPERSET_CONFIG.exists():
                superset_config_path = DEFAULT_SUPERSET_CONFIG
            if superset_config_path:
                volumes[str(superset_config_path.resolve())] = {
                    "bind": "/app/pythonpath/superset_config_embed.py",
                    "mode": "ro"
                }
            else:
                logger.warning("未找到Superset配置文件，无法挂载自定义iframe配置")

            if resource_dir and resource_dir.exists():
                bi_mount_path = f"/bi_resources/{training_id}"
                volumes[str(resource_dir.resolve())] = {"bind": bi_mount_path, "mode": "ro"}
                if training_metadata is not None:
                    training_metadata["bi_resource_mount"] = bi_mount_path
                    training_metadata["bi_templates_dir"] = str(Path(bi_mount_path) / "bi_templates")
                    if dataset_sql_rel_files:
                        resolved_sql_paths = [
                            f"{bi_mount_path}/{rel_path}"
                            for rel_path in dataset_sql_rel_files
                        ]
                        training_metadata["bi_dataset_sql_files"] = resolved_sql_paths
                        training_metadata["dataset_sql_path"] = resolved_sql_paths[0]
                    else:
                        training_metadata["bi_dataset_sql_files"] = []
                        training_metadata.pop("dataset_sql_path", None)
                    training_metadata.setdefault("bi_dataset_database", "examples")

        # HDFS持久化挂载（如果启用）
        try:
            hdfs_svc = get_hdfs_service()
            if hdfs_svc.enabled:
                hdfs_volumes = hdfs_svc.get_volume_mounts(user_id, training_id, env_type)
                volumes.update(hdfs_volumes)
                logger.info(f"添加HDFS持久化挂载: {list(hdfs_volumes.keys())}")
        except Exception as e:
            logger.warning(f"获取HDFS挂载配置失败: {e}")

        return volumes

    def _resolve_training_resource_dir(self, training_name: Optional[str]) -> Optional[Path]:
        """根据实训名称定位资源目录"""
        if not training_name:
            return None
        
        candidates = [
            settings.resource_base_path / "实训资源" / training_name,
            settings.resource_base_path / training_name,
        ]
        
        for path in candidates:
            if path.exists():
                return path
        return None
        
        return volumes
    
    def _prepare_env_vars(
        self, 
        env_type: str, 
        user_id: int, 
        training_id: int,
        training_metadata: Optional[Dict[str, Any]] = None,
        init_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """准备环境变量"""
        env_vars = {
            "USER_ID": str(user_id),
            "TRAINING_ID": str(training_id),
        }
        
        if env_type.upper() == "JUPYTER":
            # 生成Jupyter token
            token = secrets.token_urlsafe(32)
            env_vars["JUPYTER_TOKEN"] = token
            env_vars["JUPYTER_ENABLE_LAB"] = "yes"
            env_vars["JUPYTER_PORT"] = "8888"
        
        elif env_type.upper() == "TEMPO_BI":  # Apache Superset
            # Superset需要安全的SECRET_KEY才能启动
            # 生成一个安全的SECRET_KEY（至少42字符）
            superset_secret_key = secrets.token_urlsafe(42)
            env_vars["SUPERSET_SECRET_KEY"] = superset_secret_key
            env_vars["SUPERSET_EMBED_SECRET"] = settings.SUPERSET_EMBED_SECRET
            env_vars["SUPERSET_PORT"] = "8088"
            env_vars["FLASK_ENV"] = "development"
            # 加载示例数据，让学生可以立即开始BI实训
            env_vars["SUPERSET_LOAD_EXAMPLES"] = "yes"  # 加载示例数据（包括示例数据集和仪表板）
            env_vars["SUPERSET_PARENT_ORIGINS"] = settings.BI_PARENT_ORIGIN
            env_vars["SUPERSET_CONFIG_PATH"] = "/app/pythonpath/superset_config_embed.py"
            if training_metadata:
                resource_mount = training_metadata.get("bi_resource_mount")
                if resource_mount:
                    env_vars["BI_RESOURCES_PATH"] = resource_mount
                dashboard_id = training_metadata.get("superset_dashboard_id")
                if dashboard_id:
                    env_vars["SUPERSET_DEFAULT_DASHBOARD_ID"] = str(dashboard_id)
        
        elif env_type.upper() == "TEMPO_AI":  # KNIME VDI
            vnc_pw = secrets.token_urlsafe(16)
            env_vars["VNC_PW"] = vnc_pw
            env_vars["VNC_RESOLUTION"] = "1280x720"
            env_vars["DISPLAY"] = ":1"

        elif env_type.upper() == "VDI" or env_type.upper().startswith("VDI_"):
            vnc_pw = secrets.token_urlsafe(16)
            env_vars["VNC_PW"] = vnc_pw
            env_vars["VNC_RESOLUTION"] = "1280x720"
            env_vars["DISPLAY"] = ":1"

        # V3.0 新增：注入资源同步相关的环境变量
        if init_config:
            env_vars.update(self._inject_resource_env_vars(init_config))

        # HDFS持久化环境变量（如果启用）
        try:
            hdfs_svc = get_hdfs_service()
            if hdfs_svc.enabled:
                hdfs_env = hdfs_svc.get_env_vars(user_id, training_id)
                env_vars.update(hdfs_env)
                logger.info(f"添加HDFS环境变量: {list(hdfs_env.keys())}")
        except Exception as e:
            logger.warning(f"获取HDFS环境变量失败: {e}")

        return env_vars

    def _inject_resource_env_vars(self, init_config: Dict[str, Any]) -> Dict[str, str]:
        """
        注入资源同步相关的环境变量 (V3.0)

        Args:
            init_config: 环境初始化配置

        Returns:
            环境变量字典
        """
        env_vars = {}

        # 设置环境类型
        env_vars["ENV_TYPE"] = init_config.get("env_type", "JUPYTER")

        # 设置资源基础URL
        if "env_vars" in init_config:
            resource_env_vars = init_config["env_vars"]

            # 复制资源相关的环境变量
            for key in ["RESOURCE_BASE_URL", "SQL_SCRIPT_URLS", "DASHBOARD_TEMPLATE_URL", "DATASET_URLS"]:
                if key in resource_env_vars:
                    env_vars[key] = resource_env_vars[key]

        # 设置初始化脚本URL
        init_script_url = init_config.get("init_script_url")
        if init_script_url:
            env_vars["INIT_SCRIPT_URL"] = init_script_url

        # 设置资源清单（JSON格式）
        if "resources" in init_config:
            import json
            try:
                env_vars["RESOURCE_MANIFEST"] = json.dumps(init_config["resources"])
            except (TypeError, ValueError) as e:
                logger.warning(f"序列化资源清单失败: {e}")

        logger.info(f"注入资源环境变量: {list(env_vars.keys())}")
        return env_vars
    
    def _get_container_port(self, env_type: str) -> int:
        """根据环境类型获取容器内部端口"""
        port_mapping = {
            "JUPYTER": 8888,
            "TEMPO_BI": 8088,  # Superset
            "TEMPO_AI": 6901,   # VNC Web端口
            "VDI_PYCHARM": 6901,
        }
        return port_mapping.get(env_type.upper(), 8080)
    
    def get_existing_container(
        self, 
        user_id: int, 
        training_id: int, 
        env_type: str,
        db: Session
    ) -> Optional[str]:
        """查询是否已有运行中的容器"""
        self._ensure_initialized()
        
        container_process = db.query(models.ContainerProcess).filter(
            models.ContainerProcess.user_id == user_id,
            models.ContainerProcess.training_id == training_id,
            models.ContainerProcess.environment_type == env_type.upper(),
            models.ContainerProcess.status == "running"
        ).first()
        
        if container_process:
            # 验证容器确实在运行
            try:
                container = self.client.containers.get(container_process.container_id)
                if container.status == "running":
                    return container_process.container_id
                else:
                    # 容器已停止，更新数据库状态
                    container_process.status = "stopped"
                    db.commit()
            except docker.errors.NotFound:
                # 容器不存在，更新数据库状态
                container_process.status = "stopped"
                db.commit()
        
        return None
    
    def start_container(
        self,
        env_type: str,
        user_id: int,
        training_id: int,
        training_name: Optional[str] = None,
        db: Optional[Session] = None,
        existing_record_id: Optional[int] = None,
        training_metadata: Optional[Dict[str, Any]] = None,
        init_config: Optional[Dict[str, Any]] = None,  # V3.0 新增：环境初始化配置
        force_swarm: bool = False  # 默认不使用Swarm模式
    ) -> Tuple[str, int]:
        """
        启动容器

        优先使用Docker Swarm模式（如果可用），实现：
        1. 强制调度到worker节点（高算力服务器2/3）
        2. 使用NFS共享存储挂载学生工作目录
        3. 动态分配宿主机端口
        4. 资源限制（CPU/内存）

        Args:
            existing_record_id: 如果提供，则更新现有记录而不是创建新记录
            force_swarm: 是否强制使用Swarm模式（默认True）

        Returns:
            tuple: (container_id/service_id, host_port)
        """
        logger.info(f"[START_CONTAINER] 开始启动容器: env_type={env_type}, user_id={user_id}, training_id={training_id}, force_swarm={force_swarm}")
        logger.info(f"[START_CONTAINER] Docker fallback模式: {self._docker_fallback}")
        logger.info(f"[START_CONTAINER] Docker初始化状态: _initialized={self._initialized}, _swarm_initialized={getattr(self, '_swarm_initialized', 'N/A')}")

        # 检查是否处于fallback模式（Docker不可用）
        if self._docker_fallback:
            logger.warning(f"Docker fallback模式：模拟启动{env_type}容器")
            # 返回模拟的容器ID和端口
            import uuid
            mock_container_id = f"mock-{uuid.uuid4().hex[:12]}"
            mock_host_port = random.randint(30000, 30100)
            logger.info(f"Fallback: 返回模拟容器 {mock_container_id}, 端口 {mock_host_port}")
            return mock_container_id, mock_host_port

        # 尝试使用Swarm模式
        if force_swarm:
            try:
                # 确保Swarm客户端已初始化
                self._ensure_swarm_initialized()
                # 检查Swarm是否可用
                info = self.client.info() if self.client else None
                logger.info(f"[START_CONTAINER] Swarm检查: client={self.client is not None}, info={info is not None}")
                if info:
                    swarm_state = info.get('Swarm', {}).get('LocalNodeState', 'unknown')
                    logger.info(f"[START_CONTAINER] Swarm状态: {swarm_state}")
                if info and info.get('Swarm', {}).get('LocalNodeState') == 'active':
                    logger.info(f"使用Swarm模式启动{env_type}容器（用户:{user_id}, 实训:{training_id}）")
                    return self.start_swarm_service(
                        env_type=env_type,
                        user_id=user_id,
                        training_id=training_id,
                        training_name=training_name,
                        db=db,
                        training_metadata=training_metadata,
                        init_config=init_config
                    )
                else:
                    logger.warning(f"[START_CONTAINER] Swarm不可用，将使用普通容器模式")
            except Exception as e:
                logger.warning(f"Swarm模式启动失败，回退到普通模式: {e}")

        # 回退到普通容器模式
        logger.info(f"使用普通容器模式启动{env_type}容器")
        self._ensure_initialized()
        logger.info(f"[START_CONTAINER] Docker客户端初始化完成: client={self.client is not None}")
        
        # 检查是否已有运行中的容器
        if db:
            existing_id = self.get_existing_container(user_id, training_id, env_type, db)
            if existing_id:
                container = self.client.containers.get(existing_id)
                # 获取端口映射
                ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
                container_port = self._get_container_port(env_type)
                host_port = None
                
                for port_config in ports.values():
                    if port_config:
                        # 找到映射的端口
                        host_port = int(port_config[0]["HostPort"])
                        break
                
                if host_port:
                    logger.info(f"复用现有容器 {existing_id}")
                    return existing_id, host_port
        
        # 从数据库获取镜像名称
        if not db:
            raise ValueError("数据库会话是必需的")

        image_name = self._get_image_name(env_type, db)
        if not image_name:
            # 如果数据库没有配置，使用各环境类型的默认镜像
            env_upper = env_type.upper()
            if env_upper == "JUPYTER":
                image_name = "huixue-jupyter:latest"
                logger.info(f"使用默认Jupyter镜像: {image_name}")
            elif env_upper == "TEMPO_BI":
                # 优先使用本地镜像，失败时回退到Docker Hub
                image_name = "huixue-superset:latest"
                logger.warning("TrainingEnvironment表无TEMPO_BI配置，使用默认Superset镜像")
            elif env_upper == "TEMPO_AI":
                image_name = "cfprot/knime:latest"
                logger.warning("TrainingEnvironment表无TEMPO_AI配置，使用默认KNIME镜像")
            elif env_upper in ("DESKTOP", "VDI"):
                image_name = "consol/ubuntu-xfce-vnc:latest"
                logger.warning(f"TrainingEnvironment表无{env_upper}配置，使用默认VNC镜像")
            else:
                raise ValueError(f"未找到环境类型 {env_type} 的Docker镜像配置")
        
        # 准备容器配置
        container_name = self._generate_container_name(env_type, user_id, training_id)
        volumes = self._prepare_volumes(
            env_type, user_id, training_id, training_name, training_metadata=training_metadata
        )
        env_vars = self._prepare_env_vars(
            env_type,
            user_id,
            training_id,
            training_metadata=training_metadata,
            init_config=init_config,
        )
        container_port = self._get_container_port(env_type)
        host_port = None

        # 确保TEMPO_BI的Superset镜像存在，如不存在则尝试拉取
        if env_type.upper() == "TEMPO_BI":
            try:
                self._ensure_image_available(image_name)
            except Exception as img_err:
                logger.warning(f"无法拉取镜像{image_name}，尝试apache/superset:latest: {img_err}")
                try:
                    image_name = self._ensure_image_available("apache/superset:latest")
                except Exception as fallback_err:
                    logger.error(f"Superset镜像均不可用，容器将无法正常启动: {fallback_err}")
                    # 不抛出异常，继续让 containers.run() 失败并记录

        # 为Jupyter容器准备自定义命令（包含CSP配置）
        command = None
        if env_type.upper() == "JUPYTER":
            csp_origins = "'self' http://localhost:3000 http://100.74.141.3:3000 http://localhost:3001 http://localhost:8000"
            command = [
                "jupyter", "notebook",
                "--ip=0.0.0.0",
                "--port=8888",
                f"--NotebookApp.token={env_vars.get('JUPYTER_TOKEN', 'huixue_token')}",
                "--allow-root",
                "--NotebookApp.disable_check_xsrf=True",
                f"--ServerApp.tornado_settings={{'headers': {{'Content-Security-Policy': \"frame-ancestors {csp_origins}\"}}}}"
            ]

        try:
            last_error = None
            for attempt in range(5):
                host_port = self._get_available_port()
                ports = {f"{container_port}/tcp": host_port}
                
                try:
                    # 启动容器
                    container = self.client.containers.run(
                        image=image_name,
                        name=container_name,
                        detach=True,
                        ports=ports,
                        volumes=volumes,
                        environment=env_vars,
                        network=settings.DOCKER_NETWORK,
                        remove=False,  # 不自动删除，由我们管理
                        command=command,  # Jupyter自定义命令（包含CSP）
                        mem_limit='4g',  # 限制最大内存为4GB
                        mem_reservation='512m',  # 预留512MB内存
                        memswap_limit='4g',  # 禁用swap，内存+swap最多4GB
                        cpu_period=100000,  # CPU调度周期
                        cpu_quota=150000,  # 1.5核 (150000/100000)
                    )
                    break
                except docker.errors.APIError as api_error:
                    error_text = str(api_error).lower()
                    last_error = api_error
                    if "port is already allocated" in error_text or "address already in use" in error_text:
                        logger.warning(
                            f"端口 {host_port} 已被占用，尝试重新分配 (attempt {attempt + 1}/5)"
                        )
                        continue
                    raise
            else:
                # 所有尝试都失败
                raise last_error or RuntimeError("端口分配失败")
            
            container_id = container.id
            
            # 初始化Jupyter工作目录：复制实训初始文件到容器
            if env_type.upper() == "JUPYTER":
                try:
                    self._initialize_jupyter_workdir(container, training_id, db)
                except Exception as e:
                    logger.warning(f"初始化Jupyter工作目录失败: {e}，容器将继续运行")
            
            # 初始化Superset环境：执行数据库初始化
            if env_type.upper() == "TEMPO_BI":
                try:
                    self._initialize_superset(container, training_metadata=training_metadata)
                except Exception as e:
                    logger.warning(f"初始化Superset失败: {e}，容器将继续运行")
            
            # 初始化KNIME/VNC环境：在KNIME启动前复制工作流文件
            # 关键：必须在KNIME启动前复制文件，否则KNIME无法检测到新文件
            if env_type.upper() == "TEMPO_AI":
                try:
                    # 立即初始化，不等待，确保在KNIME启动前完成
                    # KNIME在容器启动后5秒启动，我们需要在这之前复制文件
                    self._initialize_knime(container, training_id, training_name, db)
                except Exception as e:
                    logger.warning(f"初始化KNIME失败: {e}，容器将继续运行")
            if existing_record_id and db:
                # 更新现有记录
                container_process = db.query(models.ContainerProcess).filter(
                    models.ContainerProcess.id == existing_record_id
                ).first()
                if container_process:
                    container_process.container_id = container_id
                    container_process.container_name = container_name
                    container_process.port = host_port
                    container_process.status = "running"
                    container_process.last_activity = datetime.now(timezone.utc)
                    db.commit()
            elif db:
                # 创建新记录
                container_process = models.ContainerProcess(
                    container_id=container_id,
                    container_name=container_name,
                    user_id=user_id,
                    training_id=training_id,
                    environment_type=env_type.upper(),
                    status="running",
                    port=host_port,
                    start_time=datetime.now(timezone.utc),
                    last_activity=datetime.now(timezone.utc),
                )
                db.add(container_process)
                db.commit()
            
            logger.info(f"容器启动成功: {container_id}, 端口: {host_port}")
            return container_id, host_port
            
        except Exception as e:
            logger.error(f"启动容器失败: {e}")
            raise
    
    def _initialize_jupyter_workdir(self, container, training_id: int, db: Session):
        """
        初始化Jupyter工作目录，将实训初始文件复制到容器的/work目录
        
        Args:
            container: Docker容器对象
            training_id: 实训ID
            db: 数据库会话
        """
        import json
        import tarfile
        import io
        
        try:
            # 等待容器完全启动
            import time
            time.sleep(2)
            
            # 从数据库获取实训的Jupyter文件（不检查creator_id）
            jupyter_files = db.query(models.TrainingJupyterFile).filter(
                models.TrainingJupyterFile.training_id == training_id
            ).order_by(models.TrainingJupyterFile.is_main_file.desc()).all()
            
            # 如果没有Jupyter文件记录，尝试从模板目录复制或创建默认notebook
            if not jupyter_files:
                # 检查容器中是否有/templates目录
                result = container.exec_run("test -d /templates", user="jovyan")
                if result.exit_code == 0:
                    # 使用root权限复制模板文件到工作目录
                    container.exec_run("mkdir -p /home/jovyan/work", user="root")
                    container.exec_run("cp -r /templates/* /home/jovyan/work/", user="root")
                    # 确保jovyan用户有权限访问 - 使用chmod因为chown在Docker Desktop上可能不工作
                    container.exec_run("chmod -R 755 /home/jovyan/work && chown -R jovyan:users /home/jovyan/work 2>/dev/null || true", user="root")
                    logger.info(f"从模板目录复制文件到工作目录")
                else:
                    # 创建一个默认的notebook
                    default_notebook = {
                        "cells": [
                            {
                                "cell_type": "markdown",
                                "metadata": {},
                                "source": ["# 编码式实训\n\n请在此处开始编写你的代码。"]
                            },
                            {
                                "cell_type": "code",
                                "execution_count": None,
                                "metadata": {},
                                "outputs": [],
                                "source": ["# 请在此处编写你的代码\nprint('Hello, World!')"]
                            }
                        ],
                        "metadata": {
                            "kernelspec": {
                                "display_name": "Python 3",
                                "language": "python",
                                "name": "python3"
                            },
                            "language_info": {
                                "name": "python",
                                "version": "3.9.0"
                            }
                        },
                        "nbformat": 4,
                        "nbformat_minor": 4
                    }
                    
                    # 创建tar文件
                    tar_stream = io.BytesIO()
                    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                        notebook_json = json.dumps(default_notebook, ensure_ascii=False, indent=2)
                        notebook_bytes = notebook_json.encode('utf-8')
                        # 创建work目录结构
                        tarinfo_dir = tarfile.TarInfo(name="work")
                        tarinfo_dir.type = tarfile.DIRTYPE
                        tar.addfile(tarinfo_dir)
                        tarinfo = tarfile.TarInfo(name="work/main.ipynb")
                        tarinfo.size = len(notebook_bytes)
                        tar.addfile(tarinfo, io.BytesIO(notebook_bytes))
                    
                    tar_stream.seek(0)
                    # 将文件复制到/home/jovyan/work目录（Jupyter的工作目录）
                    container.put_archive("/home/jovyan", tar_stream)
                    # 确保目录权限正确 - 使用chmod因为chown在Docker Desktop上可能不工作
                    container.exec_run("chmod -R 755 /home/jovyan/work && chown -R jovyan:users /home/jovyan/work 2>/dev/null || true", user="root")
                    logger.info(f"创建默认notebook文件: main.ipynb")
                return
            
            # 将Jupyter文件复制到容器
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                # 创建work目录结构
                tarinfo_dir = tarfile.TarInfo(name="work")
                tarinfo_dir.type = tarfile.DIRTYPE
                tar.addfile(tarinfo_dir)
                
                for jupyter_file in jupyter_files:
                    file_name = jupyter_file.file_name or "notebook.ipynb"
                    file_content = jupyter_file.file_content or ""
                    
                    # 如果file_content是字符串，尝试解析为JSON
                    if isinstance(file_content, str):
                        try:
                            # 验证是否为有效的JSON（notebook格式）
                            json.loads(file_content)
                            content_bytes = file_content.encode('utf-8')
                        except json.JSONDecodeError:
                            # 如果不是JSON，作为纯文本处理
                            content_bytes = file_content.encode('utf-8')
                    else:
                        # 如果是字典，转换为JSON字符串
                        content_bytes = json.dumps(file_content, ensure_ascii=False, indent=2).encode('utf-8')
                    
                    tarinfo = tarfile.TarInfo(name=f"work/{file_name}")
                    tarinfo.size = len(content_bytes)
                    tar.addfile(tarinfo, io.BytesIO(content_bytes))
            
            tar_stream.seek(0)
            # 将文件复制到/home/jovyan/work目录（Jupyter的工作目录）
            container.put_archive("/home/jovyan", tar_stream)
            # 确保目录权限正确 - 使用chmod因为chown在Docker Desktop上可能不工作
            container.exec_run("chmod -R 755 /home/jovyan/work && chown -R jovyan:users /home/jovyan/work 2>/dev/null || true", user="root")
            logger.info(f"成功初始化Jupyter工作目录，复制了 {len(jupyter_files)} 个文件")
            
        except Exception as e:
            logger.error(f"初始化Jupyter工作目录时出错: {e}")
            # 不抛出异常，允许容器继续运行
            pass
    
    def _initialize_superset(self, container, training_metadata: Optional[Dict[str, Any]] = None):
        """
        初始化Superset环境，等待服务就绪并创建管理员账户
        
        Args:
            container: Docker容器对象
        """
        import time
        
        try:
            # 等待容器完全启动
            time.sleep(5)
            
            # Superset容器启动时会自动执行数据库初始化
            # 我们只需要等待服务就绪即可
            # 注意：apache/superset:latest 镜像在启动时会自动执行初始化
            
            # 检查Superset是否就绪（通过健康检查）
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    # 检查容器内是否有superset进程
                    result = container.exec_run(
                        "ps aux | grep -i superset | grep -v grep || exit 1",
                        user="superset"
                    )
                    if result.exit_code == 0:
                        logger.info("Superset进程已启动")
                        # 再等待几秒让服务完全就绪
                        time.sleep(3)
                        break
                except Exception:
                    pass
                
                time.sleep(2)
                if attempt % 5 == 0:
                    logger.debug(f"等待Superset启动... ({attempt + 1}/{max_attempts})")
            
            # 创建管理员账户（如果不存在）
            try:
                logger.info("创建Superset管理员账户...")
                result = container.exec_run(
                    "superset fab create-admin --username admin --firstname Admin --lastname User --email admin@example.com --password admin",
                    user="superset"
                )
                if result.exit_code == 0:
                    output = result.output.decode('utf-8', errors='ignore')
                    if "created" in output.lower() or "exists" in output.lower():
                        logger.info("Superset管理员账户已创建或已存在")
                    else:
                        logger.warning(f"创建管理员账户输出: {output[:200]}")
                else:
                    logger.warning(f"创建管理员账户失败，退出码: {result.exit_code}")
            except Exception as e:
                logger.warning(f"创建管理员账户时出错: {e}")
            
            # 创建学生账户（用于实训）
            try:
                logger.info("创建Superset学生账户...")
                result = container.exec_run(
                    "superset fab create-user --username student --firstname Student --lastname User --email student@example.com --password student123 --role Gamma",
                    user="superset"
                )
                if result.exit_code == 0:
                    output = result.output.decode('utf-8', errors='ignore')
                    if "created" in output.lower() or "exists" in output.lower():
                        logger.info("Superset学生账户已创建或已存在")
                    else:
                        logger.warning(f"创建学生账户输出: {output[:200]}")
                else:
                    # 如果创建失败（可能是用户已存在），尝试重置密码
                    logger.info("尝试重置学生账户密码...")
                    container.exec_run(
                        "superset fab reset-password --username student --password student123",
                        user="superset"
                    )
                    # 确保角色正确
                    container.exec_run(
                        "superset fab set-user-role --username student --role Gamma",
                        user="superset"
                    )
            except Exception as e:
                logger.warning(f"创建学生账户时出错: {e}")
            
            # 创建嵌入服务账号（用于 Guest Token 签发）
            try:
                embed_username = settings.SUPERSET_EMBED_USERNAME
                embed_password = settings.SUPERSET_EMBED_PASSWORD
                embed_email = settings.SUPERSET_EMBED_EMAIL
                embed_firstname = settings.SUPERSET_EMBED_FIRSTNAME
                embed_lastname = settings.SUPERSET_EMBED_LASTNAME
                
                if embed_username and embed_username not in {"admin", "student"}:
                    logger.info("创建Superset嵌入服务账号...")
                    command = [
                        "superset",
                        "fab",
                        "create-user",
                        "--username", embed_username,
                        "--firstname", embed_firstname,
                        "--lastname", embed_lastname,
                        "--email", embed_email,
                        "--password", embed_password,
                        "--role", "Admin",
                    ]
                    result = container.exec_run(command, user="superset")
                    output = result.output.decode('utf-8', errors='ignore') if result.output else ""
                    if result.exit_code == 0:
                        logger.info("Superset嵌入服务账号已创建或已存在")
                        if output:
                            logger.debug(output.strip())
                    else:
                        lowered = output.lower()
                        if "already exists" in lowered or "existing user" in lowered:
                            logger.info("Superset嵌入服务账号已存在，跳过创建")
                        else:
                            logger.warning(f"创建嵌入服务账号失败，退出码: {result.exit_code}, 输出: {output[:200]}")
                else:
                    logger.debug("嵌入服务账号与默认管理员相同，跳过单独创建")
            except Exception as e:
                logger.warning(f"创建嵌入服务账号时出错: {e}")
            
            # 初始化数据库和权限
            try:
                logger.info("初始化Superset数据库...")
                container.exec_run("superset db upgrade", user="superset")
                logger.info("初始化Superset权限...")
                container.exec_run("superset init", user="superset")
                
                # 加载示例数据（如果环境变量设置了但还没有加载）
                # 注意：如果SUPERSET_LOAD_EXAMPLES=yes，容器启动时会自动加载
                # 但为了确保加载完成，我们再次检查并加载
                logger.info("检查并加载Superset示例数据...")
                try:
                    # 检查是否已有示例数据集
                    result = container.exec_run(
                        "superset list-datasets | grep -i 'examples' || echo 'no_examples'",
                        user="superset"
                    )
                    output = result.output.decode('utf-8', errors='ignore')
                    
                    # 如果没有示例数据，手动加载
                    if 'no_examples' in output or not output.strip():
                        logger.info("未找到示例数据，开始加载...")
                        # 加载示例数据（这会创建示例数据集和仪表板）
                        container.exec_run(
                            "superset load-examples",
                            user="superset"
                        )
                        logger.info("示例数据加载完成")
                    else:
                        logger.info("示例数据已存在，跳过加载")
                except Exception as e:
                    logger.warning(f"加载示例数据时出错（可能已自动加载）: {e}")
            except Exception as e:
                logger.warning(f"初始化数据库/权限时出错: {e}")
            
            logger.info("Superset初始化完成")
            self._import_bi_assets(container, training_metadata)
            
        except Exception as e:
            logger.error(f"初始化Superset时出错: {e}")
            # 不抛出异常，允许容器继续运行
            pass

    def _exec_python_script(
        self,
        container,
        script: str,
        args: Optional[List[str]] = None,
        user: str = "superset",
    ) -> Tuple[int, str]:
        """在容器内创建并执行临时Python脚本"""
        token = secrets.token_hex(4)
        remote_dir = "/tmp"
        filename = f"bi_helper_{token}.py"
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            data = script.encode("utf-8")
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(data)
            tar.addfile(tarinfo, io.BytesIO(data))
        tar_stream.seek(0)
        container.put_archive(remote_dir, tar_stream.getvalue())
        python_bin = "/app/.venv/bin/python"
        cmd = [python_bin, f"{remote_dir}/{filename}"]
        if args:
            cmd.extend(args)
        result = container.exec_run(cmd, user=user)
        output = result.output.decode("utf-8", errors="ignore") if result.output else ""
        if result.exit_code != 0:
            logger.warning(
                "执行容器Python脚本失败(exit=%s): %s",
                result.exit_code,
                output[:400],
            )
        return result.exit_code, output
    
    def _apply_dataset_sql_scripts(
        self,
        container,
        training_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """执行BI资源中的SQL脚本，创建/填充示例数据表"""
        if not training_metadata:
            return
        sql_files: List[str] = training_metadata.get("bi_dataset_sql_files") or []
        if not sql_files:
            return
        
        script = textwrap.dedent(
            """
            import sqlite3
            import re
            import sys
            from pathlib import Path
            
            def normalize_sql(content: str) -> str:
                content = content.replace("`", "")
                content = re.sub(r" COMMENT '.*?'", "", content)
                content = re.sub(r"\\) ENGINE=.*?;", ");", content, flags=re.S)
                content = re.sub(r"COLLATE\\s+\\w+", "", content)
                return content
            
            def apply_sql(sql_path: str) -> None:
                path = Path(sql_path)
                if not path.exists():
                    return
                raw = path.read_text(encoding="utf-8")
                content = normalize_sql(raw)
                if not content.strip():
                    return
                conn = sqlite3.connect("/app/superset_home/examples.db")
                conn.executescript(content)
                conn.commit()
                conn.close()
            
            if __name__ == "__main__":
                for target in sys.argv[1:]:
                    apply_sql(target)
            """
        )
        exit_code, output = self._exec_python_script(container, script, args=sql_files)
        if exit_code == 0:
            logger.info("BI示例数据表脚本执行完成: %s", ", ".join(sql_files))
        else:
            logger.warning("执行BI数据脚本失败: %s", output[:400])
    
    def _import_bi_dashboard_from_json(
        self,
        container,
        template_path: str,
        training_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, str]:
        """使用JSON模板在Superset内构建数据集/图表/仪表盘"""
        database_name = "examples"
        if training_metadata:
            database_name = training_metadata.get("bi_dataset_database") or database_name
        
        script = textwrap.dedent(
            """
            import json
            import os
            import sys
            from pathlib import Path

            from superset.app import create_app
            from sqlalchemy import inspect

            def load_params(raw_params):
                if isinstance(raw_params, str):
                    try:
                        return json.loads(raw_params)
                    except Exception:
                        return {}
                return raw_params or {}

            def ensure_json_string(raw):
                if isinstance(raw, str):
                    try:
                        json.loads(raw)
                        return raw
                    except Exception:
                        return "{}"
                return json.dumps(raw or {})

            def load_positions(raw):
                if isinstance(raw, str):
                    try:
                        return json.loads(raw)
                    except Exception:
                        return {}
                return raw or {}
            
            def ensure_dashboard_layout(positions, chart_id_map):
                def has_root(nodes):
                    for node in nodes.values():
                        if isinstance(node, dict) and node.get("type") == "ROOT":
                            return True
                    return False
                
                if has_root(positions):
                    for node in positions.values():
                        if isinstance(node, dict):
                            meta = node.get("meta")
                            if meta and isinstance(meta, dict):
                                old_id = meta.get("chartId")
                                if old_id in chart_id_map:
                                    meta["chartId"] = chart_id_map[old_id]
                    return positions
                
                normalized = {}
                grid_children = []
                for idx, (old_id, slice_id) in enumerate(chart_id_map.items(), start=1):
                    chart_node_id = f"CHART-{idx}"
                    row_node_id = f"ROW-{idx}"
                    grid_children.append(row_node_id)
                    chart_meta = {
                        "chartId": slice_id,
                        "width": 12,
                        "height": 8,
                    }
                    existing = positions.get(chart_node_id)
                    if isinstance(existing, dict):
                        existing_meta = existing.get("meta") or {}
                        chart_meta["width"] = existing_meta.get("width", chart_meta["width"])
                        chart_meta["height"] = existing_meta.get("height", chart_meta["height"])
                    normalized[chart_node_id] = {
                        "id": chart_node_id,
                        "type": "CHART",
                        "children": [],
                        "meta": chart_meta,
                    }
                    normalized[row_node_id] = {
                        "id": row_node_id,
                        "type": "ROW",
                        "children": [chart_node_id],
                        "meta": {"background": "BACKGROUND_TRANSPARENT"},
                    }
                normalized["GRID_ID"] = {
                    "id": "GRID_ID",
                    "type": "GRID",
                    "children": grid_children,
                }
                normalized["ROOT_ID"] = {
                    "id": "ROOT_ID",
                    "type": "ROOT",
                    "children": ["GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                }
                return normalized

            def main(template_path: str, database_name: str):
                template = Path(template_path)
                if not template.exists():
                    raise SystemExit(f"Template not found: {template_path}")
                payload = json.loads(template.read_text(encoding="utf-8"))
                app = create_app()
                with app.app_context():
                    from superset import db, security_manager
                    from superset.models.core import Database
                    from superset.connectors.sqla.models import (
                        SqlaTable,
                        TableColumn,
                        SqlMetric,
                    )
                    from superset.models.slice import Slice
                    from superset.models.dashboard import Dashboard

                    database = (
                        db.session.query(Database)
                        .filter_by(database_name=database_name)
                        .one_or_none()
                    )
                    if not database:
                        database = Database(database_name=database_name)
                        database.set_sqlalchemy_uri(
                            "sqlite:////app/superset_home/examples.db"
                        )
                        db.session.add(database)
                        db.session.commit()

                    datasets = payload.get("datasets") or []
                    fallback_table = (
                        payload.get("table_name")
                        or (payload.get("dashboard") or {}).get("table_name")
                        or "tt_ai_purchase_funds"
                    )
                    if not datasets:
                        datasets = [
                            {
                                "table_name": fallback_table,
                                "columns": [],
                                "metrics": [],
                            }
                        ]
                    dataset_def = datasets[0]
                    table_name = dataset_def.get("table_name") or fallback_table
                    if not table_name:
                        raise SystemExit("Dataset missing table_name")

                    dataset = (
                        db.session.query(SqlaTable)
                        .filter_by(table_name=table_name, database_id=database.id)
                        .one_or_none()
                    )
                    if not dataset:
                        dataset = SqlaTable(table_name=table_name, database=database)
                    else:
                        dataset.columns = []
                        dataset.metrics = []
                        db.session.flush()
                    dataset.database = database
                    dataset.schema = dataset_def.get("schema")
                    dataset.description = dataset_def.get("description")
                    dataset.main_dttm_col = dataset_def.get("main_dttm_col")
                    column_defs = dataset_def.get("columns") or []
                    if not column_defs:
                        try:
                            with database.get_sqla_engine() as engine:
                                inspector = inspect(engine)
                                inferred_columns = inspector.get_columns(table_name)
                        except Exception:
                            inferred_columns = []
                        for column_info in inferred_columns:
                            if not column_info.get("name"):
                                continue
                            inferred_type = column_info.get("type")
                            column_defs.append(
                                {
                                    "column_name": column_info["name"],
                                    "type": str(inferred_type),
                                    "is_dttm": str(inferred_type).lower()
                                    in {"date", "datetime", "timestamp"},
                                }
                            )
                    dataset.columns = []
                    for column_def in column_defs:
                        column = TableColumn(
                            column_name=column_def.get("column_name"),
                            type=column_def.get("type"),
                            verbose_name=column_def.get("column_name"),
                            description=column_def.get("description"),
                            is_dttm=column_def.get("is_dttm", False),
                        )
                        dataset.columns.append(column)
                    metric_defs = dataset_def.get("metrics") or []
                    if not metric_defs:
                        metric_defs = [
                            {
                                "metric_name": "count",
                                "expression": "COUNT(*)",
                                "description": "Row count",
                            }
                        ]
                    dataset.metrics = []
                    for metric_def in metric_defs:
                        metric = SqlMetric(
                            metric_name=metric_def.get("metric_name"),
                            expression=metric_def.get("expression"),
                            description=metric_def.get("description"),
                        )
                        dataset.metrics.append(metric)
                    db.session.add(dataset)
                    db.session.commit()

                    owner = security_manager.find_user(
                        username=os.environ.get("SUPERSET_EMBED_USERNAME", "admin")
                    ) or security_manager.find_user("admin")

                    chart_id_map = {}
                    created_slices = []
                    for idx, chart_def in enumerate(payload.get("charts") or [], start=1):
                        slice_obj = (
                            db.session.query(Slice)
                            .filter_by(slice_name=chart_def.get("slice_name"))
                            .one_or_none()
                        )
                        params = load_params(chart_def.get("params"))
                        params["datasource"] = f"{dataset.id}__table"
                        params["datasource_id"] = dataset.id
                        params["datasource_name"] = dataset.table_name
                        params["datasource_type"] = "table"
                        params["database_name"] = database.database_name
                        params["schema"] = dataset.schema or ""
                        params_json = json.dumps(params, ensure_ascii=False)
                        if not slice_obj:
                            slice_obj = Slice(
                                slice_name=chart_def.get("slice_name"),
                                viz_type=chart_def.get("viz_type"),
                                datasource_id=dataset.id,
                                datasource_type="table",
                            )
                        slice_obj.viz_type = chart_def.get("viz_type") or slice_obj.viz_type
                        slice_obj.params = params_json
                        slice_obj.description = chart_def.get("description")
                        if owner:
                            slice_obj.owners = [owner]
                        db.session.add(slice_obj)
                        db.session.flush()
                        chart_id_map[idx] = slice_obj.id
                        created_slices.append(slice_obj)

                    dashboard_def = payload.get("dashboard") or {}
                    slug = dashboard_def.get("slug")
                    dashboard = None
                    if slug:
                        dashboard = (
                            db.session.query(Dashboard)
                            .filter_by(slug=slug)
                            .one_or_none()
                        )
                    if not dashboard:
                        dashboard = Dashboard()
                    dashboard.dashboard_title = (
                        dashboard_def.get("dashboard_title")
                        or slug
                        or "BI Dashboard"
                    )
                    dashboard.slug = slug
                    dashboard.description = dashboard_def.get("description")
                    dashboard.css = dashboard_def.get("css") or ""
                    dashboard.published = dashboard_def.get("published", True)
                    dashboard.json_metadata = ensure_json_string(
                        dashboard_def.get("json_metadata") or "{}"
                    )
                    positions_raw = load_positions(dashboard_def.get("position_json") or "{}")
                    positions = ensure_dashboard_layout(positions_raw, chart_id_map)
                    dashboard.position_json = json.dumps(positions)
                    dashboard.slices = created_slices
                    if owner:
                        dashboard.owners = [owner]
                    db.session.add(dashboard)
                    db.session.commit()
                    print(
                        json.dumps(
                            {
                                "dataset_id": dataset.id,
                                "dashboard_id": dashboard.id,
                                "chart_map": chart_id_map,
                            },
                            ensure_ascii=False,
                        )
                    )

            if __name__ == "__main__":
                template_path = sys.argv[1]
                db_name = sys.argv[2] if len(sys.argv) > 2 else "examples"
                main(template_path, db_name)
            """
        )
        return self._exec_python_script(
            container,
            script,
            args=[template_path, database_name],
        )
    
    def _import_bi_assets(self, container, training_metadata: Optional[Dict[str, Any]] = None):
        """导入BI课程的仪表盘等资源"""
        if not training_metadata:
            return
        
        resource_mount = training_metadata.get("bi_resource_mount")
        if not resource_mount:
            logger.info("当前实训未配置BI资源目录，跳过仪表盘导入")
            return
        
        dashboard_path = self._find_bi_dashboard_file(
            container,
            resource_mount,
            training_metadata.get("bi_template_path")
        )
        
        if not dashboard_path:
            logger.warning("未找到BI仪表盘模板文件，学生将看到空白Superset")
            return
        
        try:
            self._apply_dataset_sql_scripts(container, training_metadata)
        except Exception as exc:
            logger.warning(f"执行BI数据SQL脚本失败: {exc}")
        
        logger.info(f"开始导入Superset仪表盘: {dashboard_path}")
        if dashboard_path.lower().endswith(".json"):
            exit_code, output = self._import_bi_dashboard_from_json(
                container, dashboard_path, training_metadata
            )
            if exit_code == 0:
                logger.info("Superset仪表盘(JSON模板)导入完成")
                if output:
                    logger.debug(output.strip()[:400])
            else:
                logger.warning(
                    "通过JSON模板导入Superset仪表盘失败 (exit=%s): %s",
                    exit_code,
                    (output or "")[:500],
                )
        else:
            import_cmd = (
                f'superset import-dashboards --path "{dashboard_path}" --username admin'
            )
            result = container.exec_run(import_cmd, user="superset")
            if result.exit_code == 0:
                logger.info("Superset仪表盘导入完成")
                output = result.output.decode("utf-8", errors="ignore") if result.output else ""
                if output:
                    logger.debug(f"导入输出: {output[:200]}")
            else:
                output = result.output.decode("utf-8", errors="ignore") if result.output else ""
                logger.warning(f"导入Superset仪表盘失败，退出码 {result.exit_code}，输出: {output[:500]}")
                # 不抛出异常，允许容器继续运行

    def _find_bi_dashboard_file(
        self,
        container,
        resource_mount: str,
        template_relpath: Optional[str]
    ) -> Optional[str]:
        """根据配置查找仪表盘导出文件"""
        candidates = []
        if template_relpath:
            if template_relpath.startswith("/"):
                candidates.append(template_relpath)
            else:
                candidates.append(str(Path(resource_mount) / template_relpath))
        
        default_candidates = [
            Path(resource_mount) / "bi_templates" / "dashboard_export.zip",
            Path(resource_mount) / "bi_templates" / "dashboard_export.json",
            Path(resource_mount) / "bi_templates" / "dashboard.json",
            Path(resource_mount) / "dashboard_export.zip",
            Path(resource_mount) / "export" / "dashboard_export.zip",
        ]
        candidates.extend(str(path) for path in default_candidates)
        
        for path in candidates:
            if self._container_path_exists(container, path):
                return path
        return None

    def _container_path_exists(self, container, path: str) -> bool:
        """检查容器内文件是否存在"""
        try:
            result = container.exec_run(f'test -f "{path}"', user="superset")
            return result.exit_code == 0
        except Exception:
            return False
    
    def _initialize_knime(self, container, training_id: int, training_name: Optional[str], db: Session):
        """
        初始化KNIME/VNC环境，确保工作流文件正确加载
        
        Args:
            container: Docker容器对象
            training_id: 实训ID
            training_name: 实训名称（用于查找资源目录）
            db: 数据库会话
        """
        import time
        import json
        
        try:
            # 立即开始初始化，不等待KNIME启动
            # KNIME在容器启动后5秒启动，我们需要在这之前复制文件
            logger.info("立即初始化KNIME工作空间（在KNIME启动前）...")
            time.sleep(1)  # 只等待1秒，确保容器文件系统就绪
            
            # 检查容器是否正常运行
            container.reload()
            if container.status != "running":
                logger.warning(f"容器状态不是running: {container.status}")
                return
            
            # 1. KNIME实际使用 /work/knime-workspace 作为工作空间（从Dockerfile看，启动参数是 -data /work/knime-workspace）
            # 检查 /work/knime-workspace 目录
            result = container.exec_run("test -d /work/knime-workspace", user="root")
            knime_workdir_exists = result.exit_code == 0
            
            # 检查/knime-workspace目录是否存在（这是挂载点，如果资源目录存在）
            result = container.exec_run("test -d /knime-workspace", user="root")
            knime_workspace_mounted = result.exit_code == 0
            
            logger.info(f"KNIME工作空间检查: /knime-workspace挂载={knime_workspace_mounted}, /work/knime-workspace存在={knime_workdir_exists}")
            
            # 确保 /work/knime-workspace 存在
            if not knime_workdir_exists:
                container.exec_run("mkdir -p /work/knime-workspace", user="root")
                container.exec_run("chown -R 1000:1000 /work/knime-workspace", user="root")
            
            # 2. 优先从挂载的 /knime-workspace 复制文件（如果存在）
            # 这样可以确保文件在KNIME启动前就存在
            result = container.exec_run("bash -c 'test -d /knime-workspace && find /knime-workspace -maxdepth 1 \\( -name \"*.knwf\" -o -name \"*.knime\" \\) 2>/dev/null | head -5'", user="root")
            if result.exit_code == 0 and result.output.strip():
                logger.info("发现挂载的KNIME工作流文件，复制到 /work/knime-workspace...")
                container.exec_run(
                    "bash -c 'find /knime-workspace -maxdepth 1 -name \"*.knwf\" -exec cp {} /work/knime-workspace/ \\; 2>/dev/null || true; "
                    "find /knime-workspace -maxdepth 1 -name \"*.knime\" -exec cp {} /work/knime-workspace/ \\; 2>/dev/null || true'",
                    user="root"
                )
                container.exec_run("chown -R 1000:1000 /work/knime-workspace", user="root")
                container.exec_run("chmod -R 755 /work/knime-workspace", user="root")
                logger.info("已从挂载目录复制工作流文件到 /work/knime-workspace")
            
            # 3. 如果挂载目录没有文件，从资源目录复制
            if training_name:
                resource_base = settings.resource_base_path / "实训资源" / training_name
                metadata_file = resource_base / "metadata.json"
                
                # 读取metadata.json以获取配置
                initial_workflow_path = None
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            env_config = metadata.get("environment_config", {})
                            initial_workflow_path = env_config.get("initial_workflow_path")
                            if initial_workflow_path:
                                logger.info(f"从metadata.json读取到初始工作流路径: {initial_workflow_path}")
                    except Exception as e:
                        logger.warning(f"读取metadata.json失败: {e}")
                
                knime_resource_dir = resource_base / "knime"
                
                if knime_resource_dir.exists():
                    logger.info(f"发现KNIME资源目录: {knime_resource_dir}")
                    
                    # 根据配置决定复制哪些文件
                    workflow_files = []
                    if initial_workflow_path:
                        # 如果指定了特定工作流文件，只复制该文件
                        workflow_file_path = resource_base / initial_workflow_path
                        if workflow_file_path.exists() and workflow_file_path.suffix in ['.knwf', '.knime']:
                            workflow_files = [workflow_file_path]
                            logger.info(f"使用指定的工作流文件: {workflow_file_path}")
                        else:
                            logger.warning(f"指定的工作流文件不存在或格式不正确: {workflow_file_path}")
                            # 回退到查找所有工作流文件
                            workflow_files = list(knime_resource_dir.glob("*.knwf")) + list(knime_resource_dir.glob("*.knime"))
                    else:
                        # 如果没有指定，复制所有工作流文件
                        workflow_files = list(knime_resource_dir.glob("*.knwf")) + list(knime_resource_dir.glob("*.knime"))
                    
                    if workflow_files:
                        logger.info(f"找到 {len(workflow_files)} 个工作流文件，准备复制到容器...")
                        
                        # 使用tarfile将文件复制到容器
                        import tarfile
                        import io
                        
                        for workflow_file in workflow_files:
                            try:
                                # 创建tar归档
                                tar_stream = io.BytesIO()
                                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                                    tar.add(workflow_file, arcname=workflow_file.name)
                                tar_stream.seek(0)
                                
                                # 复制到容器
                                container.put_archive("/work/knime-workspace", tar_stream.read())
                                logger.info(f"已复制工作流文件: {workflow_file.name}")
                            except Exception as e:
                                logger.warning(f"复制工作流文件失败 {workflow_file.name}: {e}")
                        
                        # 设置权限
                        container.exec_run("chown -R 1000:1000 /work/knime-workspace", user="root")
                        container.exec_run("chmod -R 755 /work/knime-workspace", user="root")
                    else:
                        logger.info(f"KNIME资源目录存在但没有找到工作流文件（.knwf或.knime）")
                else:
                    logger.info(f"KNIME资源目录不存在: {knime_resource_dir}")
            
            # 4. 检查 /work/knime-workspace 目录内容
            if knime_workdir_exists:
                result = container.exec_run("ls -la /work/knime-workspace", user="root")
                if result.exit_code == 0:
                    output = result.output.decode('utf-8', errors='ignore')
                    logger.info(f"KNIME工作空间内容:\n{output}")
                    
                    # 检查是否有.knwf文件
                    result = container.exec_run("find /work/knime-workspace -name '*.knwf' -o -name '*.knime' 2>/dev/null | head -10", user="root")
                    if result.exit_code == 0:
                        workflows = result.output.decode('utf-8', errors='ignore').strip()
                        if workflows:
                            logger.info(f"找到KNIME工作流文件:\n{workflows}")
                        else:
                            logger.warning("KNIME工作空间目录存在但没有找到工作流文件")
            else:
                # 工作空间目录不存在，创建它
                logger.info("创建KNIME工作空间目录...")
                container.exec_run("mkdir -p /work/knime-workspace", user="root")
                container.exec_run("chown -R 1000:1000 /work/knime-workspace", user="root")
                logger.info("KNIME工作空间目录已创建")
            
            # 5. 检查/templates目录（AI模板文件）
            result = container.exec_run("test -d /templates", user="root")
            templates_exists = result.exit_code == 0
            
            if templates_exists:
                result = container.exec_run("ls -la /templates", user="root")
                if result.exit_code == 0:
                    output = result.output.decode('utf-8', errors='ignore')
                    logger.info(f"AI模板目录内容:\n{output}")
            
            # 6. 检查/datasets目录（数据集文件）
            result = container.exec_run("test -d /datasets", user="root")
            datasets_exists = result.exit_code == 0
            
            if datasets_exists:
                result = container.exec_run("ls -la /datasets", user="root")
                if result.exit_code == 0:
                    output = result.output.decode('utf-8', errors='ignore')
                    logger.info(f"数据集目录内容:\n{output}")
            
            # 7. 确保KNIME可以访问工作空间
            # KNIME默认工作空间通常在用户主目录下的.knime或knime-workspace
            # 我们需要确保KNIME可以访问/knime-workspace目录
            logger.info("设置KNIME工作空间权限...")
            container.exec_run("chown -R 1000:1000 /knime-workspace 2>/dev/null || true", user="root")
            container.exec_run("chmod -R 755 /knime-workspace 2>/dev/null || true", user="root")
            
            # 8. 如果/templates目录存在且有文件，可以复制到工作空间作为初始模板
            if templates_exists:
                result = container.exec_run("ls -A /templates 2>/dev/null | head -1", user="root")
                if result.exit_code == 0 and result.output.strip():
                    logger.info("发现模板文件，复制到工作空间...")
                    container.exec_run(
                        "cp -r /templates/* /knime-workspace/ 2>/dev/null || true",
                        user="root"
                    )
                    container.exec_run("chown -R 1000:1000 /knime-workspace", user="root")
                    logger.info("模板文件已复制到工作空间")
            
            logger.info("KNIME环境初始化完成")
            
        except Exception as e:
            logger.error(f"初始化KNIME时出错: {e}")
            # 不抛出异常，允许容器继续运行
            pass
    
    def get_container_status_by_training(
        self, 
        training_id: int, 
        user_id: int, 
        db: Session,
        env_type: Optional[str] = None
    ) -> Dict[str, any]:
        """根据training_id和user_id获取容器状态"""
        # 先查询所有匹配的记录
        query = db.query(models.ContainerProcess).filter(
            models.ContainerProcess.training_id == training_id,
            models.ContainerProcess.user_id == user_id
        )
        # 如果指定了环境类型，优先查找该类型的容器
        if env_type:
            query = query.filter(models.ContainerProcess.environment_type == env_type.upper())
        all_containers = query.order_by(models.ContainerProcess.created_at.desc()).all()
        
        logger.info(f"查询training_id={training_id}, user_id={user_id}的容器记录: {len(all_containers)}条")
        
        # 优先查找运行中的容器（按创建时间倒序）
        container_process = None
        for cp in all_containers:
            if cp.status == "running":
                # 验证容器确实在运行
                try:
                    self._ensure_initialized()
                    container = self.client.containers.get(cp.container_id)
                    if container.status == "running":
                        container_process = cp
                        logger.info(f"找到运行中的容器: container_id={cp.container_id}, port={cp.port}")
                        break
                    else:
                        # 容器已停止，更新数据库状态
                        cp.status = "stopped"
                        db.commit()
                        logger.info(f"容器已停止，更新状态: container_id={cp.container_id}")
                except docker.errors.NotFound:
                    # 容器不存在，更新数据库状态
                    cp.status = "stopped"
                    db.commit()
                    logger.info(f"容器不存在，更新状态: container_id={cp.container_id}")
                except Exception as e:
                    logger.warning(f"检查容器状态失败: {e}")
        
        # 如果没有运行中的容器，尝试查找最新的容器记录并验证
        if not container_process and all_containers:
            latest = all_containers[0]
            try:
                self._ensure_initialized()
                container = self.client.containers.get(latest.container_id)
                if container.status == "running":
                    # 更新数据库状态
                    latest.status = "running"
                    # 更新端口信息
                    ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
                    for container_port, port_config in ports.items():
                        if port_config:
                            latest.port = int(port_config[0]["HostPort"])
                            break
                    db.commit()
                    container_process = latest
                    logger.info(f"找到运行中的容器（数据库状态已更新）: container_id={latest.container_id}, port={latest.port}")
            except docker.errors.NotFound:
                logger.warning(f"容器不存在: container_id={latest.container_id}")
            except Exception as e:
                logger.warning(f"检查容器状态失败: {e}")
        
        if container_process:
            return self.get_container_status(container_process.container_id, db)
        else:
            return {
                "status": "not_found",
                "url": None,
                "host_port": None,
                "error": "容器未找到"
            }
    
    def get_container_status(self, container_id: str, db: Optional[Session] = None) -> Dict[str, any]:
        """获取容器状态"""
        self._ensure_initialized()
        
        try:
            container = self.client.containers.get(container_id)
            status = container.status
            
            # 获取容器环境变量
            env_vars = {}
            if container.attrs.get("Config", {}).get("Env"):
                for env_str in container.attrs["Config"]["Env"]:
                    if "=" in env_str:
                        key, value = env_str.split("=", 1)
                        env_vars[key] = value
            
            # 获取端口和URL
            ports = container.attrs.get("NetworkSettings", {}).get("Ports", {})
            host_port = None
            url = None
            vnc_password = env_vars.get("VNC_PW", "")
            jupyter_token = env_vars.get("JUPYTER_TOKEN", "")
            
            url = None
            host_port = None
            for container_port, port_config in ports.items():
                if port_config and len(port_config) > 0:
                    try:
                        host_port = int(port_config[0]["HostPort"])
                    except (KeyError, IndexError, ValueError):
                        logger.warning(f"无法获取主机端口: {port_config}")
                        continue
                    # 根据端口推断环境类型
                    # 获取基础URL（使用配置中的JUPYTER_BASE_URL，去掉协议前缀用于拼接）
                    try:
                        base_url_clean = settings.JUPYTER_BASE_URL.replace("http://", "").replace("https://", "")
                        base_host = base_url_clean.split(":")[0] if ":" in base_url_clean else base_url_clean
                    except Exception:
                        base_host = "localhost"

                    if container_port.startswith("8888"):
                        # Jupyter环境，需要包含token
                        if jupyter_token:
                            url = f"http://{base_host}:{host_port}/lab?token={jupyter_token}"
                        else:
                            url = f"http://{base_host}:{host_port}/lab"
                    elif container_port.startswith("8088"):
                        # Superset环境 - 需要指向登录页面或欢迎页面
                        url = f"http://{base_host}:{host_port}/superset/welcome/"
                    elif container_port.startswith("6901"):
                        # VNC Web访问URL，包含密码参数
                        if vnc_password:
                            url = f"http://{base_host}:{host_port}/vnc.html?password={vnc_password}"
                        else:
                            url = f"http://{base_host}:{host_port}/vnc.html"
                    break
            
            return {
                "status": status,
                "url": url,
                "host_port": host_port,
                "vnc_password": vnc_password if vnc_password else None,
                "jupyter_token": jupyter_token if jupyter_token else None,
                "error": None
            }
        except docker.errors.NotFound:
            return {
                "status": "stopped",
                "url": None,
                "host_port": None,
                "vnc_password": None,
                "error": "容器不存在"
            }
        except Exception as e:
            logger.error(f"查询容器状态失败: {e}")
            return {
                "status": "error",
                "url": None,
                "host_port": None,
                "vnc_password": None,
                "error": str(e)
            }
    
    def stop_container(self, container_id: str, db: Optional[Session] = None) -> bool:
        """停止并删除容器"""
        self._ensure_initialized()

        try:
            container = self.client.containers.get(container_id)

            # 获取容器信息用于HDFS同步
            container_process = None
            if db:
                container_process = db.query(models.ContainerProcess).filter(
                    models.ContainerProcess.container_id == container_id
                ).first()

            # 在停止容器前同步数据到HDFS（如果启用）
            if container_process:
                try:
                    hdfs_svc = get_hdfs_service()
                    if hdfs_svc.enabled and hdfs_svc.sync_on_stop:
                        user_id = container_process.user_id
                        training_id = container_process.training_id
                        work_dir = Path(settings.CONTAINER_STUDENT_WORK_BASE) / str(user_id) / str(training_id)
                        if work_dir.exists():
                            hdfs_svc.on_container_stop(user_id, training_id, work_dir)
                except Exception as e:
                    logger.warning(f"HDFS同步失败（容器仍将停止）: {e}")

            container.stop()
            container.remove()

            # 更新数据库状态
            if container_process:
                container_process.status = "stopped"
                db.commit()

            logger.info(f"容器停止成功: {container_id}")
            return True
        except docker.errors.NotFound:
            logger.warning(f"容器不存在: {container_id}")
            return False
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            return False


# 创建全局实例（延迟初始化）
container_manager = ContainerManager()

