"""
初始化学生管理功能的测试数据
创建一些测试用户和课堂数据
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import crud
from datetime import datetime, timezone, timedelta

def create_test_users():
    """创建测试用户（学生和教师）"""
    db = SessionLocal()
    
    try:
        # 创建教师用户
        teacher_data = {
            "username": "teacher001",
            "email": "teacher001@example.com",
            "full_name": "张老师"
        }
        
        # 检查教师是否已存在
        existing_teacher = db.query(models.User).filter(models.User.username == teacher_data["username"]).first()
        if not existing_teacher:
            teacher = models.User(**teacher_data)
            db.add(teacher)
            db.commit()
            db.refresh(teacher)
            print(f"创建教师用户: {teacher.username} (ID: {teacher.id})")
        else:
            teacher = existing_teacher
            print(f"教师用户已存在: {teacher.username} (ID: {teacher.id})")
        
        # 创建学生用户
        students_data = [
            {"username": "student001", "email": "student001@example.com", "full_name": "张三"},
            {"username": "student002", "email": "student002@example.com", "full_name": "李四"},
            {"username": "student003", "email": "student003@example.com", "full_name": "王五"},
            {"username": "student004", "email": "student004@example.com", "full_name": "赵六"},
            {"username": "student005", "email": "student005@example.com", "full_name": "钱七"},
            {"username": "student006", "email": "student006@example.com", "full_name": "孙八"},
            {"username": "student007", "email": "student007@example.com", "full_name": "周九"},
            {"username": "student008", "email": "student008@example.com", "full_name": "吴十"},
            {"username": "student009", "email": "student009@example.com", "full_name": "郑十一"},
            {"username": "student010", "email": "student010@example.com", "full_name": "王十二"},
        ]
        
        created_students = []
        for student_data in students_data:
            existing_student = db.query(models.User).filter(models.User.username == student_data["username"]).first()
            if not existing_student:
                student = models.User(**student_data)
                db.add(student)
                db.commit()
                db.refresh(student)
                created_students.append(student)
                print(f"创建学生用户: {student.username} (ID: {student.id})")
            else:
                created_students.append(existing_student)
                print(f"学生用户已存在: {existing_student.username} (ID: {existing_student.id})")
        
        return teacher, created_students
        
    except Exception as e:
        print(f"创建用户失败: {e}")
        db.rollback()
        return None, []
    finally:
        db.close()

def create_test_classroom(teacher_id):
    """创建测试课堂"""
    db = SessionLocal()
    
    try:
        # 检查课堂是否已存在
        existing_classroom = db.query(models.Classroom).filter(
            models.Classroom.name == "Python程序设计测试课堂"
        ).first()
        
        if not existing_classroom:
            classroom_data = {
                "name": "Python程序设计测试课堂",
                "teacher_id": teacher_id,
                "start_date": datetime.now(timezone.utc),
                "end_date": datetime.now(timezone.utc) + timedelta(days=90),
                "academic_year": "2023-2024",
                "semester": "春季学期",
                "status": models.ClassroomStatusEnum.ONGOING,
                "student_count": 0
            }
            
            classroom = models.Classroom(**classroom_data)
            db.add(classroom)
            db.commit()
            db.refresh(classroom)
            print(f"创建测试课堂: {classroom.name} (ID: {classroom.id})")
            return classroom
        else:
            print(f"测试课堂已存在: {existing_classroom.name} (ID: {existing_classroom.id})")
            return existing_classroom
            
    except Exception as e:
        print(f"创建课堂失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def add_some_students_to_classroom(classroom_id, student_ids):
    """添加一些学生到课堂（用于测试）"""
    db = SessionLocal()
    
    try:
        # 添加前3个学生到课堂
        test_student_ids = student_ids[:3]
        result = crud.add_students_to_classroom(db, classroom_id, test_student_ids)
        print(f"添加学生到课堂结果: {result}")
        
    except Exception as e:
        print(f"添加学生到课堂失败: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    print("开始初始化学生管理功能测试数据...")
    print("=" * 50)
    
    # 创建数据库表
    models.Base.metadata.create_all(bind=engine)
    
    # 创建测试用户
    teacher, students = create_test_users()
    
    if teacher and students:
        # 获取teacher的ID（避免会话问题）
        teacher_id = teacher.id
        student_ids = [s.id for s in students]
        
        # 创建测试课堂
        classroom = create_test_classroom(teacher_id)
        
        if classroom:
            # 添加一些学生到课堂
            add_some_students_to_classroom(classroom.id, student_ids)
            
            print("\n" + "=" * 50)
            print("测试数据初始化完成！")
            print(f"教师ID: {teacher_id}")
            print(f"课堂ID: {classroom.id}")
            print(f"学生IDs: {student_ids}")
            print("\n可以使用以下命令测试API:")
            print(f"python test_student_management_api.py")
        else:
            print("创建课堂失败")
    else:
        print("创建用户失败")

if __name__ == "__main__":
    main() 