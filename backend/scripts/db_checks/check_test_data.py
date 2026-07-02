#!/usr/bin/env python3
"""检查测试数据"""

from database import get_db
from sqlalchemy import text
import models

db = next(get_db())
try:
    # 检查课堂课程关系
    result = db.execute(text('SELECT cc.id, cc.classroom_id, cc.course_id, c.title, c.course_type FROM classroom_courses cc JOIN courses c ON cc.course_id = c.id WHERE cc.classroom_id = 13'))
    print('课堂课程关系:')
    for row in result:
        print(f'  ID: {row[0]}, 课堂ID: {row[1]}, 课程ID: {row[2]}, 标题: {row[3]}, 类型: {row[4]}')
    
    # 检查学生课程进度
    result = db.execute(text('SELECT id, classroom_course_id, student_id, training_submission_status FROM student_course_progress WHERE classroom_course_id IN (8, 9)'))
    print('\n学生课程进度:')
    for row in result:
        print(f'  ID: {row[0]}, 课堂课程ID: {row[1]}, 学生ID: {row[2]}, 提交状态: {row[3]}')
    
    # 检查课堂学生关系
    result = db.execute(text('SELECT classroom_id, student_id FROM classroom_students WHERE classroom_id = 13'))
    print('\n课堂学生关系:')
    for row in result:
        print(f'  课堂ID: {row[0]}, 学生ID: {row[1]}')
        
    # 检查用户数据
    result = db.execute(text('SELECT id, username FROM api_users WHERE id IN (10, 11, 12, 13, 14, 15)'))
    print('\napi_users表用户:')
    for row in result:
        print(f'  ID: {row[0]}, 用户名: {row[1]}')
        
    result = db.execute(text('SELECT id, username FROM users WHERE id IN (7, 8, 9, 10, 11)'))
    print('\nusers表用户:')
    for row in result:
        print(f'  ID: {row[0]}, 用户名: {row[1]}')
        
finally:
    db.close()

 