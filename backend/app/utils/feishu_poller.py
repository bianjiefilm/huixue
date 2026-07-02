"""
飞书消息轮询客户端

功能：
- 定期轮询飞书 API 检查消息
- 执行管理员发送的指令
- 发送告警通知和日报

适用场景：
- 内网服务器（能出不能进）
- 无公网 IP/域名
- 长连接无法使用的环境

使用方式：
1. 配置环境变量
2. 启动客户端: python -m app.utils.feishu_poller

环境变量：
- FEISHU_APP_ID: 飞书应用 ID
- FEISHU_APP_SECRET: 飞书应用密钥
- FEISHU_CHAT_ID: 群聊 ID（用于发送消息）
- FEISHU_WEBHOOK_URL: Webhook URL（可选，用于接收消息）
- FEISHU_POLLING_INTERVAL: 轮询间隔（默认 30 秒）
"""

import os
import sys
import json
import logging
import time
import hashlib
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
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


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    CARD = "card"


class FeishuPoller:
    """
    飞书消息轮询器

    功能：
    - 定期检查飞书消息
    - 解析并执行管理员指令
    - 发送告警和日报通知
    """

    def __init__(
        self,
        app_id: str = None,
        app_secret: str = None,
        chat_id: str = None,
        webhook_url: str = None,
        polling_interval: int = 604800  # 7天 = 604800秒
    ):
        """
        初始化轮询器

        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            chat_id: 群聊 ID（用于发送消息）
            webhook_url: Webhook URL（可选）
            polling_interval: 轮询间隔（秒）
        """
        self.app_id = app_id or os.environ.get('FEISHU_APP_ID')
        self.app_secret = app_secret or os.environ.get('FEISHU_APP_SECRET')
        self.chat_id = chat_id or os.environ.get('FEISHU_CHAT_ID')
        self.webhook_url = webhook_url or os.environ.get('FEISHU_WEBHOOK_URL')
        self.polling_interval = int(os.environ.get('FEISHU_POLLING_INTERVAL', polling_interval))

        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self.access_token_expires = 0
        self.running = False
        self.last_message_id = None

        # 已处理的消息缓存（避免重复处理）
        self._processed_messages: Dict[str, float] = {}

        # 验证配置
        if not self.app_id or not self.app_secret:
            raise ValueError("请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")

    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌（tenant_access_token）"""
        # 检查缓存是否有效
        if self.access_token and time.time() < self.access_token_expires:
            return self.access_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                self.access_token = data["tenant_access_token"]
                # 提前 5 分钟刷新
                self.access_token_expires = time.time() + data.get("expire", 7200) - 300
                return self.access_token
            else:
                logger.error(f"获取访问令牌失败: {data}")
        except Exception as e:
            logger.error(f"获取访问令牌异常: {e}")

        return None

    def _get_messages(self) -> List[Dict]:
        """获取最新消息"""
        token = self._get_access_token()
        if not token:
            return []

        # 如果没有 chat_id，无法获取消息
        if not self.chat_id:
            logger.warning("未设置 FEISHU_CHAT_ID，无法获取消息")
            return []

        url = f"{self.base_url}/im/v1/messages"
        params = {
            "container_id_type": "chat",
            "container_id": self.chat_id,
            "page_size": 20
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                return data.get("data", {}).get("items", [])
            else:
                logger.error(f"获取消息失败: {data}")
        except Exception as e:
            logger.error(f"获取消息异常: {e}")

        return []

    def _get_message_content(self, message_id: str) -> Optional[Dict]:
        """获取单条消息内容"""
        token = self._get_access_token()
        if not token:
            return None

        url = f"{self.base_url}/im/v1/messages/{message_id}"
        params = {"message_id": message_id}
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()

            if data.get("code") == 0:
                return data.get("data")
        except Exception as e:
            logger.error(f"获取消息内容异常: {e}")

        return None

    def _send_message(self, text: str, chat_id: str = None) -> bool:
        """发送消息到群聊"""
        token = self._get_access_token()
        if not token:
            return False

        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            logger.warning("未设置 chat_id，无法发送消息")
            return False

        url = f"{self.base_url}/im/v1/messages"
        params = {"receive_id_type": "chat_id"}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "receive_id": target_chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text})
        }

        try:
            response = requests.post(url, params=params, headers=headers,
                                    json=payload, timeout=10)
            data = response.json()
            if data.get("code") == 0:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"发送消息失败: {data}")
        except Exception as e:
            logger.error(f"发送消息异常: {e}")

        return False

    def _send_alert(self, title: str, message: str, severity: str = 'warning'):
        """发送告警消息"""
        emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }

        text = f"""**{emoji.get(severity, '⚠️')} {title}**

{message}

