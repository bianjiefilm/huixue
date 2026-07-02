#!/usr/bin/env python3
"""
资源加密工具 - Fernet对称加密方案

功能：
- 加密 ziyuan_data 目录中的敏感文件
- 支持解密操作（用于管理员查看）
- 生成加密密钥文件

使用方式：
1. 生成密钥（首次）：
   python encrypt_resources.py --gen-key

2. 加密资源：
   python encrypt_resources.py --encrypt --input /path/to/ziyuan_data --key key.txt

3. 解密资源：
   python encrypt_resources.py --decrypt --input /path/to/ziyuan_data --key key.txt
"""

import os
import sys
import json
import argparse
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from datetime import datetime


def generate_key(output_path: str = "resource_key.txt") -> str:
    """生成 Fernet 密钥"""
    key = Fernet.generate_key()

    # 同时生成备份的 Base64 编码密钥（用于非 Fernet 解密）
    key_b64 = base64.b64encode(key).decode()

    with open(output_path, 'w') as f:
        f.write(f"# Fernet 密钥\n")
        f.write(f"# 生成时间: {datetime.now().isoformat()}\n")
        f.write(f"# 请妥善保管此密钥！\n\n")
        f.write(f"# Fernet格式（主密钥）\n")
        f.write(f"{key.decode()}\n\n")
        f.write(f"# Base64格式（备份）\n")
        f.write(f"{key_b64}\n")

    print(f"✓ 密钥已生成: {output_path}")
    print(f"  主密钥: {key.decode()[:20]}...")
    return key.decode()


def load_key(key_path: str) -> bytes:
    """加载密钥"""
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"密钥文件不存在: {key_path}")

    with open(key_path, 'r') as f:
        content = f.read()

    # 尝试读取 Fernet 格式
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                return line.encode()
            except Exception:
                continue

    raise ValueError("无法解析密钥文件")


def encrypt_file(input_path: str, output_path: str, fernet: Fernet):
    """加密单个文件"""
    with open(input_path, 'rb') as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(output_path, 'wb') as f:
        f.write(encrypted)


def decrypt_file(input_path: str, output_path: str, fernet: Fernet):
    """解密单个文件"""
    with open(input_path, 'rb') as f:
        data = f.read()

    decrypted = fernet.decrypt(data)

    with open(output_path, 'wb') as f:
        f.write(decrypted)


def encrypt_directory(input_dir: str, output_dir: str, key_path: str, file_patterns: list = None):
    """
    加密目录中的所有文件

    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        key_path: 密钥文件路径
        file_patterns: 要加密的文件模式（默认：敏感文件）
    """
    # 默认敏感文件模式
    if file_patterns is None:
        file_patterns = [
            '*.py', '*.ipynb', '*.md', '*.txt',
            '*.json', '*.csv', '*.xlsx',
            '*.pdf', '*.docx', '*.pptx'
        ]

    key = load_key(key_path)
    fernet = Fernet(key)

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    encrypted_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(input_path):
        # 计算相对路径
        rel_path = Path(root).relative_to(input_path)

        # 创建对应的输出目录
        dest_dir = output_path / rel_path
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            src_file = Path(root) / file

            # 检查是否需要加密
            should_encrypt = False
            for pattern in file_patterns:
                if src_file.match(pattern):
                    should_encrypt = True
                    break

            if not should_encrypt:
                # 直接复制文件
                dest_file = dest_dir / file
                with open(src_file, 'rb') as f:
                    data = f.read()
                with open(dest_file, 'wb') as f:
                    f.write(data)
                skipped_count += 1
                continue

            # 加密文件
            dest_file = dest_dir / (file + '.enc')
            try:
                encrypt_file(str(src_file), str(dest_file), fernet)
                encrypted_count += 1
                print(f"  加密: {src_file.relative_to(input_path)} -> {dest_file.relative_to(output_path)}")
            except Exception as e:
                print(f"  错误: {src_file.relative_to(input_path)} - {e}")

    print(f"\n✓ 加密完成")
    print(f"  加密文件: {encrypted_count}")
    print(f"  跳过文件: {skipped_count}")
    print(f"  输出目录: {output_dir}")

    return encrypted_count


