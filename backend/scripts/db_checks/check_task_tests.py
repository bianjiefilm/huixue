from database import get_db, engine
from sqlalchemy import inspect, text

# 获取数据库连接
db = next(get_db())

try:
    # 检查task_tests表结构
    inspector = inspect(engine)
    if 'task_tests' in inspector.get_table_names():
        print('✅ task_tests表存在')
        print('📋 task_tests表结构:')
        columns = inspector.get_columns('task_tests')
        for column in columns:
            print(f'  - {column["name"]}: {column["type"]} (nullable: {"YES" if column["nullable"] else "NO"}, default: {column["default"]})')
    else:
        print('❌ task_tests表不存在')
        
    # 查看所有表
    print('\n📊 相关表:')
    tables = inspector.get_table_names()
    for table in sorted(tables):
        if 'task' in table.lower() or 'test' in table.lower():
            print(f'  - {table}')
            
except Exception as e:
    print(f'❌ 错误: {e}')
finally:
    db.close() 