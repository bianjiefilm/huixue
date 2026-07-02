from sqlalchemy import create_engine, text
from config import settings

def check_classrooms_table():
    """检查classrooms表的结构"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
            
            # 查询classrooms表的列结构
            result = conn.execute(text("""
                SELECT column_name, data_type, udt_name, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'classrooms'
                ORDER BY ordinal_position;
            """))
            
            print("\n📊 classrooms表的列结构:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} ({row[2]}) nullable: {row[3]} default: {row[4]}")
                
            # 查询classrooms表的外键约束
            result2 = conn.execute(text("""
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = 'classrooms';
            """))
            
            print("\n📋 classrooms表的外键约束:")
            for row in result2:
                print(f"  - {row[1]}.{row[2]} -> {row[3]}.{row[4]} ({row[0]})")
                
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_classrooms_table() 