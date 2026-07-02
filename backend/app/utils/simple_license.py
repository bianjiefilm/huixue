"""
极简授权验证模块 - 支持在线(GitHub Gist)和离线(本地文件)方案

功能：
- 在线模式：定期从 GitHub Gist 读取授权状态
- 离线模式：从本地文件读取授权状态，支持机器码绑定
- 支持在线授权/停用控制
- 支持查看机器码

使用方式（在线模式）：
1. 创建一个公开的 GitHub Gist
2. 文件名: license.json
3. 文件内容示例:
   {
     "enabled": true,
     "expire_date": "2026-12-31",
     "message": "授权正常"
   }
4. 配置环境变量:
   - LICENSE_URL: 直接填 license 文件的原始链接（最简单）
   - GIST_ID: Gist ID（从 URL 中获取）
   - GIST_TOKEN: GitHub Personal Access Token（可选，公开 Gist 不需要）

使用方式（离线模式 - 离线部署推荐）：
1. 配置环境变量:
   - LICENSE_PATH: 本地 license 文件路径（默认: /app/license/license.json）
   - LICENSE_CHECK_INTERVAL: 检查间隔（默认 604800 秒 = 7天）
2. 确保 license.json 文件存在，包含:
   {
     "machine_id": "机器码MD5哈希",
     "disk_id": "硬盘序列号",
     "expire_date": "2026-12-31",
     "features": ["all"]
   }

环境变量：
- LICENSE_CHECK_INTERVAL: 检查间隔（默认 604800 秒 = 7天）
- LICENSE_URL: 直接设置授权文件 URL（在线模式）
- LICENSE_PATH: 本地授权文件路径（离线模式）
- GIST_ID: GitHub Gist ID
- GIST_TOKEN: GitHub Personal Access Token
"""

import os
import sys
import json
import logging
import time
import hashlib
import socket
import subprocess
import requests
import uuid
from datetime import datetime
from pathlib import Path
from threading import Thread
from enum import Enum

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LicenseStatus(Enum):
    """授权状态"""
    VALID = "valid"           # 有效
    EXPIRED = "expired"       # 已过期
    DISABLED = "disabled"     # 已停用
    ERROR = "error"           # 获取失败


