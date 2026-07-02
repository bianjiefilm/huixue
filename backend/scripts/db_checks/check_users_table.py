from sqlalchemy import create_engine, text
from config import settings
from database import get_db

def check_users_table():
    """检查users表中的数据"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
            
            # 查询users表的数据
            result = conn.execute(text("SELECT id, username FROM users WHERE id >= 7 ORDER BY id"))
            
            print("\n📊 users表中的数据:")
            users = list(result)
            if users:
                for row in users:
                    print(f"  - ID: {row[0]}, Username: {row[1]}")
            else:
                print("  - 表为空")
                
            # 查询api_users表的数据
            result2 = conn.execute(text("SELECT id, username FROM api_users LIMIT 10;"))
            
            print("\n📊 api_users表中的数据:")
            api_users = list(result2)
            if api_users:
                for row in api_users:
                    print(f"  - ID: {row[0]}, Username: {row[1]}")
            else:
                print("  - 表为空")
                
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    db = next(get_db())
    try:
        result = db.execute(text('SELECT id, username FROM users WHERE id >= 7 ORDER BY id'))
        print('users表中的记录:')
        for row in result:
            print(f'  ID: {row[0]}, 用户名: {row[1]}')
    finally:
        db.close() 