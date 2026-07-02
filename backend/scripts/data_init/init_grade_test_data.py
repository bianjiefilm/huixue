#!/usr/bin/env python3
"""
成绩管理功能测试数据初始化脚本

创建必要的测试数据：
1. 测试教师和学生用户
2. 测试课堂
3. 测试课程（实践和实训）
4. 学生课程进度记录
"""

import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from database import get_db, engine
import models
import crud

def create_test_users(db: Session):
    """创建测试用户"""
    print("创建测试用户...")
    
    from sqlalchemy import text
    
    # 检查教师是否已存在（在api_users表中）
    result = db.execute(text("SELECT id FROM api_users WHERE username = 'teacher001'"))
    existing_teacher = result.fetchone()
    
    if not existing_teacher:
        # 创建测试教师（在api_users表中）
        result = db.execute(text("""
            INSERT INTO api_users (username, email, full_name, created_at)
            VALUES ('teacher001', 'teacher001@example.com', '张老师', NOW())
            RETURNING id
        """))
        teacher_id = result.fetchone()[0]
        print(f"✓ 创建测试教师，ID: {teacher_id}")
    else:
        teacher_id = existing_teacher[0]
        print(f"✓ 测试教师已存在，ID: {teacher_id}")
    
    # 创建测试学生（需要在两个表中都创建）
    student_ids_users = []  # users表中的ID
    student_ids_api_users = []  # api_users表中的ID
    
    for i in range(1, 6):
        username = f"student{i:03d}"
        
        # 检查api_users表中是否存在
        result = db.execute(text("SELECT id FROM api_users WHERE username = :username"), {"username": username})
        existing_api_user = result.fetchone()
        
        if not existing_api_user:
            # 在api_users表中创建学生（用于classroom_students外键）
            result = db.execute(text("""
                INSERT INTO api_users (username, email, full_name, created_at)
                VALUES (:username, :email, :full_name, NOW())
                RETURNING id
            """), {
                "username": username,
                "email": f"{username}@example.com",
                "full_name": f"学生{i}"
            })
            api_user_id = result.fetchone()[0]
            student_ids_api_users.append(api_user_id)
            print(f"✓ 在api_users表创建学生{i}，ID: {api_user_id}")
        else:
            api_user_id = existing_api_user[0]
            student_ids_api_users.append(api_user_id)
            print(f"✓ api_users表中学生{i}已存在，ID: {api_user_id}")
        
        # 检查users表中是否存在
        result = db.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username})
        existing_user = result.fetchone()
        
        if not existing_user:
            # 在users表中创建学生（用于student_course_progress外键）
            # 使用相同的ID以保持一致性
            result = db.execute(text("""
                INSERT INTO users (id, username, password_hash, full_name, user_no, email, is_active, created_at)
                VALUES (:id, :username, 'hashed_password', :full_name, :user_no, :email, true, NOW())
                RETURNING id
            """), {
                "id": api_user_id,  # 使用相同的ID
                "username": username,
                "full_name": f"学生{i}",
                "user_no": f"S{i:03d}",
                "email": f"{username}@example.com"
            })
            user_id = result.fetchone()[0]
            student_ids_users.append(user_id)
            print(f"✓ 在users表创建学生{i}，ID: {user_id}")
        else:
            user_id = existing_user[0]
            student_ids_users.append(user_id)
            print(f"✓ users表中学生{i}已存在，ID: {user_id}")
    
    db.commit()
    print(f"✓ 学生在api_users表的IDs: {student_ids_api_users}")
    print(f"✓ 学生在users表的IDs: {student_ids_users}")
    
    return teacher_id, student_ids_users, student_ids_api_users

