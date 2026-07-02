#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化实践详情测试数据
创建实践、任务、技能标签等测试数据
"""

from sqlalchemy.orm import Session
from database import get_db, engine, Base
import models
from datetime import datetime

def create_test_practice_data():
    """创建测试实践数据"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查是否已存在测试数据
        existing_practice = db.query(models.Practice).filter(models.Practice.id == 501).first()
        if existing_practice:
            print("测试数据已存在，跳过创建")
            return
        
        # 创建测试实践
        test_practice = models.Practice(
            id=501,
            title="Kafka 基础实践",
            description="动手搭建 Kafka 集群并实现消息发布/订阅",
            direction="大数据",
            category="流式处理",
            difficulty=models.DifficultyLevelEnum.intermediate,
            summary="本实践课程将带领学生从零开始搭建Kafka集群，学习消息队列的核心概念，掌握生产者和消费者的开发技巧。通过实际操作，深入理解分布式消息系统的工作原理。",
            coin=120,
            task_count=5
        )
        
        db.add(test_practice)
        db.flush()  # 获取ID
        
        # 创建测试任务
        tasks = [
            {
                "title": "安装 Kafka",
                "coin": 20,
                "task_type": models.TaskTypeEnum.PRACTICE,
                "order_in_practice": 1
            },
            {
                "title": "创建 Topic",
                "coin": 20,
                "task_type": models.TaskTypeEnum.PRACTICE,
                "order_in_practice": 2
            },
            {
                "title": "Kafka 基础概念测试",
                "coin": 15,
                "task_type": models.TaskTypeEnum.SINGLE_CHOICE,
                "order_in_practice": 3
            },
            {
                "title": "消息发布订阅判断",
                "coin": 10,
                "task_type": models.TaskTypeEnum.TRUE_FALSE,
                "order_in_practice": 4
            },
            {
                "title": "集群配置实践",
                "coin": 55,
                "task_type": models.TaskTypeEnum.PRACTICE,
                "order_in_practice": 5
            }
        ]
        
        for task_data in tasks:
            task = models.Task(
                practice_id=test_practice.id,
                **task_data
            )
            db.add(task)
        
        # 创建技能标签
        skills = ["Kafka", "ZooKeeper", "消息队列", "分布式系统"]
        for skill_name in skills:
            skill = models.PracticeSkill(
                practice_id=test_practice.id,
                skill_name=skill_name
            )
            db.add(skill)
        
        # 创建更多推荐实践数据
        recommended_practices = [
            {
                "id": 502,
                "title": "Spark Streaming 实时处理",
                "direction": "大数据",
                "category": "流式处理",
                "difficulty": models.DifficultyLevelEnum.advanced,
                "coin": 150,
                "task_count": 6
            },
            {
                "id": 503,
                "title": "Flink 实时计算入门",
                "direction": "大数据",
                "category": "流式处理",
                "difficulty": models.DifficultyLevelEnum.intermediate,
                "coin": 100,
                "task_count": 4
            },
            {
                "id": 504,
                "title": "Hadoop HDFS 实践",
                "direction": "大数据",
                "category": "存储系统",
                "difficulty": models.DifficultyLevelEnum.beginner,
                "coin": 80,
                "task_count": 3
            }
        ]
        
        for practice_data in recommended_practices:
            practice = models.Practice(**practice_data)
            db.add(practice)
        
        # 创建测试课堂
        test_classroom = models.Classroom(
            id=1,
            name="23级大数据实训班",
            teacher_id=1,
            start_date=datetime.now(),
            end_date=datetime.now().replace(month=12),
            academic_year="2023-2024",
            semester="第一学期",
            status=models.ClassroomStatusEnum.ONGOING,
            student_count=30
        )
        db.add(test_classroom)
        
        # 提交所有更改
        db.commit()
        print("✅ 测试数据创建成功！")
        
        # 显示创建的数据摘要
        print(f"创建的实践: {test_practice.title} (ID: {test_practice.id})")
        print(f"创建的任务数量: {len(tasks)}")
        print(f"创建的技能标签: {skills}")
        print(f"创建的推荐实践数量: {len(recommended_practices)}")
        print(f"创建的测试课堂: {test_classroom.name} (ID: {test_classroom.id})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建测试数据失败: {str(e)}")
        raise
    finally:
        db.close()

def verify_test_data():
    """验证测试数据"""
    db = next(get_db())
    
    try:
        # 验证实践数据
        practice = db.query(models.Practice).filter(models.Practice.id == 501).first()
        if practice:
            print(f"✅ 实践数据验证成功: {practice.title}")
            
            # 验证任务数据
            tasks = db.query(models.Task).filter(models.Task.practice_id == practice.id).all()
            print(f"✅ 任务数据验证成功: {len(tasks)} 个任务")
            
            # 验证技能标签
            skills = db.query(models.PracticeSkill).filter(models.PracticeSkill.practice_id == practice.id).all()
            print(f"✅ 技能标签验证成功: {len(skills)} 个标签")
            
            # 验证课堂数据
            classroom = db.query(models.Classroom).filter(models.Classroom.id == 1).first()
            if classroom:
                print(f"✅ 课堂数据验证成功: {classroom.name}")
            else:
                print("❌ 课堂数据验证失败")
        else:
            print("❌ 实践数据验证失败")
            
    except Exception as e:
        print(f"❌ 验证测试数据失败: {str(e)}")
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始初始化实践详情测试数据")
    print("=" * 50)
    
    try:
        create_test_practice_data()
        print("\n" + "=" * 30)
        print("📋 验证测试数据")
        verify_test_data()
        
        print("\n" + "=" * 50)
        print("✅ 测试数据初始化完成！")
        print("\n📝 创建的测试数据:")
        print("- 实践ID 501: Kafka 基础实践")
        print("- 5个任务关卡（不同类型和状态）")
        print("- 4个技能标签")
        print("- 3个推荐实践")
        print("- 课堂ID 1: 23级大数据实训班")
        print("\n💡 现在可以运行 test_practice_detail_api.py 进行API测试")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")

if __name__ == "__main__":
    main() 