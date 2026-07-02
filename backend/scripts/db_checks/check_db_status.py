"""
检查数据库状态和外键约束问题
"""

from database import engine
from sqlalchemy import text

def check_database_status():
    """检查数据库状态"""
    try:
        with engine.connect() as conn:
            print("=== 数据库连接成功 ===")
            
            # 检查api_users表
            result = conn.execute(text("SELECT COUNT(*) FROM api_users"))
            api_users_count = result.scalar()
            print(f"api_users表记录数: {api_users_count}")
            
            # 检查users表
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            users_count = result.scalar()
            print(f"users表记录数: {users_count}")
            
            # 检查classrooms表
            result = conn.execute(text("SELECT COUNT(*) FROM classrooms"))
            classrooms_count = result.scalar()
            print(f"classrooms表记录数: {classrooms_count}")
            
            # 检查classroom_students表
            result = conn.execute(text("SELECT COUNT(*) FROM classroom_students"))
            classroom_students_count = result.scalar()
            print(f"classroom_students表记录数: {classroom_students_count}")
            
            print("\n=== 检查外键约束问题 ===")
            
            # 检查classrooms表的teacher_id外键
            result = conn.execute(text("""
                SELECT c.id, c.name, c.teacher_id, u.username as teacher_username
                FROM classrooms c
                LEFT JOIN users u ON c.teacher_id = u.id
                ORDER BY c.id
            """))
            classrooms = list(result)
            print("classrooms表与users表的关联:")
            for classroom in classrooms:
                print(f"  课堂ID: {classroom[0]}, 名称: {classroom[1]}, 教师ID: {classroom[2]}, 教师用户名: {classroom[3]}")
            
            # 检查是否有classrooms.teacher_id指向api_users的情况
            result = conn.execute(text("""
                SELECT c.id, c.name, c.teacher_id, au.username as api_teacher_username
                FROM classrooms c
                LEFT JOIN api_users au ON c.teacher_id = au.id
                ORDER BY c.id
            """))
            classrooms_api = list(result)
            print("\nclassrooms表与api_users表的关联:")
            for classroom in classrooms_api:
                print(f"  课堂ID: {classroom[0]}, 名称: {classroom[1]}, 教师ID: {classroom[2]}, API教师用户名: {classroom[3]}")
            
            # 检查classroom_students表的外键
            result = conn.execute(text("""
                SELECT cs.classroom_id, cs.student_id, au.username as student_username
                FROM classroom_students cs
                LEFT JOIN api_users au ON cs.student_id = au.id
                ORDER BY cs.classroom_id, cs.student_id
                LIMIT 10
            """))
            classroom_students = list(result)
            print(f"\nclassroom_students表与api_users表的关联 (前10条):")
            for cs in classroom_students:
                print(f"  课堂ID: {cs[0]}, 学生ID: {cs[1]}, 学生用户名: {cs[2]}")
                
    except Exception as e:
        print(f"数据库检查失败: {e}")

if __name__ == "__main__":
    check_database_status() 