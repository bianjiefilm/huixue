from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 检查student_course_progress表的外键约束
    result = conn.execute(text("""
        SELECT 
            tc.constraint_name, 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name='student_course_progress'
    """))
    
    progress_fk_info = list(result)
    print("student_course_progress表的外键约束:")
    for row in progress_fk_info:
        print(f"  约束名: {row[0]}, 列: {row[2]}, 引用表: {row[3]}, 引用列: {row[4]}") 