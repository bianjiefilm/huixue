#!/usr/bin/env python3
"""
端点重构脚本（修复版）
将 app/main.py 中的端点按功能模块分组到不同的文件中
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

def ensure_dir(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)

def read_main_file():
    """读取main.py文件内容"""
    with open('app/main_original.py', 'r', encoding='utf-8') as f:
        return f.read()

def extract_endpoints_by_lines(content: str) -> List[Dict]:
    """通过行分析提取端点函数"""
    lines = content.split('\n')
    endpoints = []
    current_endpoint = None
    in_function = False
    function_indent = 0
    
    for i, line in enumerate(lines):
        # 检测端点装饰器
        if re.match(r'^@app\.(get|post|put|patch|delete)', line.strip()):
            # 如果之前有未完成的端点，先保存
            if current_endpoint:
                endpoints.append(current_endpoint)
            
            # 开始新的端点
            method_match = re.search(r'@app\.(\w+)\("([^"]+)"', line)
            if method_match:
                method = method_match.group(1)
                path = method_match.group(2)
                
                current_endpoint = {
                    'method': method,
                    'path': path,
                    'function_name': 'unknown',
                    'content': [line],
                    'start_line': i
                }
                in_function = False
        
        # 检测函数定义
        elif current_endpoint and re.match(r'^def\s+(\w+)', line.strip()):
            func_match = re.search(r'def\s+(\w+)', line)
            if func_match:
                current_endpoint['function_name'] = func_match.group(1)
                current_endpoint['content'].append(line)
                in_function = True
                function_indent = len(line) - len(line.lstrip())
        
        # 在函数内部
        elif current_endpoint and in_function:
            current_endpoint['content'].append(line)
            
            # 检查是否函数结束（下一个函数或装饰器开始）
            if line.strip() and not line.startswith(' ' * (function_indent + 1)) and not line.startswith('\t'):
                # 如果不是空行且缩进不对，可能是函数结束
                if re.match(r'^@app\.|^def\s+|^class\s+|^if\s+__name__', line.strip()):
                    # 移除最后一行（因为它属于下一个函数）
                    current_endpoint['content'].pop()
                    endpoints.append(current_endpoint)
                    current_endpoint = None
                    in_function = False
                    
                    # 如果是新的端点装饰器，重新处理这一行
                    if re.match(r'^@app\.(get|post|put|patch|delete)', line.strip()):
                        method_match = re.search(r'@app\.(\w+)\("([^"]+)"', line)
                        if method_match:
                            method = method_match.group(1)
                            path = method_match.group(2)
                            
                            current_endpoint = {
                                'method': method,
                                'path': path,
                                'function_name': 'unknown',
                                'content': [line],
                                'start_line': i
                            }
                            in_function = False
        
        # 如果有当前端点但不在函数内，继续添加行
        elif current_endpoint and not in_function:
            current_endpoint['content'].append(line)
    
    # 保存最后一个端点
    if current_endpoint:
        endpoints.append(current_endpoint)
    
    # 转换为字符串格式
    for endpoint in endpoints:
        endpoint['content'] = '\n'.join(endpoint['content'])
    
    return endpoints

def categorize_endpoints(endpoints: List[Dict]) -> Dict[str, List[Dict]]:
    """将端点按功能分类"""
    categories = {
        'health': [],
        'users': [],
        'posts': [],
        'courses': [],
        'practices': [],
        'tasks': [],
        'classrooms': [],
        'students': [],
        'grades': [],
        'exams': [],
        'resources': [],
        'analytics': [],
        'sessions': []
    }
    
    # 分类规则
    for endpoint in endpoints:
        path = endpoint['path']
        func_name = endpoint['function_name']
        
        # 健康检查和根路径
        if path in ['/', '/health'] or func_name in ['root', 'health_check']:
            categories['health'].append(endpoint)
        # 用户相关
        elif '/users' in path or func_name.startswith(('create_user', 'read_user', 'delete_user')):
            categories['users'].append(endpoint)
        # 文章相关
        elif '/posts' in path or func_name.startswith(('create_post', 'read_post', 'delete_post')):
            categories['posts'].append(endpoint)
        # 考试相关
        elif '/exams' in path or '/papers' in path or func_name.startswith(('get_exam', 'submit_exam', 'auto_grade')):
            categories['exams'].append(endpoint)
        # 资源相关
        elif '/resources' in path or '/cloud-disk' in path or func_name.startswith(('get_classroom_resource', 'upload', 'delete_classroom_resource')):
            categories['resources'].append(endpoint)
        # 分析相关
        elif '/analytics' in path or func_name.startswith('get_') and 'analytics' in func_name:
            categories['analytics'].append(endpoint)
        # 成绩相关
        elif '/grades' in path or '/penalty' in path or 'grade' in func_name or 'penalty' in func_name or 'assignments' in path:
            categories['grades'].append(endpoint)
        # 学生管理相关
        elif '/students' in path or 'student' in path or func_name.startswith(('get_student', 'add_student', 'remove_student', 'get_available_students', 'get_organization_tree')):
            categories['students'].append(endpoint)
        # 会话相关
        elif '/sessions' in path or func_name.startswith(('close_session', 'session_heartbeat', 'adjust_', 'reset_', 'toggle_', 'extend_', 'sync_', 'restore_')):
            categories['sessions'].append(endpoint)
        # 任务相关
        elif '/tasks' in path or func_name.startswith(('get_task', 'submit_task', 'start_course_task', 'save_code_snapshot')):
            categories['tasks'].append(endpoint)
        # 实践相关
        elif '/practices' in path or func_name.startswith('get_practice') or func_name == 'add_practice_to_classroom':
            categories['practices'].append(endpoint)
        # 课堂相关 - 需要更精确的匹配
        elif ('/classrooms' in path and '/courses' not in path and '/students' not in path and '/resources' not in path and '/analytics' not in path) or func_name.startswith(('get_classroom', 'create_classroom', 'update_classroom', 'delete_classroom', 'get_my_classroom')):
            categories['classrooms'].append(endpoint)
        # 课程相关 - 包括课堂课程管理
        elif '/courses' in path or func_name.startswith(('get_course', 'add_course')) or 'course' in func_name or func_name.startswith(('get_filter_tags', 'get_statistics')):
            categories['courses'].append(endpoint)
        else:
            # 默认归类到courses
            categories['courses'].append(endpoint)
    
    # 移除空分类
    return {k: v for k, v in categories.items() if v}

def create_endpoint_file(category: str, endpoints: List[Dict], imports: str) -> str:
    """创建端点文件内容"""
    
    # 根据分类确定标签和前缀
    category_config = {
        'health': {'prefix': '', 'tags': ['health'], 'description': '健康检查'},
        'users': {'prefix': '/users', 'tags': ['users'], 'description': '用户管理'},
        'posts': {'prefix': '/posts', 'tags': ['posts'], 'description': '文章管理'},
        'courses': {'prefix': '/api/v1', 'tags': ['courses'], 'description': '课程管理'},
        'practices': {'prefix': '/api/v1', 'tags': ['practices'], 'description': '实践管理'},
        'tasks': {'prefix': '/api/v1', 'tags': ['tasks'], 'description': '任务管理'},
        'classrooms': {'prefix': '/api/v1', 'tags': ['classrooms'], 'description': '课堂管理'},
        'students': {'prefix': '/api/v1', 'tags': ['students'], 'description': '学生管理'},
        'grades': {'prefix': '/api/v1', 'tags': ['grades'], 'description': '成绩管理'},
        'exams': {'prefix': '/api/v1', 'tags': ['exams'], 'description': '考试管理'},
        'resources': {'prefix': '/api/v1', 'tags': ['resources'], 'description': '资源管理'},
        'analytics': {'prefix': '/api/v1', 'tags': ['analytics'], 'description': '数据分析'},
        'sessions': {'prefix': '/api/v1', 'tags': ['sessions'], 'description': '会话管理'}
    }
    
    config = category_config.get(category, {'prefix': '/api/v1', 'tags': [category], 'description': f'{category}管理'})
    
    content = f'''"""
{config['description']}端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta

