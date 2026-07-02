#!/usr/bin/env python3
"""检查实践数据，包括任务和技能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.models import Practice, Task, PracticeSkill
from app.core.config import settings

def check_practice_data(practice_id: int):
    """检查指定实践的数据"""
    engine = create_engine(settings.database_url)
    
    with Session(engine) as db:
        # 获取实践
        practice = db.query(Practice).filter(Practice.id == practice_id).first()
        if not practice:
            print(f"Practice with ID {practice_id} not found!")
            return
        
        print(f"\n=== Practice Details ===")
        print(f"ID: {practice.id}")
        print(f"Title: {practice.title}")
        print(f"Task Count (field): {practice.task_count}")
        
        # 检查任务
        tasks = db.query(Task).filter(Task.practice_id == practice_id).all()
        print(f"\n=== Tasks (Total: {len(tasks)}) ===")
        for task in tasks:
            print(f"- Task ID: {task.id}, Title: {task.title}, Order: {task.order_in_practice}")
        
        # 检查技能
        skills = db.query(PracticeSkill).filter(PracticeSkill.practice_id == practice_id).all()
        print(f"\n=== Skills (Total: {len(skills)}) ===")
        for skill in skills:
            print(f"- Skill ID: {skill.id}, Name: {skill.skill_name}")
        
        # 检查所有实践的任务和技能统计
        print(f"\n=== Overall Statistics ===")
        total_practices = db.query(Practice).count()
        practices_with_tasks = db.query(Practice).join(Task).distinct().count()
        practices_with_skills = db.query(Practice).join(PracticeSkill).distinct().count()
        total_tasks = db.query(Task).count()
        total_skills = db.query(PracticeSkill).count()
        
        print(f"Total Practices: {total_practices}")
        print(f"Practices with Tasks: {practices_with_tasks}")
        print(f"Practices with Skills: {practices_with_skills}")
        print(f"Total Tasks: {total_tasks}")
        print(f"Total Skills: {total_skills}")

if __name__ == "__main__":
    # 从命令行参数获取practice_id，默认为1
    practice_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    check_practice_data(practice_id)