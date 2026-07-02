#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据初始化脚本 - 课程实践模块
用于创建测试数据，包括课程、微型实验、课堂等
"""

from sqlalchemy.orm import Session
from database import engine, get_db
from models import (
    User, Course, Chapter, CourseResource, CourseAssessment, 
    Practice, Classroom, DifficultyEnum, DifficultyLevelEnum, CourseTypeEnum, CourseVisibilityEnum, ClassroomStatusEnum
)
from datetime import datetime, timedelta

def init_test_data():
    """初始化测试数据"""
    db = next(get_db())
    
    try:
        # 1. 创建测试用户（教师）
        teachers = [
            User(
                username="teacher1",
                email="teacher1@example.com",
                full_name="张教授"
            ),
            User(
                username="teacher2", 
                email="teacher2@example.com",
                full_name="李老师"
            ),
            User(
                username="teacher3",
                email="teacher3@example.com", 
                full_name="王副教授"
            )
        ]
        
        for teacher in teachers:
            existing = db.query(User).filter(User.username == teacher.username).first()
            if not existing:
                db.add(teacher)
        
        db.commit()
        
        # 获取教师ID
        teacher1 = db.query(User).filter(User.username == "teacher1").first()
        teacher2 = db.query(User).filter(User.username == "teacher2").first()
        teacher3 = db.query(User).filter(User.username == "teacher3").first()
        
        # 2. 创建课程教材 - 使用现有数据库结构
        courses = [
            Course(
                title="大数据基础（实验版）",
                course_type=CourseTypeEnum.COURSE_MATERIAL,
                description="涵盖 Hadoop、Spark 初步实践，适合初学者入门大数据技术",
                cover_url="https://cdn.example.com/cover/bigdata_basic.png",
                difficulty=DifficultyEnum.BEGINNER,  # 使用DifficultyEnum
                direction="大数据",
                categories=["数据处理", "分布式计算"],  # 使用数组
                source="清华大学出版社",
                practice_task_count=8,  # 使用正确的字段名
                outline_url="https://cdn.example.com/outline/bigdata_basic.pdf",
                material_resources_count=3,
                material_assessments_count=2,
                visibility=CourseVisibilityEnum.PUBLIC_PLATFORM
                # 移除creator_id，避免外键约束问题
            ),
            Course(
                title="机器学习实战",
                course_type=CourseTypeEnum.COURSE_MATERIAL,
                description="深入学习机器学习算法，包含大量实践案例和项目",
                cover_url="https://cdn.example.com/cover/ml_practice.png",
                difficulty=DifficultyEnum.INTERMEDIATE,  # 使用DifficultyEnum
                direction="人工智能",
                categories=["机器学习", "算法"],
                source="北京理工大学出版社",
                practice_task_count=12,
                outline_url="https://cdn.example.com/outline/ml_practice.pdf",
                material_resources_count=5,
                material_assessments_count=3,
                visibility=CourseVisibilityEnum.PUBLIC_PLATFORM
            ),
            Course(
                title="深度学习与神经网络",
                course_type=CourseTypeEnum.COURSE_MATERIAL,
                description="掌握深度学习核心技术，包括CNN、RNN、Transformer等",
                cover_url="https://cdn.example.com/cover/deep_learning.png",
                difficulty=DifficultyEnum.ADVANCED,  # 使用DifficultyEnum
                direction="人工智能",
                categories=["深度学习", "神经网络"],
                source="电子工业出版社",
                practice_task_count=15,
                outline_url="https://cdn.example.com/outline/deep_learning.pdf",
                material_resources_count=6,
                material_assessments_count=4,
                visibility=CourseVisibilityEnum.PUBLIC_PLATFORM
            ),
            Course(
                title="云计算技术与应用",
                course_type=CourseTypeEnum.COURSE_MATERIAL,
                description="学习云计算基础架构、容器技术、微服务等现代云技术",
                cover_url="https://cdn.example.com/cover/cloud_computing.png",
                difficulty=DifficultyEnum.INTERMEDIATE,  # 使用DifficultyEnum
                direction="云计算",
                categories=["云原生", "容器技术"],
                source="机械工业出版社",
                practice_task_count=10,
                outline_url="https://cdn.example.com/outline/cloud_computing.pdf",
                material_resources_count=4,
                material_assessments_count=2,
                visibility=CourseVisibilityEnum.PUBLIC_PLATFORM
            ),
            Course(
                title="区块链技术原理",
                course_type=CourseTypeEnum.COURSE_MATERIAL,
                description="深入理解区块链技术原理，掌握智能合约开发",
                cover_url="https://cdn.example.com/cover/blockchain.png",
                difficulty=DifficultyEnum.ADVANCED,  # 使用DifficultyEnum
                direction="区块链",
                categories=["分布式系统", "智能合约"],
                source="人民邮电出版社",
                practice_task_count=6,
                outline_url="https://cdn.example.com/outline/blockchain.pdf",
                material_resources_count=3,
                material_assessments_count=2,
                visibility=CourseVisibilityEnum.PUBLIC_PLATFORM
            )
        ]
        
        for course in courses:
            existing = db.query(Course).filter(Course.title == course.title).first()
            if not existing:
                db.add(course)
        
        db.commit()
        
        # 获取课程ID
        course_bigdata = db.query(Course).filter(Course.title == "大数据基础（实验版）").first()
        course_ml = db.query(Course).filter(Course.title == "机器学习实战").first()
        course_dl = db.query(Course).filter(Course.title == "深度学习与神经网络").first()
        course_cloud = db.query(Course).filter(Course.title == "云计算技术与应用").first()
        course_blockchain = db.query(Course).filter(Course.title == "区块链技术原理").first()
        
        # 3. 创建课程章节
        chapters = [
            # 大数据基础课程章节
            Chapter(course_id=course_bigdata.id, title="HDFS 分布式文件系统", order_index=1, experiment_count=2),
            Chapter(course_id=course_bigdata.id, title="MapReduce 编程模型", order_index=2, experiment_count=3),
            Chapter(course_id=course_bigdata.id, title="Spark 核心技术", order_index=3, experiment_count=3),
            
            # 机器学习课程章节
            Chapter(course_id=course_ml.id, title="监督学习算法", order_index=1, experiment_count=4),
            Chapter(course_id=course_ml.id, title="无监督学习", order_index=2, experiment_count=3),
            Chapter(course_id=course_ml.id, title="模型评估与优化", order_index=3, experiment_count=5),
            
            # 深度学习课程章节
            Chapter(course_id=course_dl.id, title="神经网络基础", order_index=1, experiment_count=3),
            Chapter(course_id=course_dl.id, title="卷积神经网络", order_index=2, experiment_count=4),
            Chapter(course_id=course_dl.id, title="循环神经网络", order_index=3, experiment_count=4),
            Chapter(course_id=course_dl.id, title="Transformer架构", order_index=4, experiment_count=4),
        ]
        
        for chapter in chapters:
            existing = db.query(Chapter).filter(
                Chapter.course_id == chapter.course_id,
                Chapter.title == chapter.title
            ).first()
            if not existing:
                db.add(chapter)
        
        db.commit()
        
        # 4. 创建课程教学资源
        resources = [
            # 大数据基础资源
            CourseResource(
                course_id=course_bigdata.id,
                title="HDFS实验指导书.pdf",
                url="https://cdn.example.com/resources/hdfs_guide.pdf",
                resource_type="pdf"
            ),
            CourseResource(
                course_id=course_bigdata.id,
                title="MapReduce示例代码",
                url="https://cdn.example.com/resources/mapreduce_examples.zip",
                resource_type="code"
            ),
            CourseResource(
                course_id=course_bigdata.id,
                title="Spark入门PPT",
                url="https://cdn.example.com/resources/spark_intro.pptx",
                resource_type="ppt"
            ),
            
            # 机器学习资源
            CourseResource(
                course_id=course_ml.id,
                title="机器学习算法详解.pdf",
                url="https://cdn.example.com/resources/ml_algorithms.pdf",
                resource_type="pdf"
            ),
            CourseResource(
                course_id=course_ml.id,
                title="Python机器学习代码库",
                url="https://cdn.example.com/resources/ml_python_code.zip",
                resource_type="code"
            ),
        ]
        
        for resource in resources:
            existing = db.query(CourseResource).filter(
                CourseResource.course_id == resource.course_id,
                CourseResource.title == resource.title
            ).first()
            if not existing:
                db.add(resource)
        
        db.commit()
        
        # 5. 创建课程考核
        assessments = [
            CourseAssessment(
                course_id=course_bigdata.id,
                title="大数据基础期中考试",
                url="https://cdn.example.com/assessments/bigdata_midterm.pdf",
                assessment_type="exam"
            ),
            CourseAssessment(
                course_id=course_bigdata.id,
                title="Hadoop实践作业",
                url="https://cdn.example.com/assessments/hadoop_assignment.pdf",
                assessment_type="assignment"
            ),
            CourseAssessment(
                course_id=course_ml.id,
                title="机器学习项目评估",
                url="https://cdn.example.com/assessments/ml_project.pdf",
                assessment_type="project"
            ),
        ]
        
        for assessment in assessments:
            existing = db.query(CourseAssessment).filter(
                CourseAssessment.course_id == assessment.course_id,
                CourseAssessment.title == assessment.title
            ).first()
            if not existing:
                db.add(assessment)
        
        db.commit()
        
        # 6. 创建微型实验
        practices = [
            Practice(
                title="Kafka 基础实践",
                description="学习Kafka消息队列的基本使用和配置",
                cover_url="https://cdn.example.com/practice/kafka_basic.png",
                direction="大数据",
                category="流式处理",
                difficulty=DifficultyLevelEnum.intermediate,  # 使用小写
                parent_course_id=course_bigdata.id
            ),
            Practice(
                title="Docker 容器化部署",
                description="掌握Docker容器技术，实现应用容器化部署",
                cover_url="https://cdn.example.com/practice/docker_deploy.png",
                direction="云计算",
                category="容器技术",
                difficulty=DifficultyLevelEnum.beginner,  # 使用小写
                parent_course_id=course_cloud.id
            ),
            Practice(
                title="TensorFlow 图像分类",
                description="使用TensorFlow实现卷积神经网络进行图像分类",
                cover_url="https://cdn.example.com/practice/tf_image_classification.png",
                direction="人工智能",
                category="深度学习",
                difficulty=DifficultyLevelEnum.advanced,  # 使用小写
                parent_course_id=course_dl.id
            ),
            Practice(
                title="智能合约开发实践",
                description="基于Solidity开发以太坊智能合约",
                cover_url="https://cdn.example.com/practice/smart_contract.png",
                direction="区块链",
                category="智能合约",
                difficulty=DifficultyLevelEnum.advanced,  # 使用小写
                parent_course_id=course_blockchain.id
            ),
            Practice(
                title="Kubernetes 集群管理",
                description="学习K8s集群部署和管理，掌握容器编排技术",
                cover_url="https://cdn.example.com/practice/k8s_cluster.png",
                direction="云计算",
                category="容器编排",
                difficulty=DifficultyLevelEnum.intermediate,  # 使用小写
                parent_course_id=course_cloud.id
            ),
            Practice(
                title="推荐系统算法实现",
                description="实现协同过滤、内容推荐等推荐算法",
                cover_url="https://cdn.example.com/practice/recommendation.png",
                direction="人工智能",
                category="机器学习",
                difficulty=DifficultyLevelEnum.intermediate,  # 使用小写
                parent_course_id=course_ml.id
            )
        ]
        
        for practice in practices:
            existing = db.query(Practice).filter(Practice.title == practice.title).first()
            if not existing:
                db.add(practice)
        
        db.commit()
        
        # 7. 创建课堂 - 暂时跳过，避免外键约束问题
        # now = datetime.now()
        # classrooms = [
        #     Classroom(
        #         name="2025春·大数据基础实验班",
        #         source_course_id=course_bigdata.id,  # 使用source_course_id
        #         teacher_id=1,  # 使用简单的ID，避免外键约束
        #         credit=4,
        #         start_date=now + timedelta(days=30),
        #         end_date=now + timedelta(days=150),
        #         academic_year="2024-2025",
        #         semester="春季",
        #         status=ClassroomStatusEnum.NOT_STARTED,
        #         student_count=0,
        #         sync_resources_from_source=True,
        #         sync_assessments_from_source=True
        #     ),
        #     Classroom(
        #         name="2025春·机器学习进阶班",
        #         source_course_id=course_ml.id,
        #         teacher_id=2,
        #         credit=3,
        #         start_date=now + timedelta(days=45),
        #         end_date=now + timedelta(days=165),
        #         academic_year="2024-2025",
        #         semester="春季",
        #         status=ClassroomStatusEnum.NOT_STARTED,
        #         student_count=0,
        #         sync_resources_from_source=True,
        #         sync_assessments_from_source=False
        #     ),
        #     Classroom(
        #         name="2025春·深度学习研究班",
        #         source_course_id=course_dl.id,
        #         teacher_id=3,
        #         credit=5,
        #         start_date=now + timedelta(days=60),
        #         end_date=now + timedelta(days=180),
        #         academic_year="2024-2025",
        #         semester="春季",
        #         status=ClassroomStatusEnum.NOT_STARTED,
        #         student_count=0,
        #         sync_resources_from_source=True,
        #         sync_assessments_from_source=True
        #     )
        # ]
        
        # for classroom in classrooms:
        #     existing = db.query(Classroom).filter(
        #         Classroom.name == classroom.name,
        #         Classroom.teacher_id == classroom.teacher_id
        #     ).first()
        #     if not existing:
        #         db.add(classroom)
        
        # db.commit()
        
        classrooms = []  # 暂时为空
        
        print("✅ 测试数据初始化完成！")
        print(f"📚 创建了 {len(courses)} 个课程")
        print(f"📖 创建了 {len(chapters)} 个章节")
        print(f"📁 创建了 {len(resources)} 个教学资源")
        print(f"📝 创建了 {len(assessments)} 个课程考核")
        print(f"🔬 创建了 {len(practices)} 个微型实验")
        print(f"🏫 创建了 {len(classrooms)} 个课堂（暂时跳过）")
        print(f"👨‍🏫 创建了 {len(teachers)} 个教师用户")
        
    except Exception as e:
        print(f"❌ 数据初始化失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 开始初始化课程实践测试数据...")
    init_test_data() 