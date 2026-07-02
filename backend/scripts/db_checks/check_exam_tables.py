from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 检查考试相关表
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%exam%' 
             OR table_name LIKE '%test%' 
             OR table_name LIKE '%paper%' 
             OR table_name LIKE '%question%'
             OR table_name LIKE '%answer%'
             OR table_name LIKE '%mark%'
             OR table_name LIKE '%grade%')
        ORDER BY table_name
    """))
    
    tables = [row[0] for row in result]
    print("考试相关表:")
    for table in tables:
        print(f"  - {table}")
    
    if not tables:
        print("  未找到考试相关表") 