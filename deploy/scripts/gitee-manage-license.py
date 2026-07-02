#!/usr/bin/env python3
"""
Gitee 授权管理工具

功能：
- 生成机器码
- 创建/更新授权仓库
- 检查授权状态

使用方法：
1. 创建 Gitee Personal Access Token:
   - https://gitee.com/profile/personal_access_tokens
   - 需要 repo 权限

2. 运行工具：
   python gitee-manage-license.py --create    # 创建授权
   python gitee-manage-license.py --check     # 检查授权
   python gitee-manage-license.py --disable   # 停用授权
   python gitee-manage-license.py --machine   # 查看机器码

3. 环境变量：
   export GITEE_TOKEN=你的Token
   export GITEE_OWNER=你的用户名
   export GITEE_REPO=仓库名（如 tempo-license）
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
GITEE_TOKEN = os.environ.get('GITEE_TOKEN')
GITEE_OWNER = os.environ.get('GITEE_OWNER')
GITEE_REPO = os.environ.get('GITEE_REPO', 'tempo-license')

BASE_URL = "https://gitee.com/api/v5"

# 颜色输出
RED = '\033[0;31m'
GREEN = '\033[0;32m'
CYAN = '\033[0;36m'
NC = '\033[0m'


def ok(msg):
    print(f"{GREEN}[OK] {msg}{NC}")


def fail(msg):
    print(f"{RED}[FAIL] {msg}{NC}")


def info(msg):
    print(f"{CYAN}[INFO] {msg}{NC}")


def get_headers():
    """获取请求头"""
    if not GITEE_TOKEN:
        fail("请设置环境变量 GITEE_TOKEN")
        sys.exit(1)
    return {
        "Authorization": f"token {GITEE_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }


def get_machine_code():
    """获取本机机器码"""
    identifiers = [
        f"mac:{':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])}",
        f"host:{socket.gethostname()}"
    ]

    return hashlib.sha256(':'.join(identifiers).encode()).hexdigest()


def ensure_repo():
    """确保仓库存在"""
    if not GITEE_OWNER:
        fail("请设置环境变量 GITEE_OWNER（你的 Gitee 用户名）")
        sys.exit(1)

    url = f"{BASE_URL}/repos/{GITEE_OWNER}/{GITEE_REPO}"
    response = requests.get(url, headers=get_headers())

    if response.status_code == 404:
        # 创建仓库
        info("创建授权仓库...")
        url = f"{BASE_URL}/user/repos"
        data = {
            "name": GITEE_REPO,
            "description": "慧学 授权文件",
            "private": True,
            "auto_init": True
        }
        response = requests.post(url, json=data, headers=get_headers())
        response.raise_for_status()
        ok("仓库创建成功")
    else:
        response.raise_for_status()

    return response.json()


def create_license(machine_code: str, expire_date: str = "2026-12-31"):
    """创建授权"""
    ensure_repo()

    content = {
        "enabled": True,
        "machine_code": machine_code,
        "expire_date": expire_date,
        "message": "授权正常",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 获取当前文件的 SHA（如果是更新）
    url = f"{BASE_URL}/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/license.json"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None

    # 创建/更新文件
    data = {
        "access_token": GITEE_TOKEN,
        "content": json.dumps(content, indent=2, ensure_ascii=False),
        "message": f"更新授权: {machine_code[:16]}"
    }
    if sha:
        data['sha'] = sha

    response = requests.put(url, json=data, headers=headers)
    response.raise_for_status()

    result = response.json()
    ok("授权已创建/更新")

    print(f"\n请设置环境变量:")
    print(f"  export LICENSE_URL={result.get('content', {}).get('download_url', '待获取')}")
    print(f"\n或者在 Gitee 中获取 Raw URL:")
    print(f"  https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/raw/main/license.json")

    return result


def get_license():
    """获取授权状态"""
    if not GITEE_OWNER:
        fail("请设置环境变量 GITEE_OWNER")
        return None

    url = f"{BASE_URL}/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/license.json"
    params = {"access_token": GITEE_TOKEN}

    response = requests.get(url, params=params)
    if response.status_code == 404:
        return None

    response.raise_for_status()

    content = response.json().get('content', '')
    import base64
    return json.loads(base64.b64decode(content).decode('utf-8'))


def check_license(machine_code: str = None):
    """检查授权状态"""
    license_info = get_license()
    if not license_info:
        fail("授权文件不存在")
        print("\n创建授权:")
        print(f"  python gitee-manage-license.py --create --expire 2026-12-31")
        return False

    print(f"\n{'='*50}")
    print("授权状态")
    print(f"{'='*50}")

    enabled = license_info.get('enabled', False)
    expire_date = license_info.get('expire_date', '未设置')
    message = license_info.get('message', '')

    if enabled:
        ok(f"状态: ✅ 正常")
    else:
        fail(f"状态: 🚨 已停用")

    info(f"过期日期: {expire_date}")
    info(f"消息: {message}")

    if machine_code:
        gist_machine = license_info.get('machine_code', '')
        if machine_code == gist_machine:
            ok("机器码匹配")
        else:
            info(f"机器码: {machine_code[:16]}...")
            info(f"授权机器: {gist_machine[:16]}...")

    print(f"{'='*50}\n")

    return enabled


def update_license(enabled: bool = None, expire_date: str = None, message: str = None):
    """更新授权"""
    ensure_repo()

    current = get_license() or {}

    if enabled is not None:
        current['enabled'] = enabled
    if expire_date:
        current['expire_date'] = expire_date
    if message:
        current['message'] = message

    current['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 获取 SHA
    url = f"{BASE_URL}/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/license.json"
    params = {"access_token": GITEE_TOKEN}
    response = requests.get(url, params=params)
    sha = response.json().get('sha')

    # 更新
    data = {
        "access_token": GITEE_TOKEN,
        "content": json.dumps(current, indent=2, ensure_ascii=False),
        "message": f"更新授权状态: {enabled}",
        "sha": sha
    }

    response = requests.put(url, json=data, headers=get_headers())
    response.raise_for_status()

    ok("授权已更新")


def disable_license():
    """停用授权"""
    update_license(enabled=False, message="授权已停用")
    fail("授权已停用，服务将在下次检查时停止")


def enable_license():
    """启用授权"""
    update_license(enabled=True, message="授权已恢复")
    ok("授权已恢复")


def main():
    parser = argparse.ArgumentParser(description='慧学 授权管理 (Gitee 方案)')
    parser.add_argument('--create', action='store_true', help='创建授权')
    parser.add_argument('--check', action='store_true', help='检查授权状态')
    parser.add_argument('--disable', action='store_true', help='停用授权')
    parser.add_argument('--enable', action='store_true', help='启用授权')
    parser.add_argument('--machine', action='store_true', help='显示本机机器码')
    parser.add_argument('--expire', type=str, default='2026-12-31', help='过期日期')

    args = parser.parse_args()

    if args.machine:
        code = get_machine_code()
        print(f"\n本机机器码:\n{code}\n")
        print(f"短码: {code[:16]}")
        return

    if args.create:
        machine = get_machine_code()
        create_license(machine, args.expire)
        return

    if args.check:
        machine = get_machine_code()
        check_license(machine)
        return

    if args.disable:
        disable_license()
        return

    if args.enable:
        enable_license()
        return

    parser.print_help()
    print("\n使用示例:")
    print("  # 设置环境变量")
    print("  export GITEE_TOKEN=your_token")
    print("  export GITEE_OWNER=your_username")
    print("")
    print("  # 查看机器码")
    print("  python gitee-manage-license.py --machine")
    print("")
    print("  # 创建授权")
    print("  python gitee-manage-license.py --create --expire 2026-12-31")
    print("")
    print("  # 检查授权")
    print("  python gitee-manage-license.py --check")
    print("")
    print("  # 停用授权")
    print("  python gitee-manage-license.py --disable")


if __name__ == '__main__':
    main()