from app.core.database import get_db, engine, Base
from app.models.models import User, Post
import app.crud.crud as crud
import app.schemas.schemas as schemas
import app.models.models as models

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="{config['prefix']}",
    tags={config['tags']}
)

'''
    
    # 添加端点函数
    for endpoint in endpoints:
        # 将 @app.method 替换为 @router.method
        endpoint_content = endpoint['content']
        endpoint_content = re.sub(r'@app\.(get|post|put|patch|delete)', r'@router.\1', endpoint_content)
        
        content += endpoint_content + '\n\n'
    
    return content

def create_new_main_file(categories: Dict[str, List[Dict]]) -> str:
    """创建新的main.py文件"""
    content = '''"""
慧学高校大数据API主应用
"""

from fastapi import FastAPI
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="慧学 API主应用",
    description="基于FastAPI和PostgreSQL的后端API - 课程实践模块",
    version="1.0.0"
)

# 导入并注册路由器
'''
    
    # 添加路由器导入和注册
    for category in categories.keys():
        content += f'from app.api.v1.endpoints import {category}\n'
    
    content += '\n# 注册路由器\n'
    
    for category in categories.keys():
        content += f'app.include_router({category}.router)\n'
    
    return content

def backup_main_file():
    """备份原始main.py文件"""
    import shutil
    if os.path.exists('app/main.py'):
        shutil.copy('app/main.py', 'app/main.py.backup3')
        print("✓ 已备份当前 main.py 为 main.py.backup3")

def main():
    """主函数"""
    print("开始端点重构（修复版）...")
    
    # 确保目录存在
    ensure_dir('app/api/v1/endpoints')
    
    # 备份原始文件
    backup_main_file()
    
    # 读取main.py内容
    print("1. 读取 main_original.py 文件...")
    content = read_main_file()
    
    # 提取端点
    print("2. 提取端点函数...")
    endpoints = extract_endpoints_by_lines(content)
    print(f"   找到 {len(endpoints)} 个端点")
    
    # 分类端点
    print("3. 按功能分类端点...")
    categories = categorize_endpoints(endpoints)
    
    for category, eps in categories.items():
        print(f"   {category}: {len(eps)} 个端点")
        # 显示每个分类的端点名称
        for ep in eps:
            print(f"     - {ep['function_name']} ({ep['method'].upper()} {ep['path']})")
    
    # 创建端点文件
    print("4. 创建端点文件...")
    for category, endpoints_list in categories.items():
        file_content = create_endpoint_file(category, endpoints_list, "")
        file_path = f'app/api/v1/endpoints/{category}.py'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"   ✓ 创建 {file_path}")
    
    # 创建__init__.py文件
    print("5. 创建__init__.py文件...")
    init_content = '# endpoints package\n'
    with open('app/api/v1/endpoints/__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)
    print("   ✓ 创建 app/api/v1/endpoints/__init__.py")
    
    # 创建新的main.py
    print("6. 创建新的 main.py...")
    new_main_content = create_new_main_file(categories)
    
    with open('app/main.py', 'w', encoding='utf-8') as f:
        f.write(new_main_content)
    
    print("   ✓ 更新 app/main.py")
    
    print("\n端点重构完成！")
    print("\n创建的文件:")
    for category in categories.keys():
        print(f"  - app/api/v1/endpoints/{category}.py")
    print(f"  - app/main.py (已更新)")
    print(f"  - app/main.py.backup3 (当前备份)")
    
    print("\n下一步:")
    print("1. 运行 python test_import.py 测试导入")
    print("2. 运行 python run.py 测试应用启动")
    print("3. 如有问题，可以从备份文件恢复")

if __name__ == "__main__":
    main() 