"""
考试流程完整测试脚本
用于测试考试创建、发布、学生答题、教师阅卷的完整流程
"""

import requests
import json
from datetime import datetime, timedelta
import time

# API基础URL
BASE_URL = "http://localhost:8000"

# 测试用户信息
TEACHER_ID = 1  # 教师ID
STUDENT_IDS = [2, 3, 4]  # 学生ID列表
CLASSROOM_ID = 1  # 课堂ID

# 测试数据存储
created_exam_id = None
created_paper_id = None


def print_step(step_name):
    """打印测试步骤"""
    print(f"\n{'='*50}")
    print(f"测试步骤: {step_name}")
    print(f"{'='*50}")


def check_response(response, step_name):
    """检查响应是否成功"""
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == '0000':
            print(f"✅ {step_name} 成功")
            return data.get('data')
        else:
            print(f"❌ {step_name} 失败: {data.get('message')}")
            return None
    else:
        print(f"❌ {step_name} 失败: HTTP {response.status_code}")
        print(f"响应内容: {response.text}")
        return None


def test_create_test_paper():
    """Step 1: 创建试卷"""
    print_step("创建试卷")
    
    # 创建试卷数据
    paper_data = {
        "paper_name": f"Python编程基础测试卷_{datetime.now().strftime('%Y%m%d%H%M')}",
        "paper_description": "测试Python基础知识掌握情况",
        "total_score": 100,
        "pass_score": 60,
        "time_limit_minutes": 90,
        "questions": [
            {
                "question_type": "single",
                "question_content": "Python中用于定义函数的关键字是？",
                "question_score": 10,
                "options": [
                    {"option_label": "A", "option_content": "function", "is_correct": False},
                    {"option_label": "B", "option_content": "def", "is_correct": True},
                    {"option_label": "C", "option_content": "func", "is_correct": False},
                    {"option_label": "D", "option_content": "define", "is_correct": False}
                ]
            },
            {
                "question_type": "multiple",
                "question_content": "以下哪些是Python的内置数据类型？",
                "question_score": 15,
                "options": [
                    {"option_label": "A", "option_content": "list", "is_correct": True},
                    {"option_label": "B", "option_content": "array", "is_correct": False},
                    {"option_label": "C", "option_content": "dict", "is_correct": True},
                    {"option_label": "D", "option_content": "tuple", "is_correct": True}
                ]
            },
            {
                "question_type": "judge",
                "question_content": "Python是一种编译型语言。",
                "question_score": 10,
                "options": [
                    {"option_label": "对", "option_content": "对", "is_correct": False},
                    {"option_label": "错", "option_content": "错", "is_correct": True}
                ]
            },
            {
                "question_type": "essay",
                "question_content": "请简述Python中列表(list)和元组(tuple)的主要区别。",
                "question_score": 25,
                "question_answer": "列表是可变的，可以修改元素；元组是不可变的，创建后不能修改。"
            },
            {
                "question_type": "essay", 
                "question_content": "编写一个Python函数，实现计算列表中所有数字的平均值。",
                "question_score": 40,
                "question_answer": "def average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"
            }
        ]
    }
    
    # 注意：实际API可能需要调整URL和参数
    # 这里假设有创建试卷的API
    print("注意：试卷创建API可能需要单独实现")
    global created_paper_id
    created_paper_id = 1  # 假设试卷ID为1
    return True


def test_create_exam():
    """Step 2: 创建考试"""
    print_step("创建考试")
    
    url = f"{BASE_URL}/api/v1/classrooms/{CLASSROOM_ID}/exams"
    data = {
        "title": f"Python基础测试_{datetime.now().strftime('%Y%m%d%H%M')}",
        "test_paper_id": created_paper_id
    }
    params = {"teacher_id": TEACHER_ID}
    
    response = requests.post(url, json=data, params=params)
    result = check_response(response, "创建考试")
    
    if result:
        global created_exam_id
        created_exam_id = result.get('exam_id')
        print(f"创建的考试ID: {created_exam_id}")
        return True
    return False


def test_publish_exam():
    """Step 3: 发布考试"""
    print_step("发布考试")
    
    if not created_exam_id:
        print("❌ 无法发布考试：考试ID不存在")
        return False
    
    # 设置考试时间：从现在开始，持续2小时
    start_time = datetime.now() + timedelta(minutes=5)  # 5分钟后开始
    end_time = start_time + timedelta(hours=2)  # 持续2小时
    
    url = f"{BASE_URL}/api/v1/exams/{created_exam_id}/publish"
    data = {
        "exam_start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "exam_end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "duration_minutes": 90,
        "pass_mark": 60,
        "shuffle_questions": False,
        "shuffle_options": False
    }
    params = {"teacher_id": TEACHER_ID}
    
    response = requests.patch(url, json=data, params=params)
    result = check_response(response, "发布考试")
    return result is not None


