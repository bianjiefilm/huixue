"""
极简授权验证模块 - Gitee（码云）方案

功能：
- 定期从 Gitee 读取授权状态
- 支持在线授权/停用控制
- 国内访问稳定，完全免费

使用方式：
1. 在 Gitee 创建私有仓库或使用 Gist
2. 上传 license.json 文件，内容示例:
   {
     "enabled": true,
     "expire_date": "2026-12-31",
     "message": "授权正常"
   }

3. 获取文件 raw URL:
   - 访问: https://gitee.com/你的用户名/tempo-license/raw/main/license.json

4. 配置环境变量:
   - LICENSE_URL: 直接填 license 文件的 raw URL（最简单）
   - LICENSE_TOKEN: 私有仓库的 Token（可选）

5. 飞书通知（可选）:
   - FEISHU_WEBHOOK_URL: 飞书 Webhook URL

环境变量：
- LICENSE_CHECK_INTERVAL: 检查间隔（默认 604800 秒 = 7天）
- LICENSE_URL: 直接设置授权文件 URL
- LICENSE_TOKEN: Gitee 私有仓库 Token（私有仓库需要）
"""

import os
import sys
import json
import logging
import time
import hashlib
import requests
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


class GiteeLicenseChecker:
    """
    Gitee 授权检查器

    使用码云（Gitee）作为授权服务器：
    - 国内访问稳定
    - 完全免费
    - 支持私有仓库
    """

    def __init__(
        self,
        license_url: str = None,
        license_token: str = None,
        check_interval: int = 604800  # 7天
    ):
        """
        初始化授权检查器

        Args:
            license_url: 授权文件 URL（必填）
            license_token: Gitee Token（私有仓库需要）
            check_interval: 检查间隔（秒）
        """
        self.license_url = license_url or os.environ.get('LICENSE_URL')
        self.license_token = license_token or os.environ.get('LICENSE_TOKEN')
        self.check_interval = int(os.environ.get('LICENSE_CHECK_INTERVAL', check_interval))

        # 飞书 Webhook（可选）
        self.feishu_webhook = os.environ.get('FEISHU_WEBHOOK_URL')

        self.running = False
        self._last_status = None
        self._last_check_time = None

        # 设置请求头
        self.headers = {}
        if self.license_token:
            self.headers['Authorization'] = f'token {self.license_token}'

        # 验证配置
        if not self.license_url:
            logger.warning("未配置 LICENSE_URL，将跳过授权检查")
            self.license_url = None

    def get_machine_code(self) -> str:
        """获取本机机器码"""
        import uuid
        import hashlib
        import socket

        identifiers = []

        # MAC 地址
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])
        identifiers.append(f"mac:{mac}")

        # 主机名
        identifiers.append(f"host:{socket.gethostname()}")

        # 机器码
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
        if not self.license_url:
            return LicenseStatus.VALID, {"message": "未配置授权检查，跳过"}

        try:
            import base64

            # 检查是否是 Gitee 仓库
            if 'gitee.com' in self.license_url and '/raw/' in self.license_url:
                # 从 URL 提取仓库信息
                # URL 格式: https://gitee.com/owner/repo/raw/branch/file
                parts = self.license_url.replace('https://gitee.com/', '').split('/')
                if len(parts) >= 5:
                    owner = parts[0]
                    repo = parts[1]
                    # 跳过 'raw' 和分支名，获取文件名
                    file_path = '/'.join(parts[4:])

                    # 使用 API 获取文件
                    api_url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/contents/{file_path}"
                    params = {}
                    if self.license_token:
                        params['access_token'] = self.license_token

                    response = requests.get(api_url, params=params, timeout=10)
                else:
                    raise ValueError(f"无效的 Gitee URL: {self.license_url}")
            else:
                # 其他 URL 直接访问
                response = requests.get(self.license_url, timeout=10, headers=self.headers)

            # Gitee 可能返回 404 或其他状态码
            if response.status_code == 404:
                return LicenseStatus.DISABLED, {"message": "授权文件不存在"}

            response.raise_for_status()

            # 尝试解析 JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                # 可能返回的是文本内容
                content = response.text.strip()
                if content.startswith('{'):
                    data = json.loads(content)
                else:
                    return LicenseStatus.ERROR, {"message": "授权文件格式错误"}

            # 处理 Gitee API 响应（内容是 base64 编码的）
            if 'content' in data and isinstance(data['content'], str):
                # Gitee API 返回的格式
                encoded_content = data['content']
                try:
                    content_bytes = base64.b64decode(encoded_content)
                    data = json.loads(content_bytes.decode('utf-8'))
                except Exception:
                    # 如果解码失败，尝试直接解析
                    pass

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
                try:
                    expire_datetime = datetime.strptime(expire_date, '%Y-%m-%d')
                    if datetime.now() > expire_datetime:
                        logger.warning(f"授权已过期: {expire_date}")
                        return LicenseStatus.EXPIRED, {
                            "expire_date": expire_date,
                            "message": f"授权已于 {expire_date} 过期"
                        }
                except ValueError:
                    logger.warning(f"过期日期格式错误: {expire_date}")

            # 有效
            return LicenseStatus.VALID, {
                "enabled": True,
                "expire_date": expire_date,
                "message": message or "授权有效"
            }

        except requests.exceptions.Timeout:
            logger.error("授权检查超时")
            return LicenseStatus.ERROR, {"message": "网络超时"}

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP 错误: {e}")
            return LicenseStatus.ERROR, {"message": f"请求失败: {e.response.status_code}"}

        except Exception as e:
            logger.error(f"授权检查失败: {e}")
            return LicenseStatus.ERROR, {"message": str(e)}

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

            message = f"""**授权状态变更**

• 状态: {emoji.get(status, 'ℹ️')} {status.value}
• 消息: {info.get('message', '无')}
• 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_机器码: {self.get_machine_code()[:16]}..._"""

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

            for container in client.containers.list():
                if container.name.startswith(('huixue-', 'tempo-')):
                    logger.info(f"停止容器: {container.name}")
                    container.stop()

            logger.info("所有服务已停止")

        except Exception as e:
            logger.error(f"停止服务失败: {e}")

    def poll(self):
        """轮询主循环"""
        logger.info(f"授权检查已启动，检查间隔: {self.check_interval}秒")
        logger.info(f"授权 URL: {self.license_url}")

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
def get_license_checker() -> GiteeLicenseChecker:
    """获取全局授权检查器"""
    return GiteeLicenseChecker()


def start_license_checker():
    """启动授权检查"""
    get_license_checker().start()


def check_license_once() -> tuple[LicenseStatus, dict]:
    """单次检查授权"""
    return get_license_checker().check_license()


def main():
    """主函数 - 单次检查并退出"""
    print("=" * 50)
    print("慧学 授权检查 (Gitee 方案)")
    print("=" * 50)

    checker = GiteeLicenseChecker()

    if not checker.license_url:
        print("错误: 请设置 LICENSE_URL 环境变量")
        print("\n设置方法:")
        print("  1. 在 Gitee 创建仓库，上传 license.json")
        print("  2. 获取文件 Raw URL:")
        print("     https://gitee.com/你的用户名/仓库名/raw/main/license.json")
        print("  3. 设置环境变量:")
        print("     export LICENSE_URL='你的URL'")
        return 1

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
