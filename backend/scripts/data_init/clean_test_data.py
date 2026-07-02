from database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    # 删除测试数据
    db.execute(text('DELETE FROM student_course_progress WHERE classroom_course_id IN (6, 7)'))
    db.execute(text('DELETE FROM classroom_courses WHERE id IN (6, 7)'))
    db.execute(text('DELETE FROM classroom_students WHERE classroom_id = 11'))
    db.execute(text('DELETE FROM classrooms WHERE id = 11'))
    db.commit()
    print('✓ 旧测试数据已删除')
except Exception as e:
    print(f'删除失败: {e}')
    db.rollback()
finally:
    db.close() 