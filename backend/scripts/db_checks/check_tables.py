from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 检查用户相关表
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%user%' ORDER BY table_name"))
    user_tables = [row[0] for row in result]
    print("用户相关表:", user_tables)
    
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
        AND kcu.column_name LIKE '%student_id%'
    """))
    
    fk_info = list(result)
    print("student_course_progress表的student_id外键约束:")
    for row in fk_info:
        print(f"  约束名: {row[0]}, 列: {row[2]}, 引用表: {row[3]}, 引用列: {row[4]}")
    
    # 检查users表的结构
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position"))
    users_columns = list(result)
    print("\nusers表的字段:")
    for row in users_columns:
        print(f"  {row[0]}: {row[1]}")
    
    # 检查api_users表的结构
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'api_users' ORDER BY ordinal_position"))
    api_users_columns = list(result)
    print("\napi_users表的字段:")
    for row in api_users_columns:
        print(f"  {row[0]}: {row[1]}")
    
    # 检查classrooms表的外键约束
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
        AND tc.table_name='classrooms'
        AND kcu.column_name LIKE '%teacher_id%'
    """))
    
    classroom_fk_info = list(result)
    print("\nclassrooms表的teacher_id外键约束:")
    for row in classroom_fk_info:
        print(f"  约束名: {row[0]}, 列: {row[2]}, 引用表: {row[3]}, 引用列: {row[4]}") 