#!/usr/bin/env python3
"""
项目重构脚本
将现有文件移动到新的目录结构中
"""

import os
import shutil
import sys
from pathlib import Path

def ensure_dir(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)

def move_file(src, dst, create_dirs=True):
    """移动文件，如果目标目录不存在则创建"""
    if not os.path.exists(src):
        print(f"警告: 源文件不存在 {src}")
        return False
    
    if create_dirs:
        ensure_dir(os.path.dirname(dst))
    
    try:
        shutil.move(src, dst)
        print(f"✓ 移动 {src} -> {dst}")
        return True
    except Exception as e:
        print(f"✗ 移动失败 {src} -> {dst}: {e}")
        return False

def copy_file(src, dst, create_dirs=True):
    """复制文件，如果目标目录不存在则创建"""
    if not os.path.exists(src):
        print(f"警告: 源文件不存在 {src}")
        return False
    
    if create_dirs:
        ensure_dir(os.path.dirname(dst))
    
    try:
        shutil.copy2(src, dst)
        print(f"✓ 复制 {src} -> {dst}")
        return True
    except Exception as e:
        print(f"✗ 复制失败 {src} -> {dst}: {e}")
        return False

def update_imports_in_file(file_path, import_updates):
    """更新文件中的导入语句"""
    if not os.path.exists(file_path):
        print(f"警告: 文件不存在 {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old_import, new_import in import_updates.items():
            content = content.replace(old_import, new_import)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 更新导入语句 {file_path}")
            return True
        else:
            print(f"- 无需更新 {file_path}")
            return True
    except Exception as e:
        print(f"✗ 更新导入失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("开始项目重构...")
    
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent
    os.chdir(root_dir)
    
    print(f"工作目录: {os.getcwd()}")
    
    # 1. 移动核心文件到 app/core/
    print("\n1. 移动核心文件到 app/core/...")
    core_files = [
        ('config.py', 'app/core/config.py'),
        ('database.py', 'app/core/database.py'),
    ]
    
    for src, dst in core_files:
        move_file(src, dst)
    
    # 2. 移动模型文件
    print("\n2. 移动模型文件...")
    move_file('models.py', 'app/models/models.py')
    
    # 3. 移动schemas文件
    print("\n3. 移动schemas文件...")
    move_file('schemas.py', 'app/schemas/schemas.py')
    
    # 4. 移动crud文件
    print("\n4. 移动crud文件...")
    move_file('crud.py', 'app/crud/crud.py')
    
    # 5. 移动main.py到app/
    print("\n5. 移动main.py到app/...")
    move_file('main.py', 'app/main.py')
    
    # 6. 移动其他脚本文件
    print("\n6. 移动其他脚本文件...")
    script_moves = [
        # 数据初始化脚本
        ('create_test_user.py', 'scripts/data_init/create_test_user.py'),
        ('create_users_records.py', 'scripts/data_init/create_users_records.py'),
        ('create_missing_users.py', 'scripts/data_init/create_missing_users.py'),
        ('clean_test_data.py', 'scripts/data_init/clean_test_data.py'),
        
        # 调试和修复脚本
        ('debug_api.py', 'scripts/db_checks/debug_api.py'),
        ('quick_fix.py', 'scripts/db_checks/quick_fix.py'),
    ]
    
    for src, dst in script_moves:
        if os.path.exists(src):
            move_file(src, dst)
    
    # 7. 更新run.py中的导入
    print("\n7. 更新run.py中的导入...")
    if os.path.exists('run.py'):
        import_updates = {
            'from main import app': 'from app.main import app',
            'import main': 'import app.main as main',
            'main.app': 'app.main.app'
        }
        update_imports_in_file('run.py', import_updates)
    
    # 8. 更新app/main.py中的导入
    print("\n8. 更新app/main.py中的导入...")
    if os.path.exists('app/main.py'):
        import_updates = {
            'from database import': 'from app.core.database import',
            'from models import': 'from app.models.models import',
            'import crud': 'import app.crud.crud as crud',
            'import schemas': 'import app.schemas.schemas as schemas',
            'import models': 'import app.models.models as models',
            'from config import': 'from app.core.config import',
        }
        update_imports_in_file('app/main.py', import_updates)
    
    # 9. 创建新的__init__.py文件以支持导入
    print("\n9. 更新__init__.py文件...")
    
    # 更新app/models/__init__.py
    models_init_content = '''# models package
from .models import *
'''
    with open('app/models/__init__.py', 'w', encoding='utf-8') as f:
        f.write(models_init_content)
    print("✓ 更新 app/models/__init__.py")
    
    # 更新app/schemas/__init__.py
    schemas_init_content = '''# schemas package
from .schemas import *
'''
    with open('app/schemas/__init__.py', 'w', encoding='utf-8') as f:
        f.write(schemas_init_content)
    print("✓ 更新 app/schemas/__init__.py")
    
    # 更新app/crud/__init__.py
    crud_init_content = '''# crud package
from .crud import *
'''
    with open('app/crud/__init__.py', 'w', encoding='utf-8') as f:
        f.write(crud_init_content)
    print("✓ 更新 app/crud/__init__.py")
    
    # 更新app/core/__init__.py
    core_init_content = '''# core package
from .database import *
from .config import *
'''
    with open('app/core/__init__.py', 'w', encoding='utf-8') as f:
        f.write(core_init_content)
    print("✓ 更新 app/core/__init__.py")
    
    # 10. 创建新的启动脚本
    print("\n10. 创建新的启动脚本...")
    new_run_content = '''#!/usr/bin/env python3
"""
应用启动脚本
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"]
    )
'''
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(new_run_content)
    print("✓ 创建新的 run.py")
    
    print("\n项目重构完成！")
    print("\n下一步:")
    print("1. 检查 app/main.py 中的导入语句是否正确")
    print("2. 运行 python run.py 测试应用是否正常启动")
    print("3. 如有导入错误，请手动调整相关文件")

if __name__ == "__main__":
    main() 