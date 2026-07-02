#!/usr/bin/env python3
"""
License 生成工具

使用方式：
python generate_license.py --machine-id XXX --disk-id YYY --expire 2026-12-31 --output license.json
"""

import argparse
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path


def generate_license(
    machine_id: str,
    disk_id: str,
    expire_date: str,
    features: list = None,
    output: str = 'license.json'
):
    """生成授权文件"""

    # 验证日期格式
    try:
        datetime.strptime(expire_date, '%Y-%m-%d')
    except ValueError:
        print(f"错误：无效的日期格式 '{expire_date}'，请使用 YYYY-MM-DD 格式")
        sys.exit(1)

    # 构建授权数据
    license_data = {
        'machine_id': machine_id,
        'disk_id': disk_id,
        'expire_date': expire_date,
        'features': features or ['all'],
        'created': datetime.now().strftime('%Y-%m-%d'),
        'created_by': '慧学 License Generator',
        'version': '1.0'
    }

    # 生成签名
    data_to_sign = {
        'machine_id': machine_id,
        'disk_id': disk_id,
        'expire_date': expire_date,
        'features': license_data['features']
    }

    data_str = json.dumps(data_to_sign, sort_keys=True)
    signature = hashlib.sha256(data_str.encode()).hexdigest()
    license_data['signature'] = signature

    # 保存文件
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(license_data, f, indent=2, ensure_ascii=False)

    print(f"✓ 授权文件已生成: {output}")
    print(f"\n授权信息:")
    print(f"  机器码: {machine_id}")
    print(f"  硬盘ID: {disk_id}")
    print(f"  过期日期: {expire_date}")
    print(f"  功能模块: {', '.join(license_data['features'])}")

    return license_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成 慧学 授权文件')
    parser.add_argument('--machine-id', required=True, help='机器特征码（MAC地址哈希）')
    parser.add_argument('--disk-id', required=True, help='硬盘序列号')
    parser.add_argument('--expire', required=True, help='过期日期 (YYYY-MM-DD)')
    parser.add_argument('--features', nargs='+', default=['all'], help='授权功能模块')
    parser.add_argument('--output', default='license.json', help='输出文件名')

    args = parser.parse_args()

    generate_license(
        machine_id=args.machine_id,
        disk_id=args.disk_id,
        expire_date=args.expire,
        features=args.features,
        output=args.output
    )
