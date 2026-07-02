from sqlalchemy import create_engine, text
from config import settings

def check_enum_types():
    """检查数据库中的枚举类型定义"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
            
            # 查询所有枚举类型
            result = conn.execute(text("""
                SELECT t.typname, e.enumlabel 
                FROM pg_type t 
                JOIN pg_enum e ON t.oid = e.enumtypid 
                WHERE t.typname LIKE '%difficulty%' OR t.typname LIKE '%course%'
                ORDER BY t.typname, e.enumsortorder;
            """))
            
            print("\n📊 数据库中的枚举类型:")
            current_type = None
            for row in result:
                if row[0] != current_type:
                    current_type = row[0]
                    print(f"\n🏷️  {current_type}:")
                print(f"   - {row[1]}")
                
            # 查询courses表的difficulty列具体使用的枚举类型
            result3 = conn.execute(text("""
                SELECT c.column_name, c.udt_name, t.typname, e.enumlabel
                FROM information_schema.columns c
                JOIN pg_type t ON c.udt_name = t.typname
                LEFT JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE c.table_name = 'courses' AND c.column_name = 'difficulty'
                ORDER BY e.enumsortorder;
            """))
            
            print("\n📋 courses表difficulty列的枚举定义:")
            for row in result3:
                print(f"  - 列名: {row[0]}, 类型: {row[1]}, 枚举名: {row[2]}, 值: {row[3]}")
                
            # 查询所有自定义类型
            result2 = conn.execute(text("""
                SELECT typname, typtype 
                FROM pg_type 
                WHERE typtype = 'e' 
                ORDER BY typname;
            """))
            
            print("\n📋 所有枚举类型:")
            for row in result2:
                print(f"  - {row[0]}")
                
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_enum_types() 