def create_test_courses(db: Session):
    """创建测试课程"""
    print("创建测试课程...")
    
    # 创建实践课程
    practice_course = models.Course(
        title="Python基础实践",
        course_type=models.CourseTypeEnum.PRACTICE,
        description="Python编程基础实践课程",
        difficulty=models.DifficultyEnum.BEGINNER,
        direction="编程开发",
        categories=["Python", "编程基础"],
        practice_task_count=10
    )
    
    # 创建实训课程
    training_course = models.Course(
        title="数据分析实训",
        course_type=models.CourseTypeEnum.TRAINING,
        description="数据分析综合实训项目",
        difficulty=models.DifficultyEnum.INTERMEDIATE,
        direction="数据科学",
        categories=["数据分析", "Python"],
        practice_task_count=5
    )
    
    # 检查课程是否已存在
    existing_practice = db.query(models.Course).filter(
        models.Course.title == "Python基础实践"
    ).first()
    
    if not existing_practice:
        db.add(practice_course)
        db.flush()
        practice_course_id = practice_course.id
    else:
        practice_course_id = existing_practice.id
        print("✓ 实践课程已存在")
    
    existing_training = db.query(models.Course).filter(
        models.Course.title == "数据分析实训"
    ).first()
    
    if not existing_training:
        db.add(training_course)
        db.flush()
        training_course_id = training_course.id
    else:
        training_course_id = existing_training.id
        print("✓ 实训课程已存在")
    
    db.commit()
    print(f"✓ 实践课程ID: {practice_course_id}")
    print(f"✓ 实训课程ID: {training_course_id}")
    
    return practice_course_id, training_course_id

def create_test_classroom(db: Session, teacher_id: int, practice_course_id: int, training_course_id: int):
    """创建测试课堂"""
    print("创建测试课堂...")
    
    # 检查课堂是否已存在
    existing_classroom = db.query(models.Classroom).filter(
        models.Classroom.name == "测试课堂",
        models.Classroom.teacher_id == teacher_id
    ).first()
    
    if existing_classroom:
        classroom_id = existing_classroom.id
        print(f"✓ 测试课堂已存在，ID: {classroom_id}")
    else:
        # 创建课堂
        start_date = datetime.now(timezone.utc).date()
        end_date = start_date + timedelta(days=90)
        
        classroom = models.Classroom(
            name="测试课堂",
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            academic_year="2024-2025",
            semester="第一学期",
            status=models.ClassroomStatusEnum.ONGOING
        )
        
        db.add(classroom)
        db.flush()
        classroom_id = classroom.id
        db.commit()
        print(f"✓ 创建测试课堂，ID: {classroom_id}")
    
    # 添加课程到课堂
    practice_classroom_course = add_course_to_classroom(
        db, classroom_id, practice_course_id, "第一章 Python基础"
    )
    
    training_classroom_course = add_course_to_classroom(
        db, classroom_id, training_course_id, "第二章 数据分析实训"
    )
    
    return classroom_id, practice_classroom_course.id, training_classroom_course.id

def add_course_to_classroom(db: Session, classroom_id: int, course_id: int, chapter_title: str):
    """添加课程到课堂"""
    existing = db.query(models.ClassroomCourse).filter(
        models.ClassroomCourse.classroom_id == classroom_id,
        models.ClassroomCourse.course_id == course_id
    ).first()
    
    if existing:
        return existing
    
    classroom_course = models.ClassroomCourse(
        classroom_id=classroom_id,
        course_id=course_id,
        classroom_chapter_title=chapter_title,
        teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.LEARNING,
        published_at=datetime.now(timezone.utc),
        deadline_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_mandatory=True,
        total_score=100
    )
    
    db.add(classroom_course)
    db.commit()
    db.refresh(classroom_course)
    
    return classroom_course

