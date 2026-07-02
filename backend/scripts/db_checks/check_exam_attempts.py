from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'student_exam_attempts' 
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    
    print("=== student_exam_attempts 表结构 ===")
    for row in result:
        nullable = "NULL" if row[2] == "YES" else "NOT NULL"
        default = f" DEFAULT {row[3]}" if row[3] else ""
        print(f"  {row[0]}: {row[1]} {nullable}{default}")
    
    # 检查枚举类型
    result = conn.execute(text("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'exam_status_enum'
        )
        ORDER BY enumsortorder
    """))
    
    print("\n=== exam_status_enum 枚举值 ===")
    for row in result:
        print(f"  - {row[0]}")
    
    # 检查question_type枚举
    result = conn.execute(text("""
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (
            SELECT oid 
            FROM pg_type 
            WHERE typname = 'question_type_enum'
        )
        ORDER BY enumsortorder
    """))
    
    print("\n=== question_type_enum 枚举值 ===")
    for row in result:
        print(f"  - {row[0]}") 