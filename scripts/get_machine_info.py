#!/usr/bin/env python3
"""
机器码获取工具

功能：
- 获取机器唯一标识（MAC地址、硬盘序列号、CPU ID等）
- 生成用于授权绑定的机器特征码
"""

import hashlib
import uuid
import os
from typing import Tuple, Optional


class MachineIdentifier:
    """机器标识符获取器"""

    def __init__(self):
        self._mac_address: Optional[str] = None
        self._disk_serial: Optional[str] = None
        self._cpu_id: Optional[str] = None

    def get_mac_address(self) -> str:
        """获取 MAC 地址（格式化）"""
        if self._mac_address:
            return self._mac_address

        mac = ""
        # 尝试多个可能的网络接口名称
        for path in ['/sys/class/net/eth0/address',
                     '/sys/class/net/ens33/address',
                     '/sys/class/net/enp0s3/address',
                     '/sys/class/net/ens160/address']:
            if os.path.exists(path):
                try:
                    mac = open(path).read().strip()
                    if mac:
                        break
                except Exception:
                    pass

        if not mac:
            # 备选方案：使用机器唯一标识
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff)
                           for i in range(0, 48, 8)])

        self._mac_address = mac.lower()
        return self._mac_address

    def get_disk_serial(self) -> str:
        """获取硬盘序列号"""
        if self._disk_serial:
            return self._disk_serial

        try:
            # 方法1: 使用 lsblk
            result = os.popen('lsblk -no serial /dev/sda 2>/dev/null').read().strip()
            if result:
                self._disk_serial = result
                return result

            # 方法2: 使用 hdparm
            result = os.popen('hdparm -i /dev/sda 2>/dev/null | grep SerialNo').read()
            if result:
                self._disk_serial = result.split('=')[1].strip().strip('<')
                return self._disk_serial

            # 方法3: 使用 smartctl
            result = os.popen('smartctl -i /dev/sda 2>/dev/null | grep "Serial Number"').read()
            if result:
                self._disk_serial = result.split(':')[-1].strip()
                return self._disk_serial
        except Exception as e:
            print(f"获取硬盘序列号失败: {e}")

        # 备选：使用根分区 UUID
        try:
            with open('/etc/fstab', 'r') as f:
                content = f.read()
                if 'UUID=' in content:
                    for line in content.split('\n'):
                        if 'UUID=' in line and '/' in line:
                            parts = line.split()
                            for part in parts:
                                if part.startswith('UUID='):
                                    self._disk_serial = part[5:32]  # UUID 长度
                                    return self._disk_serial
        except Exception:
            pass

        return self._disk_serial or "unknown"

    def get_hostname(self) -> str:
        """获取主机名"""
        return os.popen('hostname').read().strip()

    def get_ip_address(self) -> str:
        """获取内网 IP 地址"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 不需要实际连接
            s.connect(("172.16.100.41", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def get_machine_code(self) -> str:
        """
        生成机器特征码（用于授权绑定）

        组合 MAC + 硬盘序列号，生成 MD5 哈希
        """
        mac = self.get_mac_address()
        disk = self.get_disk_serial()

        # 组合标识符
        identifier = f"{mac}:{disk}"

        # 生成 MD5 哈希
        machine_code = hashlib.md5(identifier.encode()).hexdigest()

        return machine_code

    def get_machine_info(self) -> dict:
        """获取完整的机器信息（用于调试）"""
        return {
            'hostname': self.get_hostname(),
            'mac_address': self.get_mac_address(),
            'ip_address': self.get_ip_address(),
            'disk_serial': self.get_disk_serial(),
            'machine_code': self.get_machine_code(),
            'platform': os.uname().sysname,
            'platform_release': os.uname().release,
        }


def main():
    """主函数"""
    identifier = MachineIdentifier()
    info = identifier.get_machine_info()

    print("=" * 60)
    print("机器信息")
    print("=" * 60)
    for key, value in info.items():
        print(f"{key}: {value}")
    print("=" * 60)
    print(f"\n机器码 (machine_code): {info['machine_code']}")
    print("\n将此机器码提供给管理员以生成授权文件")


if __name__ == '__main__':
    main()
