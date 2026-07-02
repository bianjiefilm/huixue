"""
检查用户表数据
"""

from database import engine
from sqlalchemy import text

def check_users():
    """检查用户表数据"""
    with engine.connect() as conn:
        # 检查api_users表
        result = conn.execute(text("SELECT id, username, full_name FROM api_users ORDER BY id;"))
        api_users = list(result)
        print("api_users表中的数据:")
        for user in api_users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Name: {user[2]}")
        
        # 检查users表
        result = conn.execute(text("SELECT id, username, full_name FROM users ORDER BY id;"))
        users = list(result)
        print("\nusers表中的数据:")
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Name: {user[2]}")
        
        print(f"\napi_users表记录数: {len(api_users)}")
        print(f"users表记录数: {len(users)}")

if __name__ == "__main__":
    check_users() 