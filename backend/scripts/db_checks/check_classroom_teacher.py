from database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    result = db.execute(text('SELECT id, name, teacher_id FROM classrooms WHERE id = 13'))
    print('课堂13信息:')
    for row in result:
        print(f'  课堂ID: {row[0]}, 名称: {row[1]}, 教师ID: {row[2]}')
    
    result = db.execute(text('SELECT id, username, full_name FROM api_users WHERE id = 10'))
    print('\n教师10信息:')
    for row in result:
        print(f'  教师ID: {row[0]}, 用户名: {row[1]}, 姓名: {row[2]}')
finally:
    db.close() 