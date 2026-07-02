from database import engine, Base
from models import User, Post

def check_database():
    print("🔍 检查数据库连接...")
    
    try:
        # 测试连接
        conn = engine.connect()
        print("✅ 数据库连接成功")
        
        # 创建表
        print("📋 创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 表创建完成")
        
        # 查看表
        print("📊 查看数据库中的表:")
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in result]
        for table in tables:
            print(f"  - {table}")
        
        # 查看users表结构
        if 'users' in tables:
            print("\n👤 users表结构:")
            result = conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库错误: {e}")
        return False

def test_user_creation():
    print("\n🧪 测试用户创建...")
    
    try:
        from database import SessionLocal
        from models import User
        
        db = SessionLocal()
        
        # 创建测试用户
        test_user = User(
            username="testuser",
            email="test@example.com",
            full_name="测试用户"
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print(f"✅ 用户创建成功: ID={test_user.id}, 用户名={test_user.username}")
        
        # 查询用户
        users = db.query(User).all()
        print(f"📊 数据库中共有 {len(users)} 个用户")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 用户创建错误: {e}")
        return False

if __name__ == "__main__":
    if check_database():
        test_user_creation() 