def decrypt_directory(input_dir: str, output_dir: str, key_path: str):
    """
    解密目录中的所有加密文件
    """
    key = load_key(key_path)
    fernet = Fernet(key)

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    decrypted_count = 0

    for root, dirs, files in os.walk(input_path):
        rel_path = Path(root).relative_to(input_path)
        dest_dir = output_path / rel_path
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            src_file = Path(root) / file

            if not file.endswith('.enc'):
                # 直接复制非加密文件
                dest_file = dest_dir / file
                with open(src_file, 'rb') as f:
                    data = f.read()
                with open(dest_file, 'wb') as f:
                    f.write(data)
                continue

            # 解密文件
            orig_name = file[:-4]  # 移除 .enc 后缀
            dest_file = dest_dir / orig_name
            try:
                decrypt_file(str(src_file), str(dest_file), fernet)
                decrypted_count += 1
                print(f"  解密: {src_file.relative_to(input_path)} -> {dest_file.relative_to(output_path)}")
            except Exception as e:
                print(f"  错误: {src_file.relative_to(input_path)} - {e}")

    print(f"\n✓ 解密完成")
    print(f"  解密文件: {decrypted_count}")
    print(f"  输出目录: {output_dir}")

    return decrypted_count


def create_encrypted_resource_loader(key_path: str, output_path: str = "resource_loader.py"):
    """
    生成资源加载器模块（用于运行时解密）

    生成的代码会被嵌入到应用中，自动解密并缓存资源文件
    """
    key = load_key(key_path).decode()

    loader_code = f'''"""
自动资源加载器 - 运行时解密

此模块自动解密加密的资源文件并提供缓存支持
"""

import os
import hashlib
from cryptography.fernet import Fernet

# 加密密钥
_RESOURCE_KEY = "{key}"

# 缓存目录
_CACHE_DIR = "/tmp/ziyuan_cache"

# Fernet 实例
_FERNET = Fernet(_RESOURCE_KEY.encode())


def get_cached_file(resource_path: str) -> str:
    """
    获取缓存的资源文件

    Args:
        resource_path: 资源文件路径（加密文件）

    Returns:
        解密后的文件路径（缓存）
    """
    os.makedirs(_CACHE_DIR, exist_ok=True)

    # 计算文件哈希作为缓存键
    file_hash = hashlib.md5(resource_path.encode()).hexdigest()
    cache_file = os.path.join(_CACHE_DIR, file_hash)

    # 检查缓存是否存在且有效
    if os.path.exists(cache_file):
        # 检查源文件是否更新
        src_mtime = os.path.getmtime(resource_path)
        cache_mtime = os.path.getmtime(cache_file)
        if cache_mtime >= src_mtime:
            return cache_file

    # 解密并缓存
    with open(resource_path, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = _FERNET.decrypt(encrypted_data)

    with open(cache_file, 'wb') as f:
        f.write(decrypted_data)

    return cache_file


def clear_cache():
    """清除缓存"""
    import shutil
    if os.path.exists(_CACHE_DIR):
        shutil.rmtree(_CACHE_DIR)
    os.makedirs(_CACHE_DIR, exist_ok=True)
'''

    with open(output_path, 'w') as f:
        f.write(loader_code)

    print(f"✓ 资源加载器已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='资源加密工具')
    parser.add_argument('--gen-key', action='store_true', help='生成新密钥')
    parser.add_argument('--key', default='resource_key.txt', help='密钥文件路径')
    parser.add_argument('--encrypt', action='store_true', help='加密模式')
    parser.add_argument('--decrypt', action='store_true', help='解密模式')
    parser.add_argument('--input', required=True, help='输入目录')
    parser.add_argument('--output', help='输出目录（默认：input_encrypted 或 input_decrypted）')
    parser.add_argument('--loader', action='store_true', help='生成资源加载器')

    args = parser.parse_args()

    if args.gen_key:
        generate_key(args.key)
        return

    if not os.path.exists(args.input):
        print(f"错误: 输入目录不存在: {args.input}")
        sys.exit(1)

    if not os.path.exists(args.key):
        print(f"错误: 密钥文件不存在: {args.key}")
        print("请先使用 --gen-key 生成密钥")
        sys.exit(1)

    if args.encrypt:
        output_dir = args.output or (args.input + "_encrypted")
        encrypt_directory(args.input, output_dir, args.key)

        if args.loader:
            create_encrypted_resource_loader(args.key)

    elif args.decrypt:
        output_dir = args.output or (args.input + "_decrypted")
        decrypt_directory(args.input, output_dir, args.key)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
