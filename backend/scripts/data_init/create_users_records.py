#!/usr/bin/env python3
"""
在users表中创建对应的学生记录，使ID与api_users表保持一致
"""

from database import get_db
from sqlalchemy import text
from datetime import datetime, timezone

def create_users_records():
    """在users表中创建学生记录"""
    print("在users表中创建学生记录...")
    
    db = next(get_db())
    
    try:
        # 获取api_users表中的学生信息
        result = db.execute(text("""
            SELECT id, username, email, full_name 
            FROM api_users 
            WHERE id IN (11, 12, 13, 14, 15)
        """))
        api_users = list(result)
        
        for user in api_users:
            user_id, username, email, full_name = user
            
            # 检查users表中是否已存在
            result = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id})
            existing = result.fetchone()
            
            if not existing:
                # 在users表中创建对应记录
                db.execute(text("""
                    INSERT INTO users (id, username, password_hash, full_name, user_no, email, is_active, created_at)
                    VALUES (:id, :username, 'hashed_password', :full_name, :user_no, :email, true, :created_at)
                """), {
                    "id": user_id,
                    "username": username,
                    "full_name": full_name,
                    "user_no": f"S{user_id:03d}",
                    "email": email,
                    "created_at": datetime.now(timezone.utc)
                })
                print(f"  ✓ 在users表创建学生记录，ID: {user_id}, 用户名: {username}")
            else:
                print(f"  ✓ users表中学生记录已存在，ID: {user_id}")
        
        db.commit()
        print("✓ users表学生记录创建完成！")
        
    except Exception as e:
        print(f"❌ 创建失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_users_records() 