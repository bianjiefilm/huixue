from database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    result = db.execute(text('SELECT id, classroom_course_id, student_id, graded_at, is_excellent_work FROM student_course_progress WHERE classroom_course_id IN (8, 9) AND graded_at IS NOT NULL'))
    print('已点评的进度记录:')
    for row in result:
        print(f'  ID: {row[0]}, 课堂课程ID: {row[1]}, 学生ID: {row[2]}, 点评时间: {row[3]}, 是否优秀: {row[4]}')
finally:
    db.close() 