_来自: 慧学 平台_
_时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"""

        self._send_message(text)

    def _parse_command(self, text: str) -> Optional[Dict]:
        """
        解析指令

        支持的指令：
        - /status              # 查询系统状态
        - /license status      # 查询授权状态
        - /license generate --machine xxx --expire 2026-12-31  # 生成授权
        - /license revoke      # 撤销授权
        - /restart backend     # 重启后端服务
        - /restart all         # 重启所有服务
        - /logs --lines 100    # 查看日志
        """
        text = text.strip()

        if not text.startswith('/'):
            return None

        parts = text.split()
        command = parts[0]
        args = parts[1:]

        if command == '/status':
            return {'action': 'query_status'}
        elif command == '/license':
            if not args:
                return None
            if args[0] == 'status':
                return {'action': 'query_license'}
            elif args[0] == 'generate':
                return {
                    'action': 'generate_license',
                    'params': self._parse_license_args(args[1:])
                }
            elif args[0] == 'revoke':
                return {'action': 'revoke_license'}
        elif command == '/restart':
            if args:
                return {'action': 'restart_service', 'service': args[0]}
            return {'action': 'restart_service', 'service': 'all'}
        elif command == '/logs':
            lines = 50
            for arg in args:
                if arg.startswith('--lines') or arg.startswith('-n'):
                    try:
                        lines = int(args[args.index(arg) + 1])
                    except (IndexError, ValueError):
                        pass
            return {'action': 'show_logs', 'lines': lines}
        elif command == '/help':
            return {'action': 'show_help'}

        return None

    def _parse_license_args(self, args: List[str]) -> Dict:
        """解析授权参数"""
        params = {}
        i = 0
        while i < len(args):
            if args[i] == '--machine':
                params['machine_id'] = args[i + 1] if i + 1 < len(args) else None
            elif args[i] == '--expire':
                params['expire_date'] = args[i + 1] if i + 1 < len(args) else None
            elif args[i] == '--disk':
                params['disk_id'] = args[i + 1] if i + 1 < len(args) else None
            i += 2
        return params

    def _execute_command(self, command: Dict, sender_id: str = None):
        """执行指令"""
        action = command.get('action')
        logger.info(f"执行指令: {action}")

        if action == 'query_status':
            self._cmd_status()
        elif action == 'query_license':
            self._cmd_license_status()
        elif action == 'generate_license':
            self._cmd_generate_license(command.get('params'))
        elif action == 'revoke_license':
            self._cmd_revoke_license()
        elif action == 'restart_service':
            self._cmd_restart(command.get('service'))
        elif action == 'show_logs':
            self._cmd_logs(command.get('lines'))
        elif action == 'show_help':
            self._cmd_help()

    def _cmd_status(self):
        """查询系统状态"""
        import psutil
        import docker

        try:
            # 系统信息
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            uptime_seconds = time.time() - psutil.boot_time()

            # 容器信息
            from app.core.config import settings
            docker_host = getattr(settings, 'DOCKER_HOST', None) or os.environ.get('DOCKER_HOST', '')
            if docker_host and not docker_host.startswith("unix://"):
                client = docker.DockerClient(base_url=docker_host)
            else:
                client = docker.from_env()
            containers = client.containers.list()
            running_count = len([c for c in containers if c.status == 'running'])

            message = f"""📊 **慧学 系统状态**

━━━━━━━━━━━━━━━━━━━━
🖥️ **系统资源**
• CPU 使用: {cpu}%
• 内存使用: {memory.percent}%
• 运行时间: {time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))}

🐳 **容器状态**
• 运行容器: {running_count}/{len(containers)}

━━━━━━━━━━━━━━━━━━━━
_查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"""

            self._send_message(message)

        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            self._send_message(f"获取系统状态失败: {e}")

    def _cmd_license_status(self):
        """查询授权状态"""
        try:
            from app.core.license_validator import LicenseValidator
            validator = LicenseValidator()
            info = validator.get_license_info()

            message = f"""📋 **授权状态查询**

• 过期日期: {info.get('expire_date', '未知')}
• 功能模块: {', '.join(info.get('features', []))}
• 创建时间: {info.get('created', '未知')}
• 机器码: {info.get('machine_id', '未知')[:16]}...

_查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"""

            self._send_message(message)

        except Exception as e:
            self._send_message(f"获取授权状态失败: {e}")

    def _cmd_generate_license(self, params: Dict):
        """生成授权"""
        try:
            from scripts.generate_license import generate_license

            generate_license(
                machine_id=params.get('machine_id'),
                disk_id=params.get('disk_id', 'default'),
                expire_date=params.get('expire_date'),
                features=['all'],
                output='/opt/huixue/license.json'
            )

            message = f"""✅ **授权已生成**

• 过期日期: {params.get('expire_date')}
• 机器码: {params.get('machine_id', '')[:16]}...

