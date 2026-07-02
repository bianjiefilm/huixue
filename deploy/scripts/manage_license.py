#!/usr/bin/env python3
"""
GitHub Gist 授权管理工具

功能：
- 生成机器码
- 创建/更新授权 Gist
- 查看当前授权状态

使用方法：
1. 创建 GitHub Personal Access Token:
   - https://github.com/settings/tokens
   - 需要 gist 权限

2. 运行工具：
   python manage_license.py --create    # 创建授权
   python manage_license.py --check     # 检查授权
   python manage_license.py --disable   # 停用授权
   python manage_license.py --machine   # 查看机器码
"""

import os
import sys
import json
import requests
import hashlib
import uuid
import subprocess
import argparse
from datetime import datetime

# 配置
GIST_TOKEN = os.environ.get('GITHUB_TOKEN')  # GitHub Personal Access Token
GIST_ID = os.environ.get('GIST_ID')  # 已存在的 Gist ID

# 颜色输出
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'


def print_ok(msg):
    print(f"{GREEN}[OK] {msg}{NC}")


def print_fail(msg):
    print(f"{RED}[FAIL] {msg}{NC}")


def print_info(msg):
    print(f"{CYAN}[INFO] {msg}{NC}")


def get_machine_code():
    """获取本机机器码"""
    identifiers = []

    # MAC 地址
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])
    identifiers.append(f"mac:{mac}")

    # 主机名
    hostname = subprocess.check_output(['hostname'], text=True).strip()
    identifiers.append(f"host:{hostname}")

    # CPU 信息
    try:
        cpuinfo = subprocess.check_output(['cat', '/proc/cpuinfo'], text=True)
        for line in cpuinfo.split('\n'):
            if 'Serial' in line:
                identifiers.append(f"cpu:{line.split(':')[-1].strip()}")
                break
    except:
        pass

    # 磁盘信息
    try:
        disk = subprocess.check_output(
            ['cat', '/sys/class/block/sda/device/serial'],
            text=True
        ).strip()
        identifiers.append(f"disk:{disk}")
    except:
        pass

    machine_code = hashlib.sha256(
        ':'.join(identifiers).encode()
    ).hexdigest()

    return machine_code


