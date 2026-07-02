from database import get_db, engine
from sqlalchemy import inspect

# 获取数据库连接
db = next(get_db())

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # 查找代码快照相关表
    snapshot_tables = [t for t in tables if 'snapshot' in t.lower() or 'code' in t.lower()]
    print('代码快照相关表:', snapshot_tables)
    
    # 查找评测相关表
    eval_tables = [t for t in tables if 'eval' in t.lower() or 'attempt' in t.lower()]
    print('评测相关表:', eval_tables)
    
except Exception as e:
    print(f'❌ 错误: {e}')
finally:
    db.close() 