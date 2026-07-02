from sqlalchemy import create_engine, text
from config import settings

def check_practices_table():
    """检查practices表的结构"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
            
            # 查询practices表的列结构
            result = conn.execute(text("""
                SELECT column_name, data_type, udt_name, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'practices'
                ORDER BY ordinal_position;
            """))
            
            print("\n📊 practices表的列结构:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} ({row[2]}) nullable: {row[3]} default: {row[4]}")
                
            # 查询difficultylevel枚举的所有值
            result2 = conn.execute(text("""
                SELECT e.enumlabel, e.enumsortorder
                FROM pg_type t 
                JOIN pg_enum e ON t.oid = e.enumtypid 
                WHERE t.typname = 'difficultylevel'
                ORDER BY e.enumsortorder;
            """))
            
            print("\n📋 difficultylevel枚举的所有值:")
            enum_values = list(result2)
            for row in enum_values:
                print(f"  - {row[0]} (排序: {row[1]})")
            
            print(f"\n📈 总共有 {len(enum_values)} 个枚举值")
            
            # 测试插入一个practice记录
            print("\n🧪 测试插入practice记录:")
            try:
                result3 = conn.execute(text("""
                    INSERT INTO practices (title, direction, category, difficulty) 
                    VALUES ('测试实践', '测试方向', '测试分类', 'intermediate') 
                    RETURNING id;
                """))
                practice_id = result3.fetchone()[0]
                print(f"  ✅ 插入成功，ID: {practice_id}")
                
                # 删除测试记录
                conn.execute(text("DELETE FROM practices WHERE id = :id"), {"id": practice_id})
                conn.commit()
                print(f"  🗑️ 测试记录已删除")
                
            except Exception as insert_error:
                print(f"  ❌ 插入失败: {insert_error}")
                conn.rollback()
                
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_practices_table() 