请重启服务使授权生效"""

            self._send_message(message)

        except Exception as e:
            self._send_message(f"❌ 生成授权失败: {e}")

    def _cmd_revoke_license(self):
        """撤销授权"""
        import os

        license_path = '/opt/huixue/license.json'
        if os.path.exists(license_path):
            os.remove(license_path)
            self._send_message("⚠️ **授权已撤销**\n\n服务将在下次验证时停止")
        else:
            self._send_message("授权文件不存在")

    def _cmd_restart(self, service: str):
        """重启服务"""
        import docker
        from app.core.config import settings

        try:
            docker_host = getattr(settings, 'DOCKER_HOST', None) or os.environ.get('DOCKER_HOST', '')
            if docker_host and not docker_host.startswith("unix://"):
                client = docker.DockerClient(base_url=docker_host)
            else:
                client = docker.from_env()
            service_map = {
                'backend': 'huixue-backend',
                'frontend': 'huixue-frontend',
                'jupyter': 'huixue-jupyter',
                'all': None
            }

            target = service_map.get(service)
            if target:
                container = client.containers.get(target)
                container.restart()
                self._send_message(f"✅ 服务 **{service}** 已重启")
            else:
                # 重启所有服务
                for container in client.containers.list():
                    if container.name.startswith('huixue-'):
                        container.restart()
                self._send_message("✅ 所有服务已重启")

        except Exception as e:
            self._send_message(f"❌ 重启失败: {e}")

    def _cmd_logs(self, lines: int = 50):
        """查看日志"""
        import subprocess

        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(lines), 'huixue-backend'],
                capture_output=True, text=True, timeout=30
            )
            logs = result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout

            if logs:
                if len(logs) > 1000:
                    self._send_message(f"📜 **日志（最后 {lines} 行）**\n\n{logs[:1000]}...\n\n_（日志过长，仅显示前1000字符）_")
                else:
                    self._send_message(f"📜 **日志（最后 {lines} 行）**\n\n{logs}")
            else:
                self._send_message("暂无日志")

        except Exception as e:
            self._send_message(f"获取日志失败: {e}")

    def _cmd_help(self):
        """显示帮助"""
        help_text = """📖 **可用指令**

- `/status` - 查询系统状态
- `/license status` - 查询授权状态
- `/license generate --machine <机器码> --expire <日期>` - 生成授权
- `/license revoke` - 撤销授权
- `/restart backend|frontend|jupyter|all` - 重启服务
- `/logs --lines <行数>` - 查看日志

_来自: 慧学 运维机器人_"""

        self._send_message(help_text)

    def _is_duplicate(self, message_id: str) -> bool:
        """检查消息是否已处理"""
        now = time.time()

        # 清理 5 分钟前的缓存
        for msg_id, timestamp in list(self._processed_messages.items()):
            if now - timestamp > 300:
                del self._processed_messages[msg_id]

        if message_id in self._processed_messages:
            return True

        self._processed_messages[message_id] = now
        return False

    def poll(self):
        """轮询主循环"""
        logger.info(f"开始轮询飞书消息，间隔: {self.polling_interval}秒")

        while self.running:
            try:
                messages = self._get_messages()

                # 倒序处理（从最新消息开始）
                for message in reversed(messages):
                    message_id = message.get("message_id")

                    if self._is_duplicate(message_id):
                        continue

                    # 获取消息内容
                    content = self._get_message_content(message_id)
                    if not content:
                        continue

                    text_content = content.get("text", "")
                    logger.info(f"收到消息: {text_content}")

                    # 解析并执行指令
                    command = self._parse_command(text_content)
                    if command:
                        self._execute_command(command)

            except Exception as e:
                logger.error(f"轮询异常: {e}")

            # 等待下一次轮询
            time.sleep(self.polling_interval)

    def start(self, daemon: bool = True):
        """启动轮询器（后台线程）"""
        self.running = True
        thread = Thread(target=self.poll, daemon=daemon)
        thread.start()
        logger.info(f"✓ 飞书消息轮询已启动，间隔: {self.polling_interval}秒")

    def stop(self):
        """停止轮询器"""
        self.running = False
        logger.info("飞书消息轮询已停止")


def get_poller() -> FeishuPoller:
    """获取全局轮询器实例"""
    return FeishuPoller()


def start_poller():
    """启动轮询器"""
    get_poller().start()


def stop_poller():
    """停止轮询器"""
    get_poller().stop()


def main():
    """主函数 - 启动轮询器"""
    logger.info("=" * 50)
    logger.info("飞书消息轮询器启动中...")
    logger.info("=" * 50)

    try:
        poller = FeishuPoller()
        poller.start()

        # 保持运行
        import signal
        import sys

        def signal_handler(sig, frame):
            logger.info("\n正在停止轮询器...")
            poller.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 阻塞等待
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"运行错误: {e}")
        sys.exit(1)


# 兼容别名（与文档保持一致）
def start_message_poller():
    """启动消息轮询器（兼容别名）"""
    start_poller()


def stop_message_poller():
    """停止消息轮询器（兼容别名）"""
    stop_poller()


if __name__ == '__main__':
    main()
