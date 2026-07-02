#!/usr/bin/env python3
"""
路由唯一性检查脚本
用于检测API路由定义是否存在重复
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

def extract_routes(file_path: Path) -> List[Tuple[str, str, int]]:
    """
    从Python文件中提取路由定义
    返回: [(method, path, line_number), ...]
    """
    routes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 匹配路由装饰器模式
    route_pattern = re.compile(
        r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    )
    
    for i, line in enumerate(lines, 1):
        match = route_pattern.search(line)
        if match:
            method = match.group(1).upper()
            path = match.group(2)
            routes.append((method, path, i))
    
    return routes

def check_route_conflicts():
    """检查所有路由文件中的路由冲突"""
    
    # 查找所有endpoints文件
    api_dir = Path('app/api/v1/endpoints')
    if not api_dir.exists():
        print("API目录不存在，跳过检查")
        return True
    
    # 收集所有路由
    all_routes: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)
    
    for py_file in api_dir.glob('*.py'):
        if py_file.name == '__init__.py':
            continue
        
        routes = extract_routes(py_file)
        for method, path, line_num in routes:
            # 构建完整路由键（包含方法）
            route_key = f"{method} {path}"
            all_routes[route_key].append((py_file, line_num))
    
    # 检查冲突
    conflicts = []
    for route_key, locations in all_routes.items():
        if len(locations) > 1:
            conflicts.append((route_key, locations))
    
    # 报告结果
    if conflicts:
        print("❌ 发现路由冲突！")
        print("="*60)
        
        for route_key, locations in conflicts:
            print(f"\n冲突路由: {route_key}")
            print("定义位置:")
            for file_path, line_num in locations:
                print(f"  - {file_path.relative_to(Path.cwd())}:{line_num}")
        
        print("\n" + "="*60)
        print("请修复以上路由冲突后再提交代码")
        return False
    
    print("✅ 路由检查通过，无冲突")
    return True

def main():
    """主函数"""
    if not check_route_conflicts():
        sys.exit(1)

if __name__ == "__main__":
    main()