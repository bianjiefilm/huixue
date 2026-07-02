from database import engine
from sqlalchemy import text

def check_table_structure(table_name):
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        
        print(f"\n=== {table_name} 表结构 ===")
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {row[3]}" if row[3] else ""
            print(f"  {row[0]}: {row[1]} {nullable}{default}")

# 检查主要的考试相关表
tables = [
    'classroom_exams',
    'test_papers', 
    'test_paper_questions',
    'questions',
    'student_exam_attempts',
    'student_exam_answers'
]

for table in tables:
    check_table_structure(table) 