def get_headers():
    """获取请求头"""
    if not GIST_TOKEN:
        print_fail("请设置环境变量 GITHUB_TOKEN")
        sys.exit(1)
    return {
        "Authorization": f"token {GIST_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }


def create_gist(machine_code: str, expire_date: str = None):
    """创建新的授权 Gist"""
    print_info("创建授权 Gist...")

    description = f"慧学 License - {machine_code[:16]}"

    files = {
        "license.json": {
            "content": json.dumps({
                "enabled": True,
                "machine_code": machine_code,
                "expire_date": expire_date or "2026-12-31",
                "message": "授权正常",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, indent=2, ensure_ascii=False)
        },
        "README.md": {
            "content": f"""# 慧学 授权文件

## 机器码
```
{machine_code}
```

## 授权状态
- ✅ 启用

## 使用方法
将此 Gist ID 设置到服务环境变量：
```
GIST_ID=此处的ID
```

## 手动控制
编辑 `license.json` 文件：
- `enabled: false` - 停用服务
- `enabled: true` - 启用服务
- `expire_date` - 设置过期日期
"""
        }
    }

    url = "https://api.github.com/gists"
    data = {
        "description": description,
        "public": False,  # 私有 Gist
        "files": files
    }

    response = requests.post(url, json=data, headers=get_headers())
    response.raise_for_status()

    result = response.json()
    gist_id = result.get('id')
    print_ok(f"Gist 创建成功！")
    print_info(f"Gist ID: {gist_id}")
    print_info(f"URL: {result.get('html_url')}")
    print(f"\n请设置环境变量:")
    print(f"  export GIST_ID={gist_id}")
    print(f"  export GITHUB_TOKEN={GIST_TOKEN}")

    return gist_id


def update_gist(gist_id: str, enabled: bool = None, expire_date: str = None, message: str = None):
    """更新授权 Gist"""
    print_info(f"更新授权 Gist: {gist_id}")

    # 获取当前内容
    url = f"https://api.github.com/gists/{gist_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()

    result = response.json()
    current_content = json.loads(result['files']['license.json']['content'])

    # 更新内容
    if enabled is not None:
        current_content['enabled'] = enabled
    if expire_date:
        current_content['expire_date'] = expire_date
    if message:
        current_content['message'] = message

    current_content['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 更新文件
    url = f"https://api.github.com/gists/{gist_id}"
    data = {
        "files": {
            "license.json": {
                "content": json.dumps(current_content, indent=2, ensure_ascii=False)
            }
        }
    }

    response = requests.patch(url, json=data, headers=get_headers())
    response.raise_for_status()

    print_ok("授权已更新")

    return current_content


def get_license(gist_id: str = None):
    """获取授权状态"""
    target_id = gist_id or GIST_ID
    if not target_id:
        print_fail("请指定 GIST_ID")
        return None

    # 如果是公开 Gist（没有 token），直接获取 raw
    if not GIST_TOKEN:
        raw_url = f"https://gist.githubusercontent.com/anonymous/{target_id}/raw/license.json"
        try:
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            pass

    # 使用 API
    url = f"https://api.github.com/gists/{target_id}"
    headers = get_headers() if GIST_TOKEN else {}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    result = response.json()
    return json.loads(result['files']['license.json']['content'])


def check_license(machine_code: str = None):
    """检查授权状态"""
    license_info = get_license()
    if not license_info:
        print_fail("无法获取授权信息")
        return False

    print(f"\n{'='*50}")
    print("授权状态")
    print(f"{'='*50}")

    enabled = license_info.get('enabled', False)
    expire_date = license_info.get('expire_date', '未设置')
    message = license_info.get('message', '')

    if enabled:
        print_ok(f"状态: ✅ 正常")
    else:
        print_fail(f"状态: 🚨 已停用")

    print_info(f"过期日期: {expire_date}")
    print_info(f"消息: {message}")

    # 检查机器码（如果有）
    if machine_code and license_info.get('machine_code'):
        gist_machine = license_info['machine_code']
        if machine_code == gist_machine:
            print_ok("机器码匹配")
        else:
            print_warn(f"机器码不匹配")
            print_info(f"本机: {machine_code[:16]}...")
            print_info(f"授权: {gist_machine[:16]}...")

    print(f"{'='*50}\n")

    return enabled


def disable_license(gist_id: str = None):
    """停用授权"""
    update_gist(gist_id or GIST_ID, enabled=False, message="授权已停用")
    print_ok("授权已停用，服务将在下次检查时停止")


def enable_license(gist_id: str = None):
    """启用授权"""
    update_gist(gist_id or GIST_ID, enabled=True, message="授权已恢复")
    print_ok("授权已恢复")


def main():
    parser = argparse.ArgumentParser(description='慧学 授权管理')
    parser.add_argument('--create', action='store_true', help='创建新授权')
    parser.add_argument('--check', action='store_true', help='检查授权状态')
    parser.add_argument('--disable', action='store_true', help='停用授权')
    parser.add_argument('--enable', action='store_true', help='启用授权')
    parser.add_argument('--machine', action='store_true', help='显示本机机器码')
    parser.add_argument('--gist', type=str, help='指定 Gist ID')
    parser.add_argument('--expire', type=str, default='2026-12-31', help='过期日期 (YYYY-MM-DD)')

    args = parser.parse_args()

    if args.machine:
        code = get_machine_code()
        print(f"\n本机机器码:\n{code}\n")
        print(f"短码: {code[:16]}")
        return

    if args.create:
        machine = get_machine_code()
        create_gist(machine, args.expire)
        return

    if args.check:
        machine = get_machine_code() if GIST_ID else None
        check_license(machine)
        return

    if args.disable:
        disable_license(args.gist)
        return

    if args.enable:
        enable_license(args.gist)
        return

    # 默认显示帮助
    parser.print_help()
    print("\n示例:")
    print("  # 查看本机机器码")
    print("  python manage_license.py --machine")
    print("")
    print("  # 创建授权（GITHUB_TOKEN 需提前设置）")
    print("  export GITHUB_TOKEN=your_token")
    print("  python manage_license.py --create")
    print("")
    print("  # 检查授权")
    print("  export GIST_ID=your_gist_id")
    print("  python manage_license.py --check")
    print("")
    print("  # 停用授权")
    print("  python manage_license.py --disable")


if __name__ == '__main__':
    main()
