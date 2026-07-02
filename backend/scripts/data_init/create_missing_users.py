#!/usr/bin/env python3
"""
创建users表中缺失的用户记录
"""

from database import get_db
from sqlalchemy import text
from datetime import datetime, timezone

def create_missing_users():
    """创建缺失的用户记录"""
    print("创建缺失的用户记录...")
    
    db = next(get_db())
    
    try:
        # 需要创建的用户ID和对应的api_users信息
        missing_ids = [10, 12, 13, 14, 15]
        
        for user_id in missing_ids:
            # 获取api_users表中的对应信息
            result = db.execute(text("""
                SELECT username, email, full_name 
                FROM api_users 
                WHERE id = :id
            """), {"id": user_id})
            api_user = result.fetchone()
            
            if api_user:
                username, email, full_name = api_user
                
                # 检查users表中是否已存在
                result = db.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id})
                existing = result.fetchone()
                
                if not existing:
                    # 创建新的用户名以避免冲突
                    new_username = f"user_{user_id}"
                    
                    # 在users表中创建记录
                    db.execute(text("""
                        INSERT INTO users (id, username, password_hash, full_name, user_no, email, is_active, created_at)
                        VALUES (:id, :username, 'hashed_password', :full_name, :user_no, :email, true, :created_at)
                    """), {
                        "id": user_id,
                        "username": new_username,
                        "full_name": full_name,
                        "user_no": f"S{user_id:03d}",
                        "email": f"user_{user_id}@example.com",
                        "created_at": datetime.now(timezone.utc)
                    })
                    print(f"  ✓ 创建用户记录，ID: {user_id}, 用户名: {new_username}")
                else:
                    print(f"  ✓ 用户记录已存在，ID: {user_id}")
            else:
                print(f"  ❌ api_users表中未找到ID {user_id} 的记录")
        
        db.commit()
        print("✓ 缺失用户记录创建完成！")
        
        # 验证创建结果
        result = db.execute(text('SELECT id, username FROM users WHERE id >= 7 ORDER BY id'))
        print("\n验证users表记录:")
        for row in result:
            print(f'  ID: {row[0]}, 用户名: {row[1]}')
        
    except Exception as e:
        print(f"❌ 创建失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_missing_users() 