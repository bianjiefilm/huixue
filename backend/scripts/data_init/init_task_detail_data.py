"""
初始化关卡详情测试数据
包括任务、测试用例、代码快照等
"""

from database import get_db, engine, Base
from sqlalchemy.orm import Session
import models
import json

def init_task_detail_data():
    """初始化关卡详情测试数据"""
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        # 检查是否已有测试数据
        existing_task = db.query(models.Task).filter(models.Task.id == 1001).first()
        if existing_task:
            print("✅ 测试数据已存在，跳过初始化")
            return
        
        print("🔄 开始初始化关卡详情测试数据...")
        
        # 1. 创建测试课程（作为实践容器）
        test_course = models.Course(
            id=501,
            title="Python基础编程实践",
            course_type=models.CourseTypeEnum.PRACTICE,
            description="学习Python基础语法和编程技巧",
            direction="编程语言",
            categories=["Python"],
            difficulty=models.DifficultyEnum.BEGINNER,
            practice_task_count=3
        )
        
        # 检查课程是否已存在
        existing_course = db.query(models.Course).filter(models.Course.id == 501).first()
        if not existing_course:
            db.add(test_course)
            db.commit()
            print("✅ 创建测试课程")
        
        # 2. 创建测试任务 - 使用正确的枚举值
        tasks_data = [
            {
                "id": 1001,
                "title": "Hello World程序",
                "task_type": "PRACTICE",
                "order_in_practice": 1,
                "coin": 20,
                "env_type": "CODING_ONLINE",  # 使用正确的枚举值
                "difficulty": "BEGINNER",     # 使用正确的枚举值
                "skills": ["Python", "基础语法"],
                "handbook_markdown": """# Hello World程序

## 任务描述
编写你的第一个Python程序，输出"Hello, World!"

## 编程要求
1. 使用print函数输出指定内容
2. 输出内容必须完全匹配"Hello, World!"

## 测试说明
程序将通过自动测试验证输出结果是否正确。

## 知识点
- Python基础语法
- print函数的使用
- 字符串输出
""",
                "answer_content_markdown": """# 参考答案

```python
print("Hello, World!")
```

## 解析
这是最简单的Python程序，使用print函数输出字符串。注意字符串需要用引号包围。
""",
                "evaluation_script_path": "/scripts/hello_world_eval.py",
                "evaluation_command": "python student.py",
                "evaluation_timeout_seconds": 20,
                "student_task_file_paths": ["student.py"]
            },
            {
                "id": 1002,
                "title": "变量与计算",
                "task_type": "PRACTICE",
                "order_in_practice": 2,
                "coin": 30,
                "env_type": "CODING_ONLINE",
                "difficulty": "BEGINNER",
                "skills": ["Python", "变量", "运算"],
                "handbook_markdown": """# 变量与计算

## 任务描述
编写程序计算两个数的和并输出结果

## 编程要求
1. 定义两个变量a=10, b=20
2. 计算它们的和
3. 输出结果，格式为"10 + 20 = 30"

## 测试说明
程序将验证输出格式和计算结果的正确性。
""",
                "answer_content_markdown": """# 参考答案

```python
a = 10
b = 20
result = a + b
print(f"{a} + {b} = {result}")
```
""",
                "evaluation_script_path": "/scripts/calc_eval.py",
                "evaluation_command": "python student.py",
                "evaluation_timeout_seconds": 20,
                "student_task_file_paths": ["student.py"]
            },
            {
                "id": 1003,
                "title": "Python基础选择题",
                "task_type": "SINGLE_CHOICE",
                "order_in_practice": 3,
                "coin": 10,
                "env_type": None,  # 选择题不需要环境
                "difficulty": "BEGINNER",
                "skills": ["Python", "理论知识"],
                "handbook_markdown": """# Python基础选择题

## 题目
下列哪个是Python的正确注释语法？

A. // 这是注释
B. /* 这是注释 */
C. # 这是注释
D. <!-- 这是注释 -->

请选择正确答案。
""",
                "answer_content_markdown": """# 参考答案

正确答案是：C

## 解析
Python使用#符号进行单行注释。其他选项分别是：
- A: JavaScript/C++的单行注释
- B: C/Java的多行注释
- D: HTML的注释
""",
                "evaluation_script_path": None,
                "evaluation_command": None,
                "evaluation_timeout_seconds": 20,
                "student_task_file_paths": None,
                "question_data": json.dumps({
                    "question": "下列哪个是Python的正确注释语法？",
                    "options": [
                        "// 这是注释",
                        "/* 这是注释 */", 
                        "# 这是注释",
                        "<!-- 这是注释 -->"
                    ],
                    "correct_answer": "C"
                })
            }
        ]
        
        # 使用原生SQL插入，避免枚举类型问题
        for task_data in tasks_data:
            existing_task = db.query(models.Task).filter(models.Task.id == task_data["id"]).first()
            if not existing_task:
                # 使用原生SQL插入
                from sqlalchemy import text
                sql = text("""
                    INSERT INTO tasks (
                        id, practice_id, title, task_type, order_in_practice, coin, 
                        env_type, difficulty, skills, handbook_markdown, 
                        answer_content_markdown, evaluation_script_path, 
                        evaluation_command, evaluation_timeout_seconds,
                        student_task_file_paths, question_data
                    ) VALUES (
                        :id, :practice_id, :title, :task_type, :order_in_practice, :coin,
                        :env_type, :difficulty, :skills, :handbook_markdown,
                        :answer_content_markdown, :evaluation_script_path,
                        :evaluation_command, :evaluation_timeout_seconds,
                        :student_task_file_paths, :question_data
                    )
                """)
                
                db.execute(sql, {
                    "id": task_data["id"],
                    "practice_id": 501,  # 使用课程ID作为practice_id
                    "title": task_data["title"],
                    "task_type": task_data["task_type"],
                    "order_in_practice": task_data["order_in_practice"],
                    "coin": task_data["coin"],
                    "env_type": task_data["env_type"],
                    "difficulty": task_data["difficulty"],
                    "skills": task_data["skills"],
                    "handbook_markdown": task_data["handbook_markdown"],
                    "answer_content_markdown": task_data["answer_content_markdown"],
                    "evaluation_script_path": task_data["evaluation_script_path"],
                    "evaluation_command": task_data["evaluation_command"],
                    "evaluation_timeout_seconds": task_data["evaluation_timeout_seconds"],
                    "student_task_file_paths": task_data["student_task_file_paths"],
                    "question_data": task_data.get("question_data")
                })
                print(f"✅ 创建任务: {task_data['title']}")
        
        db.commit()
        
        # 3. 创建测试用例
        test_cases_data = [
            # Hello World任务的测试用例
            {
                "task_id": 1001,
                "input_data": "",
                "expected_output": "Hello, World!",
                "is_hidden": False,
                "order_index": 1
            },
            {
                "task_id": 1001,
                "input_data": "",
                "expected_output": "Hello, World!",
                "is_hidden": True,  # 隐藏测试用例
                "order_index": 2
            },
            # 变量与计算任务的测试用例
            {
                "task_id": 1002,
                "input_data": "",
                "expected_output": "10 + 20 = 30",
                "is_hidden": False,
                "order_index": 1
            },
            {
                "task_id": 1002,
                "input_data": "",
                "expected_output": "10 + 20 = 30",
                "is_hidden": True,
                "order_index": 2
            }
        ]
        
        for test_case_data in test_cases_data:
            existing_test = db.query(models.TaskTest).filter(
                models.TaskTest.task_id == test_case_data["task_id"],
                models.TaskTest.order_index == test_case_data["order_index"]
            ).first()
            
            if not existing_test:
                test_case = models.TaskTest(**test_case_data)
                db.add(test_case)
                print(f"✅ 创建测试用例: 任务{test_case_data['task_id']}-{test_case_data['order_index']}")
        
        db.commit()
        
        # 4. 创建测试用户（如果不存在）
        test_user = db.query(models.User).filter(models.User.username == "student1").first()
        if not test_user:
            test_user = models.User(
                username="student1",
                email="student1@example.com",
                full_name="测试学生1"
            )
            db.add(test_user)
            db.commit()
            print("✅ 创建测试用户")
        
        print("🎉 关卡详情测试数据初始化完成！")
        print("\n📋 测试数据概览:")
        print("- 课程: Python基础编程实践 (ID: 501)")
        print("- 任务1: Hello World程序 (ID: 1001)")
        print("- 任务2: 变量与计算 (ID: 1002)")
        print("- 任务3: Python基础选择题 (ID: 1003)")
        print("- 测试用户: student1")
        print("\n🔗 可以测试的API:")
        print("- GET /api/v1/tasks/1001 - 获取关卡详情")
        print("- GET /api/v1/tasks/1001/tests - 获取测试集")
        print("- POST /api/v1/tasks/1001/evaluate - 提交评测")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_task_detail_data() 