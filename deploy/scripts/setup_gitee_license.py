#!/usr/bin/env python3
"""
Gitee 授权一键配置工具

功能：
- 生成机器码
- 在 Gitee 仓库创建 license.json
- 生成环境变量配置

使用方法：
1. 先创建 Gitee Token:
   https://gitee.com/profile/personal_access_tokens
   勾选: repo (仓库操作)

2. 运行脚本：
   python setup_gitee_license.py --token 你的Token

3. 复制输出的环境变量到服务器
"""

import os
import sys
import json
import requests
import hashlib
import uuid
import socket
import argparse
from datetime import datetime

# 配置
GITEE_TOKEN = None
GITEE_OWNER = "noderead"
GITEE_REPO = "huixuejson"

BASE_URL = "https://gitee.com/api/v5"

# 颜色输出
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'


def ok(msg):
    print(f"{GREEN}[OK] {msg}{NC}")


def fail(msg):
    print(f"{RED}[FAIL] {msg}{NC}")


def warn(msg):
    print(f"{YELLOW}[WARN] {msg}{NC}")


def info(msg):
    print(f"{CYAN}[INFO] {msg}{NC}")


def banner():
    print(f"""
{CYAN}╔════════════════════════════════════════════════════════════╗
║       慧学 - Gitee 授权配置工具                  ║
╚════════════════════════════════════════════════════════════╝{NC}
    """)


def get_headers(token):
    return {
        "Authorization": f"token {token}",
        "Content-Type": "application/json; charset=utf-8"
    }


def get_machine_code():
    """获取本机机器码"""
    identifiers = [
        f"mac:{':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])}",
        f"host:{socket.gethostname()}"
    ]
    return hashlib.sha256(':'.join(identifiers).encode()).hexdigest()


def check_repo_exists(token, owner, repo):
    """检查仓库是否存在"""
    url = f"{BASE_URL}/repos/{owner}/{repo}"
    response = requests.get(url, headers=get_headers(token))
    return response.status_code == 200


def create_license(token, owner, repo, machine_code, expire_date):
    """创建授权文件"""
    content = {
        "enabled": True,
        "machine_code": machine_code,
        "expire_date": expire_date,
        "message": "授权正常",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 获取当前文件的 SHA
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/license.json"
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None

    # 创建/更新文件
    data = {
        "access_token": token,
        "content": json.dumps(content, indent=2, ensure_ascii=False),
        "message": f"授权创建: {machine_code[:16]}"
    }
    if sha:
        data['sha'] = sha

    response = requests.put(url, json=data, headers=headers)
    response.raise_for_status()

    return response.json()


def get_license_url(owner, repo):
    """生成 license 文件的 Raw URL"""
    return f"https://gitee.com/{owner}/{repo}/raw/main/license.json"


def main():
    banner()

    parser = argparse.ArgumentParser(description='Gitee 授权配置')
    parser.add_argument('--token', type=str, required=True, help='Gitee Personal Access Token')
    parser.add_argument('--expire', type=str, default='2026-12-31', help='过期日期 (YYYY-MM-DD)')
    parser.add_argument('--owner', type=str, default='noderead', help='Gitee 用户名')

    args = parser.parse_args()

    GITEE_TOKEN = args.token
    GITEE_OWNER = args.owner

    # 1. 检查仓库
    info(f"检查仓库: {GITEE_OWNER}/{GITEE_REPO}")
    if not check_repo_exists(GITEE_TOKEN, GITEE_OWNER, GITEE_REPO):
        fail(f"仓库不存在: https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}")
        print(f"\n请先创建仓库:")
        print(f"  1. 访问 https://gitee.com/{GITEE_OWNER}/huixuejson")
        print(f"  2. 点击 '创建仓库'（私有）")
        return 1

    ok("仓库存在")

    # 2. 生成机器码
    info("生成机器码...")
    machine_code = get_machine_code()
    print(f"\n机器码: {machine_code}")
    print(f"短码:   {machine_code[:16]}")

    # 3. 创建授权文件
    info("创建授权文件...")
    try:
        result = create_license(GITEE_TOKEN, GITEE_OWNER, GITEE_REPO, machine_code, args.expire)
        ok("授权文件已创建/更新")
    except Exception as e:
        fail(f"创建授权失败: {e}")
        return 1

    # 4. 生成配置
    license_url = get_license_url(GITEE_OWNER, GITEE_REPO)

    print(f"""
{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}

授权配置完成！

{CYAN}【Gitee 仓库】{NC}
  URL: https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}

{CYAN}【授权文件 Raw URL】{NC}
  {license_url}

{CYAN}【服务器环境变量配置】{NC}
  在三台服务器上设置以下环境变量：

  # 编辑 ~/.bashrc 或 /etc/profile
  export LICENSE_URL="{license_url}"
  export LICENSE_TOKEN="{GITEE_TOKEN}"  # 私有仓库需要

  # 或添加到 docker-stack.yml 的环境变量

{CYAN}【验证授权】{NC}
  # 查看机器码（复制到 Gitee 授权）
  python setup_gitee_license.py --token {GITEE_TOKEN} --machine

  # 检查授权状态
  python setup_gitee_license.py --token {GITEE_TOKEN} --check

{CYAN}【控制授权】{NC}
  # 停用服务
  python setup_gitee_license.py --token {GITEE_TOKEN} --disable

  # 启用服务
  python setup_gitee_license.py --token {GITEE_TOKEN} --enable

{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}
    """)

    return 0


if __name__ == '__main__':
    sys.exit(main())
