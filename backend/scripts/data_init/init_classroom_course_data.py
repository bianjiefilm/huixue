#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化课堂课程测试数据
"""

from database import get_db, engine, Base
from sqlalchemy.orm import Session
import models
from datetime import datetime, timezone, timedelta

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 获取数据库连接
db = next(get_db())

try:
    print("🚀 开始初始化课堂课程测试数据...")
    
    # 检查是否已有测试数据
    existing_classroom_courses = db.query(models.ClassroomCourse).count()
    if existing_classroom_courses > 0:
        print(f"⚠️  已存在 {existing_classroom_courses} 条课堂课程记录")
        response = input("是否清空现有数据并重新初始化？(y/N): ")
        if response.lower() != 'y':
            print("❌ 取消初始化")
            exit()
        
        # 清空现有数据
        db.query(models.StudentCourseProgress).delete()
        db.query(models.ClassroomCourse).delete()
        db.commit()
        print("🗑️  已清空现有课堂课程数据")
    
    # 获取现有的课堂和课程
    classrooms = db.query(models.Classroom).limit(3).all()
    courses = db.query(models.Course).limit(10).all()
    users = db.query(models.User).limit(5).all()
    
    if not classrooms:
        print("❌ 没有找到课堂数据，请先运行 init_data.py")
        exit()
    
    if not courses:
        print("❌ 没有找到课程数据，请先运行 init_data.py")
        exit()
    
    print(f"📚 找到 {len(classrooms)} 个课堂，{len(courses)} 个课程，{len(users)} 个用户")
    
    # 为每个课堂添加课程
    classroom_courses_created = 0
    student_progress_created = 0
    
    for i, classroom in enumerate(classrooms):
        print(f"\n📖 为课堂 '{classroom.name}' 添加课程...")
        
        # 为每个课堂添加3-5个课程
        course_count = min(5, len(courses))
        selected_courses = courses[:course_count]
        
        for j, course in enumerate(selected_courses):
            # 创建课堂课程记录
            classroom_course = models.ClassroomCourse(
                classroom_id=classroom.id,
                course_id=course.id,
                classroom_chapter_title=f"第{j+1}章 {course.title}",
                order_in_classroom=j + 1,
                teacher_publish_status=models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED if j == 0 
                    else models.CourseInClassroomStatusTeacherEnum.LEARNING if j < 3
                    else models.CourseInClassroomStatusTeacherEnum.COMPLETED,
                published_at=datetime.now(timezone.utc) - timedelta(days=j) if j > 0 else None,
                deadline_at=datetime.now(timezone.utc) + timedelta(days=7) if j < 3 else None,
                makeup_deadline_at=datetime.now(timezone.utc) + timedelta(days=14) if j < 3 else None,
                is_mandatory=True,
                allow_late_submission=True,
                total_score=100
            )
            
            db.add(classroom_course)
            db.flush()  # 获取ID
            classroom_courses_created += 1
            
            print(f"  ✅ 添加课程: {course.title} (状态: {classroom_course.teacher_publish_status.value})")
            
            # 为已发布的课程创建学生进度记录
            if classroom_course.teacher_publish_status != models.CourseInClassroomStatusTeacherEnum.UNPUBLISHED:
                for k, user in enumerate(users[:3]):  # 为前3个用户创建进度
                    # 根据课程状态和用户设置不同的学生状态
                    if classroom_course.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.COMPLETED:
                        student_status = models.CourseInClassroomStatusStudentEnum.COMPLETED_ON_TIME if k < 2 else models.CourseInClassroomStatusStudentEnum.COMPLETED_LATE
                        overall_score = 85 + k * 5
                        completed_task_count = 10
                    elif classroom_course.teacher_publish_status == models.CourseInClassroomStatusTeacherEnum.LEARNING:
                        student_status = models.CourseInClassroomStatusStudentEnum.LEARNING if k < 2 else models.CourseInClassroomStatusStudentEnum.NOT_STARTED
                        overall_score = 60 + k * 10 if k < 2 else 0
                        completed_task_count = 5 + k if k < 2 else 0
                    else:
                        student_status = models.CourseInClassroomStatusStudentEnum.NOT_STARTED
                        overall_score = 0
                        completed_task_count = 0
                    
                    progress = models.StudentCourseProgress(
                        classroom_course_id=classroom_course.id,
                        student_id=user.id,
                        student_status=student_status,
                        overall_score=overall_score,
                        final_calculated_score=overall_score,
                        first_access_at=datetime.now(timezone.utc) - timedelta(days=j+k) if student_status != models.CourseInClassroomStatusStudentEnum.NOT_STARTED else None,
                        last_submission_at=datetime.now(timezone.utc) - timedelta(hours=k+1) if completed_task_count > 0 else None,
                        total_time_spent_seconds=(j+1) * 3600 + k * 1800,  # 学习时间
                        completed_task_count=completed_task_count
                    )
                    
                    db.add(progress)
                    student_progress_created += 1
    
    # 提交所有更改
    db.commit()
    
    print(f"\n🎉 课堂课程测试数据初始化完成！")
    print(f"📊 统计信息:")
    print(f"  - 创建课堂课程记录: {classroom_courses_created} 条")
    print(f"  - 创建学生进度记录: {student_progress_created} 条")
    
    # 显示各状态的统计
    print(f"\n📈 课程状态分布:")
    for status in models.CourseInClassroomStatusTeacherEnum:
        count = db.query(models.ClassroomCourse).filter(
            models.ClassroomCourse.teacher_publish_status == status
        ).count()
        print(f"  - {status.value}: {count} 个")
    
    print(f"\n📈 学生状态分布:")
    for status in models.CourseInClassroomStatusStudentEnum:
        count = db.query(models.StudentCourseProgress).filter(
            models.StudentCourseProgress.student_status == status
        ).count()
        print(f"  - {status.value}: {count} 个")

except Exception as e:
    print(f"❌ 初始化失败: {e}")
    db.rollback()
finally:
    db.close() 