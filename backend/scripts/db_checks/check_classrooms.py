"""
检查课堂数据
"""

from database import engine
from sqlalchemy import text

def check_classrooms():
    """检查课堂数据"""
    with engine.connect() as conn:
        # 检查现有课堂
        result = conn.execute(text("SELECT id, name, teacher_id FROM classrooms ORDER BY id;"))
        classrooms = list(result)
        print("现有课堂:")
        for classroom in classrooms:
            print(f"  - ID: {classroom[0]}, Name: {classroom[1]}, Teacher ID: {classroom[2]}")
        
        print(f"\n课堂总数: {len(classrooms)}")
        
        # 检查classroom_students表
        result = conn.execute(text("SELECT classroom_id, student_id FROM classroom_students ORDER BY classroom_id, student_id;"))
        classroom_students = list(result)
        print(f"\n课堂学生关联记录:")
        for cs in classroom_students:
            print(f"  - 课堂ID: {cs[0]}, 学生ID: {cs[1]}")
        
        print(f"\n课堂学生关联记录总数: {len(classroom_students)}")

if __name__ == "__main__":
    check_classrooms() 