def test_get_exam_list():
    """Step 4: 获取考试列表"""
    print_step("获取考试列表")
    
    url = f"{BASE_URL}/api/v1/classrooms/{CLASSROOM_ID}/exams"
    params = {
        "teacher_id": TEACHER_ID,
        "page": 1,
        "page_size": 20
    }
    
    response = requests.get(url, params=params)
    result = check_response(response, "获取考试列表")
    
    if result:
        exams = result.get('list', [])
        print(f"找到 {len(exams)} 个考试")
        for exam in exams[:5]:  # 只显示前5个
            print(f"  - {exam.get('exam_name')} (ID: {exam.get('id')}, 状态: {exam.get('is_published')})")
        return True
    return False


def test_simulate_student_answers():
    """Step 5: 模拟学生答题（需要学生端API）"""
    print_step("模拟学生答题")
    
    print("注意：学生答题需要单独的API实现")
    print("这里仅作为占位，实际测试需要：")
    print("  1. 学生登录获取考试")
    print("  2. 开始考试")
    print("  3. 提交答案")
    print("  4. 结束考试")
    
    # 模拟数据，实际需要调用学生答题API
    return True


def test_get_papers_for_marking():
    """Step 6: 获取待阅卷试卷列表"""
    print_step("获取待阅卷试卷")
    
    if not created_exam_id:
        print("❌ 无法获取试卷：考试ID不存在")
        return False
    
    url = f"{BASE_URL}/api/v1/exams/{created_exam_id}/papers"
    params = {
        "teacher_id": TEACHER_ID,
        "unmarked": True  # 只获取未批阅的
    }
    
    response = requests.get(url, params=params)
    result = check_response(response, "获取待阅卷试卷")
    
    if result:
        students = result.get('students', [])
        print(f"待阅卷学生数: {len(students)}")
        return True
    return False


def test_mark_paper():
    """Step 7: 批阅试卷"""
    print_step("批阅学生试卷")
    
    if not created_exam_id:
        print("❌ 无法批阅：考试ID不存在")
        return False
    
    # 假设批阅第一个学生的试卷
    student_id = STUDENT_IDS[0]
    
    # 先获取试卷详情
    url = f"{BASE_URL}/api/v1/exams/{created_exam_id}/papers/{student_id}"
    params = {"teacher_id": TEACHER_ID}
    
    response = requests.get(url, params=params)
    paper_detail = check_response(response, "获取试卷详情")
    
    if not paper_detail:
        print("❌ 无法获取试卷详情")
        return False
    
    # 提交评分
    url = f"{BASE_URL}/api/v1/exams/{created_exam_id}/papers/{student_id}/marks"
    marks_data = {
        "marks": [
            {"question_id": 4, "score": 20, "comment": "回答基本正确，但不够全面"},
            {"question_id": 5, "score": 35, "comment": "代码实现正确，逻辑清晰"}
        ],
        "overall_comments": "整体表现良好，基础知识掌握扎实"
    }
    
    response = requests.post(url, json=marks_data, params=params)
    result = check_response(response, "提交评分")
    return result is not None


def test_get_exam_statistics():
    """Step 8: 获取考试统计"""
    print_step("获取考试统计")
    
    if not created_exam_id:
        print("❌ 无法获取统计：考试ID不存在")
        return False
    
    url = f"{BASE_URL}/api/v1/exams/{created_exam_id}/statistics"
    params = {"teacher_id": TEACHER_ID}
    
    response = requests.get(url, params=params)
    result = check_response(response, "获取考试统计")
    
    if result:
        print(f"总学生数: {result.get('total_students')}")
        print(f"已提交数: {result.get('submitted_count')}")
        print(f"已批阅数: {result.get('graded_count')}")
        print(f"平均分: {result.get('average_score')}")
        return True
    return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始考试流程完整测试")
    print("="*60)
    
    tests = [
        test_create_test_paper,
        test_create_exam,
        test_publish_exam,
        test_get_exam_list,
        test_simulate_student_answers,
        test_get_papers_for_marking,
        test_mark_paper,
        test_get_exam_statistics
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
        
        time.sleep(1)  # 避免请求过快
    
    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()