#!/usr/bin/env python3
"""为现有实践添加任务和技能数据"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.models import Practice, Task, PracticeSkill, TaskTypeEnum
from app.core.config import settings
import json

def add_tasks_and_skills_for_practice(practice_id: int):
    """为指定实践添加任务和技能"""
    engine = create_engine(settings.database_url)
    
    with Session(engine) as db:
        # 获取实践
        practice = db.query(Practice).filter(Practice.id == practice_id).first()
        if not practice:
            print(f"Practice with ID {practice_id} not found!")
            return
        
        print(f"\n=== Adding data for Practice: {practice.title} ===")
        
        # 根据实践定义任务
        if practice_id == 1:  # Hadoop分布式文件系统实践
            tasks_data = [
                {
                    "title": "搭建Hadoop单机环境",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 1,
                    "coin": 30,
                    "difficulty": "beginner",
                    "skills": json.dumps(["Hadoop", "HDFS", "环境配置"]),
                    "handbook_markdown": "# 搭建Hadoop单机环境\n\n## 任务目标\n在本地搭建一个单机版的Hadoop环境，包括HDFS和YARN。\n\n## 步骤\n1. 下载并安装Hadoop\n2. 配置环境变量\n3. 修改配置文件\n4. 格式化HDFS\n5. 启动Hadoop服务"
                },
                {
                    "title": "HDFS基本操作",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 2,
                    "coin": 40,
                    "difficulty": "beginner",
                    "skills": json.dumps(["HDFS", "命令行操作"]),
                    "handbook_markdown": "# HDFS基本操作\n\n## 任务目标\n学习并掌握HDFS的基本命令操作。\n\n## 内容\n- 创建目录\n- 上传文件\n- 下载文件\n- 查看文件内容\n- 删除文件和目录"
                },
                {
                    "title": "编写MapReduce程序",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 3,
                    "coin": 50,
                    "difficulty": "intermediate",
                    "skills": json.dumps(["MapReduce", "Java编程"]),
                    "handbook_markdown": "# 编写MapReduce程序\n\n## 任务目标\n编写一个简单的WordCount MapReduce程序。\n\n## 要求\n1. 使用Java编写\n2. 实现Map和Reduce函数\n3. 在Hadoop上运行并验证结果"
                }
            ]
            
            skills_data = ["Hadoop", "HDFS", "MapReduce", "分布式系统", "大数据"]
            
        elif practice_id == 2:  # Python数据分析入门
            tasks_data = [
                {
                    "title": "NumPy数组操作",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 1,
                    "coin": 25,
                    "difficulty": "beginner",
                    "skills": json.dumps(["Python", "NumPy", "数组操作"]),
                    "handbook_markdown": "# NumPy数组操作\n\n## 任务目标\n学习NumPy库的基本数组操作。\n\n## 内容\n- 创建数组\n- 数组索引和切片\n- 数组运算\n- 数组形状变换"
                },
                {
                    "title": "Pandas数据处理",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 2,
                    "coin": 35,
                    "difficulty": "beginner",
                    "skills": json.dumps(["Python", "Pandas", "数据处理"]),
                    "handbook_markdown": "# Pandas数据处理\n\n## 任务目标\n使用Pandas进行数据读取和基本处理。\n\n## 内容\n- 读取CSV文件\n- 数据筛选和过滤\n- 数据聚合\n- 数据可视化"
                }
            ]
            
            skills_data = ["Python", "NumPy", "Pandas", "数据分析", "数据可视化"]
            
        else:
            # 为其他实践添加通用任务
            tasks_data = [
                {
                    "title": f"{practice.title} - 基础任务",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 1,
                    "coin": 30,
                    "difficulty": "beginner",
                    "skills": json.dumps([practice.direction, practice.category]),
                    "handbook_markdown": f"# {practice.title} - 基础任务\n\n## 任务目标\n完成{practice.title}的基础练习。"
                },
                {
                    "title": f"{practice.title} - 进阶任务",
                    "task_type": TaskTypeEnum.PRACTICE,
                    "order_in_practice": 2,
                    "coin": 40,
                    "difficulty": "intermediate",
                    "skills": json.dumps([practice.direction, practice.category]),
                    "handbook_markdown": f"# {practice.title} - 进阶任务\n\n## 任务目标\n完成{practice.title}的进阶练习。"
                }
            ]
            
            skills_data = [practice.direction, practice.category, "实践"]
        
        # 添加任务
        for task_data in tasks_data:
            # 检查是否已存在
            existing_task = db.query(Task).filter(
                Task.practice_id == practice_id,
                Task.title == task_data["title"]
            ).first()
            
            if not existing_task:
                task = Task(practice_id=practice_id, **task_data)
                db.add(task)
                print(f"✅ Added task: {task_data['title']}")
            else:
                print(f"⏭️  Task already exists: {task_data['title']}")
        
        # 添加技能
        for skill_name in skills_data:
            # 检查是否已存在
            existing_skill = db.query(PracticeSkill).filter(
                PracticeSkill.practice_id == practice_id,
                PracticeSkill.skill_name == skill_name
            ).first()
            
            if not existing_skill:
                skill = PracticeSkill(practice_id=practice_id, skill_name=skill_name)
                db.add(skill)
                print(f"✅ Added skill: {skill_name}")
            else:
                print(f"⏭️  Skill already exists: {skill_name}")
        
        # 提交更改
        db.commit()
        print(f"\n✅ Successfully added tasks and skills for practice ID {practice_id}")

def add_data_for_all_practices():
    """为所有实践添加任务和技能"""
    engine = create_engine(settings.database_url)
    
    with Session(engine) as db:
        # 获取所有实践
        practices = db.query(Practice).all()
        print(f"Found {len(practices)} practices")
        
        for practice in practices:
            add_tasks_and_skills_for_practice(practice.id)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了practice_id，只为该实践添加数据
        practice_id = int(sys.argv[1])
        add_tasks_and_skills_for_practice(practice_id)
    else:
        # 否则为所有实践添加数据
        add_data_for_all_practices()