def add_students_to_classroom(db: Session, classroom_id: int, student_ids_api_users: list):
    """添加学生到课堂（使用api_users表的ID）"""
    print("添加学生到课堂...")
    
    for student_id in student_ids_api_users:
        existing = db.query(models.ClassroomStudent).filter(
            models.ClassroomStudent.classroom_id == classroom_id,
            models.ClassroomStudent.student_id == student_id
        ).first()
        
        if not existing:
            classroom_student = models.ClassroomStudent(
                classroom_id=classroom_id,
                student_id=student_id,
                joined_at=datetime.now(timezone.utc)
            )
            db.add(classroom_student)
    
    db.commit()
    print("✓ 学生已添加到课堂")

def create_student_progress(db: Session, practice_classroom_course_id: int, training_classroom_course_id: int, student_ids_users: list):
    """创建学生课程进度（使用users表的ID）"""
    print("创建学生课程进度...")
    
    for i, student_id in enumerate(student_ids_users):
        # 实践课程进度
        practice_progress = models.StudentCourseProgress(
            classroom_course_id=practice_classroom_course_id,
            student_id=student_id,
            student_status=models.CourseInClassroomStatusStudentEnum.LEARNING,
            overall_score=80 + i * 5,  # 80, 85, 90, 95, 100
            teacher_penalties=0,
            final_calculated_score=80 + i * 5,
            first_access_at=datetime.now(timezone.utc) - timedelta(days=10),
            completed_task_count=5 + i,
            total_time_spent_seconds=3600 * (2 + i)
        )
        
        # 实训课程进度
        training_progress = models.StudentCourseProgress(
            classroom_course_id=training_classroom_course_id,
            student_id=student_id,
            student_status=models.CourseInClassroomStatusStudentEnum.LEARNING,
            overall_score=75 + i * 5,
            teacher_penalties=0,
            final_calculated_score=75 + i * 5,
            first_access_at=datetime.now(timezone.utc) - timedelta(days=8),
            training_submission_status=models.SubmissionStatusEnum.SUBMITTED if i < 3 else models.SubmissionStatusEnum.IN_PROGRESS,
            last_submission_at=datetime.now(timezone.utc) - timedelta(days=2) if i < 3 else None,
            training_assignment_files='{"design_files": [{"file_name": "design.pdf", "file_url": "/files/design.pdf"}], "experiment_reports": [{"file_name": "report.docx", "file_url": "/files/report.docx"}]}' if i < 3 else None
        )
        
        # 检查是否已存在
        existing_practice = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == practice_classroom_course_id,
            models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not existing_practice:
            db.add(practice_progress)
        
        existing_training = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.classroom_course_id == training_classroom_course_id,
            models.StudentCourseProgress.student_id == student_id
        ).first()
        
        if not existing_training:
            db.add(training_progress)
    
    db.commit()
    print("✓ 学生课程进度已创建")

def main():
    """主函数"""
    print("成绩管理功能测试数据初始化")
    print("=" * 50)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 1. 创建测试用户
        teacher_id, student_ids_users, student_ids_api_users = create_test_users(db)
        
        # 2. 创建测试课程
        practice_course_id, training_course_id = create_test_courses(db)
        
        # 3. 创建测试课堂
        classroom_id, practice_classroom_course_id, training_classroom_course_id = create_test_classroom(
            db, teacher_id, practice_course_id, training_course_id
        )
        
        # 4. 添加学生到课堂（使用api_users表的ID）
        add_students_to_classroom(db, classroom_id, student_ids_api_users)
        
        # 5. 创建学生课程进度（使用users表的ID）
        create_student_progress(db, practice_classroom_course_id, training_classroom_course_id, student_ids_users)
        
        print("\n" + "=" * 50)
        print("测试数据初始化完成！")
        print(f"教师ID: {teacher_id}")
        print(f"课堂ID: {classroom_id}")
        print(f"实践课程ID: {practice_classroom_course_id}")
        print(f"实训课程ID: {training_classroom_course_id}")
        print(f"学生在users表的IDs: {student_ids_users}")
        print(f"学生在api_users表的IDs: {student_ids_api_users}")
        print("\n现在可以运行成绩管理API测试了！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 