class SimpleLicenseChecker:
    """
    极简授权检查器

    支持三种配置方式（按简单程度排序）：
    1. LICENSE_PATH: 本地文件路径（离线部署推荐）
    2. LICENSE_URL: 直接设置文件 URL（在线模式）
    3. GIST_ID: GitHub Gist ID
    """

    def __init__(
        self,
        license_path: str = None,
        license_url: str = None,
        gist_id: str = None,
        gist_token: str = None,
        check_interval: int = 604800  # 7天
    ):
        """
        初始化授权检查器

        Args:
            license_path: 本地 license 文件路径（离线模式）
            license_url: 直接的 license 文件 URL（在线模式）
            gist_id: GitHub Gist ID
            gist_token: GitHub Personal Access Token（公开 Gist 不需要）
            check_interval: 检查间隔（秒）
        """
        # 优先级: 构造参数 > 环境变量
        self.license_path = license_path or os.environ.get('LICENSE_PATH')
        self.license_url = license_url or os.environ.get('LICENSE_URL')
        self.gist_id = gist_id or os.environ.get('GIST_ID')
        self.gist_token = gist_token or os.environ.get('GIST_TOKEN')
        self.check_interval = int(os.environ.get('LICENSE_CHECK_INTERVAL', check_interval))

        # 飞书 Webhook（可选，用于通知）
        self.feishu_webhook = os.environ.get('FEISHU_WEBHOOK_URL')

        self.running = False
        self._last_status = None
        self._last_check_time = None

        # 计算 URL（如果是 Gist 方式）
        if self.gist_id and not self.license_url:
            raw_url = f"https://gist.githubusercontent.com/anonymous/{self.gist_id}/raw/license.json"
            if self.gist_token:
                # 私有 Gist 需要认证
                self.headers = {"Authorization": f"token {self.gist_token}"}
            else:
                self.headers = {}
            self.license_url = raw_url

        # 确定使用哪种模式
        if self.license_path:
            self.mode = "local"
            logger.info(f"使用本地授权文件: {self.license_path}")
        elif self.license_url:
            self.mode = "online"
            logger.info(f"使用在线授权 URL: {self.license_url}")
        elif self.gist_id:
            self.mode = "gist"
            logger.info(f"使用 GitHub Gist: {self.gist_id}")
        else:
            self.mode = "disabled"
            logger.warning("未配置授权检查，将跳过授权检查")
            self.license_path = None
            self.license_url = None

    def get_machine_code(self) -> str:
        """获取本机机器码（用于申请授权）"""

        # 优先级1: 从环境变量读取（容器环境）
        env_machine_code = os.environ.get('HOST_MACHINE_CODE')
        if env_machine_code:
            logger.debug(f"从环境变量获取机器码")
            return env_machine_code

        identifiers = []

        # MAC 地址（使用容器网络接口的MAC）
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])
        identifiers.append(mac)

        # 生成机器码
        machine_code = hashlib.sha256(
            ':'.join(identifiers).encode()
        ).hexdigest()

        return machine_code

    def check_license(self) -> tuple[LicenseStatus, dict]:
        """
        检查授权状态

        Returns:
            (状态, 授权信息字典)
        """
        # 离线模式：本地文件验证
        if self.mode == "local":
            return self._check_local_license()

        # 在线模式：URL 或 Gist
        if not self.license_url:
            return LicenseStatus.VALID, {"message": "未配置授权检查，跳过"}

        try:
            response = requests.get(self.license_url, timeout=10, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            # 解析授权信息
            enabled = data.get('enabled', True)
            expire_date = data.get('expire_date', '')
            message = data.get('message', '')

            # 检查是否启用
            if not enabled:
                logger.warning("授权已被停用")
                return LicenseStatus.DISABLED, {
                    "enabled": False,
                    "message": message or "授权已被停用，请联系管理员"
                }

            # 检查是否过期
            if expire_date:
                expire_datetime = datetime.strptime(expire_date, '%Y-%m-%d')
                if datetime.now() > expire_datetime:
                    logger.warning(f"授权已过期: {expire_date}")
                    return LicenseStatus.EXPIRED, {
                        "expire_date": expire_date,
                        "message": f"授权已于 {expire_date} 过期"
                    }

            # 有效
            return LicenseStatus.VALID, {
                "enabled": True,
                "expire_date": expire_date,
                "message": message or "授权有效"
            }

        except requests.exceptions.Timeout:
            logger.error("授权检查超时")
            # 网络超时时不强制停机，返回最后的状态
            if self._last_status == LicenseStatus.DISABLED:
                return LicenseStatus.ERROR, {"message": "网络超时，授权状态未知"}
            return LicenseStatus.VALID, {"message": "网络超时，使用缓存状态"}

        except Exception as e:
            logger.error(f"授权检查失败: {e}")
            return LicenseStatus.ERROR, {"message": f"检查失败: {str(e)}"}

    def _check_local_license(self) -> tuple[LicenseStatus, dict]:
        """
        本地授权文件验证（离线模式）

        验证：
        1. 授权文件是否存在
        2. 机器码是否匹配
        3. 硬盘ID是否匹配
        4. 是否过期
        """
        if not self.license_path:
            return LicenseStatus.ERROR, {"message": "未配置本地授权文件路径"}

        try:
            # 检查文件是否存在
            if not os.path.exists(self.license_path):
                logger.error(f"授权文件不存在: {self.license_path}")
                return LicenseStatus.ERROR, {"message": f"授权文件不存在: {self.license_path}"}

            # 读取授权文件
            with open(self.license_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 验证机器码
            expected_machine_id = data.get('machine_id', '')
            if expected_machine_id:
                current_machine_id = self.get_machine_code()
                if expected_machine_id != current_machine_id:
                    logger.error(f"机器码不匹配: 预期 {expected_machine_id[:16]}..., 当前 {current_machine_id[:16]}...")
                    return LicenseStatus.DISABLED, {
                        "message": "机器码不匹配，授权无效"
                    }

            # 验证硬盘ID（在容器环境中跳过此验证）
            # 容器内无法可靠获取硬盘ID，且已有机器码绑定
            expected_disk_id = data.get('disk_id', '')
            if expected_disk_id and not os.environ.get('HOST_MACHINE_CODE'):
                # 非容器环境才验证硬盘ID
                current_disk_id = self.get_disk_serial()
                if expected_disk_id != current_disk_id:
                    logger.error(f"硬盘ID不匹配: 预期 {expected_disk_id}, 当前 {current_disk_id}")
                    return LicenseStatus.DISABLED, {
                        "message": "硬盘ID不匹配，授权无效"
                    }
            elif expected_disk_id:
                logger.info(f"跳过硬盘ID验证（容器环境），仅验证机器码")

            # 检查过期日期
            expire_date = data.get('expire_date', '')
            if expire_date:
                expire_datetime = datetime.strptime(expire_date, '%Y-%m-%d')
                if datetime.now() > expire_datetime:
                    logger.warning(f"授权已过期: {expire_date}")
                    return LicenseStatus.EXPIRED, {
                        "expire_date": expire_date,
                        "message": f"授权已于 {expire_date} 过期"
                    }

            # 验证签名（可选）
            signature = data.get('signature', '')
            if signature:
                # 验证签名
                data_to_verify = {
                    'machine_id': data.get('machine_id', ''),
                    'disk_id': data.get('disk_id', ''),
                    'expire_date': expire_date,
                    'features': data.get('features', [])
                }
                expected_sig = hashlib.sha256(
                    json.dumps(data_to_verify, sort_keys=True).encode()
                ).hexdigest()
                if signature != expected_sig:
                    logger.warning("授权文件签名验证失败")

            # 有效
            features = data.get('features', ['all'])
            return LicenseStatus.VALID, {
                "expire_date": expire_date,
                "features": features,
                "message": "授权有效（离线模式）"
            }

        except json.JSONDecodeError as e:
            logger.error(f"授权文件 JSON 解析失败: {e}")
            return LicenseStatus.ERROR, {"message": f"授权文件格式错误: {str(e)}"}

        except Exception as e:
            logger.error(f"本地授权检查失败: {e}")
            return LicenseStatus.ERROR, {"message": f"检查失败: {str(e)}"}

    def get_disk_serial(self) -> str:
        """获取硬盘序列号（用于离线验证）"""
        try:
            # 方法1: 使用 lsblk
            result = os.popen('lsblk -no serial /dev/sda 2>/dev/null').read().strip()
            if result:
                return result

            # 方法2: 使用 hdparm
            result = os.popen('hdparm -i /dev/sda 2>/dev/null | grep SerialNo').read()
            if result:
                return result.split('=')[1].strip().strip('<')

            # 方法3: 使用 smartctl
            result = os.popen('smartctl -i /dev/sda 2>/dev/null | grep "Serial Number"').read()
            if result:
                return result.split(':')[-1].strip()

            # 方法4: 读取 /proc 或 /sys
            for path in ['/sys/class/block/sda/device/serial', '/sys/block/sda/serial']:
                if os.path.exists(path):
                    return open(path).read().strip()
        except Exception as e:
            logger.debug(f"获取硬盘序列号失败: {e}")

        # 返回默认标识
        return "unknown"

    def send_notification(self, status: LicenseStatus, info: dict):
        """发送飞书通知"""
        if not self.feishu_webhook:
            return

        try:
            emoji = {
                LicenseStatus.VALID: "✅",
                LicenseStatus.EXPIRED: "⚠️",
                LicenseStatus.DISABLED: "🚨",
                LicenseStatus.ERROR: "❓"
            }

            title = f"慧学 授权检查 - {status.value}"
            message = f"""
{emoji.get(status, 'ℹ️')} **授权状态变更**

• 状态: {status.value}
• 消息: {info.get('message', '无')}
• 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_机器码: {self.get_machine_code()[:16]}..._
"""

            payload = {
                "msg_type": "text",
                "content": {"text": message}
            }

            requests.post(self.feishu_webhook, json=payload, timeout=10)
            logger.info("飞书通知已发送")

        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    def should_stop_service(self, status: LicenseStatus) -> bool:
        """是否应该停止服务"""
        return status in [LicenseStatus.DISABLED, LicenseStatus.EXPIRED]

    def stop_services(self):
        """停止所有服务"""
        try:
            import docker
            from app.core.config import settings
            docker_host = getattr(settings, 'DOCKER_HOST', None) or ''
            if docker_host and not docker_host.startswith("unix://"):
                client = docker.DockerClient(base_url=docker_host)
            else:
                client = docker.from_env()

            service_prefixes = ['huixue-', 'tempo-']
            for container in client.containers.list():
                for prefix in service_prefixes:
                    if container.name.startswith(prefix):
                        logger.info(f"停止容器: {container.name}")
                        container.stop()
                        break

            logger.info("所有服务已停止")

        except Exception as e:
            logger.error(f"停止服务失败: {e}")

    def poll(self):
        """轮询主循环"""
        logger.info(f"授权检查已启动，检查间隔: {self.check_interval}秒")

        while self.running:
            try:
                status, info = self.check_license()
                self._last_status = status
                self._last_check_time = datetime.now()

                logger.info(f"授权检查结果: {status.value} - {info.get('message', '')}")

                # 状态变化时发送通知
                if self._last_status != status:
                    self.send_notification(status, info)

                # 如果授权失效，停止服务
                if self.should_stop_service(status):
                    logger.critical("授权失效，停止服务")
                    self.stop_services()
                    return

            except Exception as e:
                logger.error(f"授权检查异常: {e}")

            time.sleep(self.check_interval)

    def start(self, daemon: bool = True):
        """启动授权检查"""
        self.running = True
        thread = Thread(target=self.poll, daemon=daemon)
        thread.start()
        logger.info("授权检查器已启动")

    def stop(self):
        """停止授权检查"""
        self.running = False
        logger.info("授权检查已停止")


# 便捷函数
def get_license_checker() -> SimpleLicenseChecker:
    """获取全局授权检查器"""
    return SimpleLicenseChecker()


def start_license_checker():
    """启动授权检查"""
    get_license_checker().start()


def check_license_once() -> tuple[LicenseStatus, dict]:
    """单次检查授权"""
    return get_license_checker().check_license()


def main():
    """主函数 - 单次检查并退出"""
    logger.info("=" * 50)
    logger.info("慧学 授权检查")
    logger.info("=" * 50)

    checker = SimpleLicenseChecker()
    status, info = checker.check_license()

    print(f"\n授权状态: {status.value}")
    print(f"信息: {info.get('message', '无')}")
    print(f"时间: {datetime.now()}")

    if checker.should_stop_service(status):
        print("\n⚠️  授权失效，服务应该停止")
        return 1
    else:
        print("\n✓  授权检查通过")
        return 0


if __name__ == '__main__':
    sys.exit(main())
