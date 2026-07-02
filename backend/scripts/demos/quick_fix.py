from database import engine
from sqlalchemy import text

print("开始修复外键约束...")

try:
    with engine.begin() as conn:
        # 删除旧的外键约束
        conn.execute(text("ALTER TABLE classroom_students DROP CONSTRAINT IF EXISTS classroom_students_student_id_fkey"))
        print("删除旧约束")
        
        # 添加新的外键约束
        conn.execute(text("ALTER TABLE classroom_students ADD CONSTRAINT fk_classroom_students_student_id FOREIGN KEY (student_id) REFERENCES api_users(id)"))
        print("添加新约束")
        
    print("外键约束修复完成！")
    
except Exception as e:
    print(f"修复失败: {e}") 