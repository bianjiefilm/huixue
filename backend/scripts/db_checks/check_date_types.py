#!/usr/bin/env python3
"""检查数据库中的日期类型"""

from database import get_db
from models import Classroom
from datetime import datetime, timezone

def check_date_types():
    db = next(get_db())
    try:
        classroom = db.query(Classroom).first()
        if classroom:
            print(f"end_date type: {type(classroom.end_date)}")
            print(f"end_date value: {classroom.end_date}")
            print(f"end_date timezone: {classroom.end_date.tzinfo if hasattr(classroom.end_date, 'tzinfo') else 'No tzinfo'}")
            
            # 测试日期比较
            test_datetime = datetime.now(timezone.utc)
            print(f"test_datetime type: {type(test_datetime)}")
            print(f"test_datetime value: {test_datetime}")
            
            try:
                result = test_datetime > classroom.end_date
                print(f"Comparison result: {result}")
            except Exception as e:
                print(f"Comparison error: {e}")
        else:
            print("No classroom found")
    finally:
        db.close()

if __name__ == "__main__":
    check_date_types() 