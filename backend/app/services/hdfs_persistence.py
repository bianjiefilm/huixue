"""
HDFS持久化服务

负责将学生工作数据同步到HDFS，实现跨容器的数据持久化
"""
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class HDFSPersistenceService:
    """HDFS持久化服务，管理学生数据的HDFS存储"""

    def __init__(self):
        self.enabled = settings.HDFS_ENABLED
        self.hdfs_host = settings.HDFS_HOST
        self.hdfs_port = settings.HDFS_PORT
        self.hdfs_user = settings.HDFS_USER
        self.hdfs_base_path = settings.HDFS_BASE_PATH
        self.local_cache_dir = Path(settings.HDFS_LOCAL_CACHE_DIR)
        self.sync_on_stop = settings.HDFS_SYNC_ON_STOP

        # 确保本地缓存目录存在
        if self.enabled:
            self.local_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_hdfs_path(self, user_id: int, training_id: int) -> str:
        """获取HDFS上的学生数据路径"""
        return f"{self.hdfs_base_path}/user_{user_id}/training_{training_id}"

    def _get_local_cache_path(self, user_id: int, training_id: int) -> Path:
        """获取本地缓存路径"""
        path = self.local_cache_dir / f"user_{user_id}" / f"training_{training_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _run_hdfs_command(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """执行HDFS命令"""
        cmd = ["hdfs", "dfs"] + args
        env = os.environ.copy()
        env["HADOOP_USER_NAME"] = self.hdfs_user

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            if check and result.returncode != 0:
                logger.error(f"HDFS命令失败: {' '.join(cmd)}")
                logger.error(f"stderr: {result.stderr}")
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"HDFS命令超时: {' '.join(cmd)}")
            raise
        except FileNotFoundError:
            logger.error("hdfs命令未找到，请确保Hadoop已安装并配置PATH")
            raise

    def ensure_hdfs_directory(self, user_id: int, training_id: int) -> bool:
        """确保HDFS目录存在"""
        if not self.enabled:
            return True

        hdfs_path = self._get_hdfs_path(user_id, training_id)
        try:
            # 检查目录是否存在
            result = self._run_hdfs_command(["-test", "-d", hdfs_path], check=False)
            if result.returncode != 0:
                # 目录不存在，创建它
                result = self._run_hdfs_command(["-mkdir", "-p", hdfs_path])
                if result.returncode == 0:
                    logger.info(f"创建HDFS目录: {hdfs_path}")
                    return True
                else:
                    logger.error(f"创建HDFS目录失败: {hdfs_path}")
                    return False
            return True
        except Exception as e:
            logger.error(f"确保HDFS目录时出错: {e}")
            return False

    def sync_to_hdfs(self, user_id: int, training_id: int, local_path: Path) -> bool:
        """
        将本地数据同步到HDFS

        Args:
            user_id: 用户ID
            training_id: 实训ID
            local_path: 本地数据路径

        Returns:
            是否成功
        """
        if not self.enabled:
            logger.debug("HDFS未启用，跳过同步")
            return True

        if not local_path.exists():
            logger.warning(f"本地路径不存在: {local_path}")
            return False

        hdfs_path = self._get_hdfs_path(user_id, training_id)

        try:
            # 确保HDFS目录存在
            if not self.ensure_hdfs_directory(user_id, training_id):
                return False

            # 同步文件到HDFS
            # 使用 -put -f 强制覆盖
            result = self._run_hdfs_command(["-put", "-f", str(local_path) + "/*", hdfs_path])
            if result.returncode == 0:
                logger.info(f"同步到HDFS成功: {local_path} -> {hdfs_path}")
                return True
            else:
                logger.error(f"同步到HDFS失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"同步到HDFS时出错: {e}")
            return False

    def sync_from_hdfs(self, user_id: int, training_id: int, local_path: Path) -> bool:
        """
        从HDFS同步数据到本地

        Args:
            user_id: 用户ID
            training_id: 实训ID
            local_path: 本地数据路径

        Returns:
            是否成功
        """
        if not self.enabled:
            logger.debug("HDFS未启用，跳过同步")
            return True

        hdfs_path = self._get_hdfs_path(user_id, training_id)

        try:
            # 检查HDFS路径是否存在
            result = self._run_hdfs_command(["-test", "-d", hdfs_path], check=False)
            if result.returncode != 0:
                logger.info(f"HDFS路径不存在，无需同步: {hdfs_path}")
                return True

            # 确保本地目录存在
            local_path.mkdir(parents=True, exist_ok=True)

            # 从HDFS获取文件
            result = self._run_hdfs_command(["-get", "-f", hdfs_path + "/*", str(local_path)])
            if result.returncode == 0:
                logger.info(f"从HDFS同步成功: {hdfs_path} -> {local_path}")
                return True
            else:
                # 可能是目录为空
                if "No such file" in result.stderr or "Source path is a directory" in result.stderr:
                    logger.info(f"HDFS目录为空或无文件: {hdfs_path}")
                    return True
                logger.error(f"从HDFS同步失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"从HDFS同步时出错: {e}")
            return False

    def get_volume_mounts(
        self,
        user_id: int,
        training_id: int,
        env_type: str
    ) -> Dict[str, Dict[str, str]]:
        """
        获取HDFS持久化相关的卷挂载配置

        Args:
            user_id: 用户ID
            training_id: 实训ID
            env_type: 环境类型

        Returns:
            卷挂载配置字典
        """
        volumes = {}

        if not self.enabled:
            return volumes

        # 获取本地缓存路径
        local_cache = self._get_local_cache_path(user_id, training_id)

        # 从HDFS预加载数据到本地缓存
        try:
            self.sync_from_hdfs(user_id, training_id, local_cache)
        except Exception as e:
            logger.warning(f"从HDFS预加载数据失败: {e}")

        # 挂载HDFS缓存目录
        # 这个目录将作为持久化数据的缓存层
        hdfs_data_dir = local_cache / "hdfs_data"
        hdfs_data_dir.mkdir(parents=True, exist_ok=True)
        volumes[str(hdfs_data_dir.resolve())] = {"bind": "/hdfs_data", "mode": "rw"}

        # 对于需要HDFS持久化的环境类型，添加额外配置
        if env_type.upper() in ["JUPYTER", "TEMPO_AI", "VDI_PYCHARM"]:
            # 挂载HDFS配置文件（如果存在）
            hadoop_conf_dir = Path("/etc/hadoop/conf")
            if hadoop_conf_dir.exists():
                volumes[str(hadoop_conf_dir)] = {"bind": "/etc/hadoop/conf", "mode": "ro"}

        return volumes

    def get_env_vars(self, user_id: int, training_id: int) -> Dict[str, str]:
        """
        获取HDFS相关的环境变量

        Args:
            user_id: 用户ID
            training_id: 实训ID

        Returns:
            环境变量字典
        """
        env_vars = {}

        if not self.enabled:
            return env_vars

        # HDFS连接信息
        env_vars["HDFS_ENABLED"] = "true"
        env_vars["HDFS_HOST"] = self.hdfs_host
        env_vars["HDFS_PORT"] = str(self.hdfs_port)
        env_vars["HDFS_USER"] = self.hdfs_user
        env_vars["HDFS_USER_PATH"] = self._get_hdfs_path(user_id, training_id)

        # WebHDFS URL（用于REST API访问）
        env_vars["WEBHDFS_URL"] = f"http://{self.hdfs_host}:{settings.HDFS_WEBHDFS_PORT}/webhdfs/v1"

        # 本地HDFS数据目录（容器内路径）
        env_vars["HDFS_LOCAL_DATA_DIR"] = "/hdfs_data"

        return env_vars

    def on_container_stop(self, user_id: int, training_id: int, work_dir: Path) -> bool:
        """
        容器停止时的回调，同步数据到HDFS

        Args:
            user_id: 用户ID
            training_id: 实训ID
            work_dir: 学生工作目录

        Returns:
            是否成功
        """
        if not self.enabled or not self.sync_on_stop:
            return True

        logger.info(f"容器停止，开始同步数据到HDFS: user={user_id}, training={training_id}")

        try:
            # 同步工作目录到HDFS
            success = self.sync_to_hdfs(user_id, training_id, work_dir)
            if success:
                logger.info(f"容器停止时同步完成: user={user_id}, training={training_id}")
            else:
                logger.warning(f"容器停止时同步失败: user={user_id}, training={training_id}")
            return success
        except Exception as e:
            logger.error(f"容器停止时同步出错: {e}")
            return False

    def cleanup_local_cache(self, user_id: int, training_id: int, keep_days: int = 7) -> bool:
        """
        清理本地缓存（仅保留最近N天的数据）

        Args:
            user_id: 用户ID
            training_id: 实训ID
            keep_days: 保留天数

        Returns:
            是否成功
        """
        local_cache = self._get_local_cache_path(user_id, training_id)

        if not local_cache.exists():
            return True

        try:
            # 检查目录修改时间
            mtime = datetime.fromtimestamp(local_cache.stat().st_mtime)
            age_days = (datetime.now() - mtime).days

            if age_days > keep_days:
                # 先同步到HDFS
                self.sync_to_hdfs(user_id, training_id, local_cache)
                # 然后删除本地缓存
                shutil.rmtree(local_cache)
                logger.info(f"清理本地缓存: {local_cache} (已存在 {age_days} 天)")

            return True
        except Exception as e:
            logger.error(f"清理本地缓存失败: {e}")
            return False

    def get_user_storage_usage(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的HDFS存储使用情况

        Args:
            user_id: 用户ID

        Returns:
            存储使用信息
        """
        if not self.enabled:
            return {"enabled": False}

        user_hdfs_path = f"{self.hdfs_base_path}/user_{user_id}"

        try:
            # 获取目录大小
            result = self._run_hdfs_command(["-du", "-s", "-h", user_hdfs_path], check=False)
            if result.returncode == 0:
                # 解析输出格式: "123.4 M  /path/to/dir"
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    size_str = parts[0]
                    unit = parts[1] if len(parts) > 2 else "B"
                    return {
                        "enabled": True,
                        "path": user_hdfs_path,
                        "size": f"{size_str} {unit}",
                        "raw_output": result.stdout.strip()
                    }

            return {
                "enabled": True,
                "path": user_hdfs_path,
                "size": "0 B",
                "message": "目录为空或不存在"
            }

        except Exception as e:
            return {
                "enabled": True,
                "path": user_hdfs_path,
                "error": str(e)
            }


# 创建全局实例
hdfs_service = HDFSPersistenceService()
