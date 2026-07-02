#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 修复版
"""

import uvicorn
import sys
import socket
import os

# 设置环境变量以支持UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

def find_free_port(start_port=8000, max_attempts=1):
    """查找可用端口，默认使用8000"""
    # 优先使用8000端口
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 8000))
            return 8000
    except OSError:
        # 如果8000不可用，查找其他可用端口
        for port in range(8001, 8001 + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
    return None

def main():
    """主函数"""
    try:
        # 先测试导入是否正常
        from app.main import app
        
        # 查找可用端口
        port = find_free_port()  # 默认使用8000
        if port is None:
            print("ERROR: 无法找到可用端口")
            sys.exit(1)
        
        print(f"启动应用在端口 {port}...")
        print(f"API文档: http://localhost:{port}/docs")
        print(f"健康检查: http://localhost:{port}/health")
        
        # 使用导入字符串而不是直接传递app对象
        uvicorn.run(
            "app.main:app",  # 使用导入字符串
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=["app"]
        )
        
    except ImportError as e:
        print(f"ERROR: 导入错误: {e}")
        print("请确保所有依赖都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
