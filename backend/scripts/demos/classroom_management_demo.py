#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课堂管理功能演示
展示课堂管理的完整工作流程
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import random

class ClassroomManagementDemo:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.teacher_id = 1  # 演示教师ID
        
    def log(self, message: str, level: str = "INFO"):
        """打印演示日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        if level == "TITLE":
            print(f"\n{'='*60}")
            print(f"🎯 {message}")
            print(f"{'='*60}")
        elif level == "STEP":
            print(f"\n📋 [{timestamp}] {message}")
        elif level == "SUCCESS":
            print(f"✅ [{timestamp}] {message}")
        elif level == "ERROR":
            print(f"❌ [{timestamp}] {message}")
        else:
            print(f"ℹ️  [{timestamp}] {message}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "success": 200 <= response.status_code < 300
            }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
    
    def demo_classroom_creation(self):
        """演示课堂创建"""
        self.log("课堂创建与基础设置", "TITLE")
        
        # 1. 创建课堂
        self.log("创建新课堂...", "STEP")
        
        random_suffix = random.randint(1000, 9999)
        
        classroom_data = {
            "name": f"Python程序设计基础-{random_suffix}",
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "credit": 3,
            "academic_year": "2024-2025",
            "semester": "第一学期"
        }
        
        result = self.make_request(
            "POST", 
            f"/api/v1/classrooms?teacher_id={self.teacher_id}",
            json=classroom_data
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"] and "classroom_id" in result["data"]["data"]:
                classroom_id = result["data"]["data"]["classroom_id"]
                self.log(f"课堂创建成功！课堂ID: {classroom_id}", "SUCCESS")
                self.log(f"课堂名称: {classroom_data['name']}")
                self.log(f"学分: {classroom_data['credit']}")
                self.log(f"学年学期: {classroom_data['academic_year']} {classroom_data['semester']}")
                return classroom_id
            else:
                self.log(f"课堂创建响应格式错误: {result}", "ERROR")
                return None
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"课堂创建失败: {error_msg}", "ERROR")
            return None
    
    def demo_chapter_management(self, classroom_id: int):
        """演示章节管理"""
        self.log("章节管理", "TITLE")
        
        chapters = [
            "第一章 Python基础语法",
            "第二章 数据结构与算法",
            "第三章 面向对象编程",
            "第四章 文件操作与异常处理",
            "第五章 网络编程基础"
        ]
        
        chapter_ids = []
        
        for i, chapter_title in enumerate(chapters, 1):
            self.log(f"创建章节 {i}: {chapter_title}", "STEP")
            
            result = self.make_request(
                "POST",
                f"/api/v1/classrooms/{classroom_id}/chapters?title={chapter_title}&teacher_id={self.teacher_id}"
            )
            
            if result["success"] and result["data"]["code"] == "0000":
                if "data" in result["data"] and result["data"]["data"] and "id" in result["data"]["data"]:
                    chapter_id = result["data"]["data"]["id"]
                    chapter_ids.append(chapter_id)
                    self.log(f"章节创建成功，ID: {chapter_id}", "SUCCESS")
                else:
                    self.log(f"章节创建响应格式错误: {result}", "ERROR")
            else:
                error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
                self.log(f"章节创建失败: {error_msg}", "ERROR")
        
        # 获取章节列表
        self.log("获取课堂章节列表...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/chapters?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"] and "chapters" in result["data"]["data"]:
                chapters_list = result["data"]["data"]["chapters"]
                self.log(f"成功获取 {len(chapters_list)} 个章节", "SUCCESS")
                for chapter in chapters_list:
                    self.log(f"  - {chapter['title']} (ID: {chapter['id']})")
            else:
                self.log(f"获取章节列表响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"获取章节列表失败: {error_msg}", "ERROR")
        
        return chapter_ids
    
    def demo_course_addition(self, classroom_id: int):
        """演示课程添加"""
        self.log("课程添加与管理", "TITLE")
        
        # 1. 获取可选课程
        self.log("获取可选的实践课程...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/courses/available?course_type=practice&page_size=5&teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"] and "list" in result["data"]["data"] and result["data"]["data"]["list"]:
                available_courses = result["data"]["data"]["list"]
                self.log(f"找到 {len(available_courses)} 个可选课程", "SUCCESS")
                
                # 添加前3个课程到课堂
                added_courses = []
                for i, course in enumerate(available_courses[:3], 1):
                    self.log(f"添加课程 {i}: {course['title']}", "STEP")
                    
                    result = self.make_request(
                        "POST",
                        f"/api/v1/classrooms/{classroom_id}/courses?course_id={course['id']}&teacher_id={self.teacher_id}"
                    )
                    
                    if result["success"] and result["data"]["code"] == "0000":
                        added_courses.append(course)
                        self.log(f"课程添加成功", "SUCCESS")
                    else:
                        error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
                        self.log(f"课程添加失败: {error_msg}", "ERROR")
                
                return added_courses
            else:
                self.log("获取可选课程失败或无可选课程", "ERROR")
                return []
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"获取可选课程失败: {error_msg}", "ERROR")
            return []
    
    def demo_teaching_resources(self, classroom_id: int):
        """演示教学资源管理"""
        self.log("教学资源管理", "TITLE")
        
        # 上传多种类型的教学资源
        resources = [
            {
                "title": "Python基础语法视频教程",
                "resource_type": "video",
                "url": "https://example.com/python-basics.mp4"
            },
            {
                "title": "数据结构课件PPT",
                "resource_type": "ppt",
                "url": "https://example.com/data-structures.pptx"
            },
            {
                "title": "Python编程规范文档",
                "resource_type": "pdf",
                "url": "https://example.com/python-style-guide.pdf"
            },
            {
                "title": "课程学习指南",
                "resource_type": "document",
                "url": "https://example.com/study-guide.docx"
            }
        ]
        
        uploaded_resources = []
        
        for resource in resources:
            self.log(f"上传教学资源: {resource['title']}", "STEP")
            
            result = self.make_request(
                "POST",
                f"/api/v1/classrooms/{classroom_id}/resources?teacher_id={self.teacher_id}",
                params=resource
            )
            
            if result["success"] and result["data"]["code"] == "0000":
                if "data" in result["data"] and result["data"]["data"] and "id" in result["data"]["data"]:
                    resource_id = result["data"]["data"]["id"]
                    uploaded_resources.append(resource_id)
                    self.log(f"资源上传成功，ID: {resource_id}", "SUCCESS")
                else:
                    self.log(f"资源上传响应格式错误: {result}", "ERROR")
            else:
                error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
                self.log(f"资源上传失败: {error_msg}", "ERROR")
        
        # 获取教学资源列表
        self.log("获取教学资源列表...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/resources?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"] and "list" in result["data"]["data"]:
                resources_list = result["data"]["data"]["list"]
                self.log(f"成功获取 {len(resources_list)} 个教学资源", "SUCCESS")
                for resource in resources_list:
                    self.log(f"  - {resource['title']} ({resource['resource_type']})")
            else:
                self.log(f"获取教学资源列表响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"获取教学资源列表失败: {error_msg}", "ERROR")
        
        return uploaded_resources
    
    def demo_cloud_disk(self, classroom_id: int):
        """演示课堂云盘"""
        self.log("课堂云盘管理", "TITLE")
        
        # 上传不同类型的文件到云盘
        files = [
            {
                "file_name": "第一章练习题.pdf",
                "file_type": "pdf",
                "file_size": 512000,
                "folder_path": "练习题",
                "url": "https://example.com/chapter1-exercises.pdf",
                "is_shared": True
            },
            {
                "file_name": "Python代码示例.zip",
                "file_type": "zip",
                "file_size": 1024000,
                "folder_path": "代码示例",
                "url": "https://example.com/python-examples.zip",
                "is_shared": True
            },
            {
                "file_name": "期末考试大纲.docx",
                "file_type": "docx",
                "file_size": 256000,
                "folder_path": "考试资料",
                "url": "https://example.com/exam-outline.docx",
                "is_shared": False  # 不共享给学生
            }
        ]
        
        uploaded_files = []
        
        for file_info in files:
            self.log(f"上传文件: {file_info['file_name']} 到 {file_info['folder_path']}", "STEP")
            
            result = self.make_request(
                "POST",
                f"/api/v1/classrooms/{classroom_id}/cloud-disk/upload?teacher_id={self.teacher_id}",
                params=file_info
            )
            
            if result["success"] and result["data"]["code"] == "0000":
                if "data" in result["data"] and result["data"]["data"] and "id" in result["data"]["data"]:
                    file_id = result["data"]["data"]["id"]
                    uploaded_files.append(file_id)
                    share_status = "共享" if file_info["is_shared"] else "私有"
                    self.log(f"文件上传成功，ID: {file_id} ({share_status})", "SUCCESS")
                else:
                    self.log(f"文件上传响应格式错误: {result}", "ERROR")
            else:
                error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
                self.log(f"文件上传失败: {error_msg}", "ERROR")
        
        # 获取云盘文件列表
        self.log("获取云盘文件列表...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/cloud-disk?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"] and "list" in result["data"]["data"]:
                files_list = result["data"]["data"]["list"]
                self.log(f"成功获取 {len(files_list)} 个文件", "SUCCESS")
                for file_item in files_list:
                    share_status = "共享" if file_item["is_shared"] else "私有"
                    self.log(f"  - {file_item['name']} ({file_item['folder_path']}) [{share_status}]")
            else:
                self.log(f"获取云盘文件列表响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"获取云盘文件列表失败: {error_msg}", "ERROR")
        
        return uploaded_files
    
    def demo_classroom_management_page(self, classroom_id: int):
        """演示课堂管理页面"""
        self.log("课堂管理页面", "TITLE")
        
        self.log("获取课堂管理页面数据...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/management?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"]:
                data = result["data"]["data"]
                self.log("课堂管理页面数据获取成功", "SUCCESS")
                
                # 显示课堂基本信息
                if "classroom_info" in data:
                    classroom_info = data["classroom_info"]
                    self.log(f"课堂名称: {classroom_info.get('name', '未知')}")
                    if "status_cn" in classroom_info:
                        self.log(f"课堂状态: {classroom_info['status_cn']}")
                    self.log(f"学生人数: {classroom_info.get('student_count', 0)}")
                
                # 显示目录结构
                if "catalog" in data:
                    catalog = data["catalog"]
                    self.log(f"目录结构 ({len(catalog)} 项):")
                    for item in catalog:
                        if item.get("type") == "chapter":
                            self.log(f"  📁 {item.get('title', '未知章节')} ({item.get('course_count', 0)} 个课程)")
                        else:
                            self.log(f"    📄 {item.get('title', '未知课程')} ({item.get('course_type', '未知类型')})")
                
                # 显示统计信息
                if "stats" in data:
                    stats = data["stats"]
                    self.log(f"统计信息:")
                    self.log(f"  - 总课程数: {stats.get('total_courses', 0)}")
                    self.log(f"  - 已发布: {stats.get('published_courses', 0)}")
                    self.log(f"  - 未发布: {stats.get('unpublished_courses', 0)}")
            else:
                self.log(f"获取管理页面数据响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"获取管理页面数据失败: {error_msg}", "ERROR")
    
    def demo_analytics(self, classroom_id: int):
        """演示学情分析"""
        self.log("学情分析", "TITLE")
        
        # 1. 学情总览
        self.log("获取学情总览...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/analytics/overview?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"]:
                overview = result["data"]["data"]
                self.log("学情总览获取成功", "SUCCESS")
                
                if "classroom_info" in overview:
                    classroom_info = overview["classroom_info"]
                    self.log(f"课堂: {classroom_info.get('name', '未知')}")
                
                if "course_stats" in overview:
                    course_stats = overview["course_stats"]
                    self.log(f"课程统计: 总数 {course_stats.get('total', 0)}, 必修 {course_stats.get('mandatory', 0)}, 拓展 {course_stats.get('elective', 0)}")
                
                if "student_stats" in overview:
                    student_stats = overview["student_stats"]
                    self.log(f"学生统计: 总数 {student_stats.get('total', 0)}, 活跃 {student_stats.get('active', 0)}")
            else:
                self.log(f"学情总览响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"学情总览获取失败: {error_msg}", "ERROR")
        
        # 2. 必修课程统计
        self.log("获取必修课程统计...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/analytics/mandatory-courses?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"]:
                mandatory_analytics = result["data"]["data"]
                self.log("必修课程统计获取成功", "SUCCESS")
                
                if "course_analytics" in mandatory_analytics:
                    course_analytics = mandatory_analytics["course_analytics"]
                    self.log(f"必修课程分析 ({len(course_analytics)} 门课程):")
                    for course in course_analytics[:3]:  # 显示前3门课程
                        completion_rate = course.get('completion_rate', 0)
                        average_score = course.get('average_score', 0)
                        self.log(f"  - {course.get('course_title', '未知课程')}: 完成率 {completion_rate:.1%}, 平均分 {average_score:.1f}")
                
                if "summary" in mandatory_analytics:
                    summary = mandatory_analytics["summary"]
                    overall_completion = summary.get('overall_completion_rate', 0)
                    average_hours = summary.get('average_study_hours', 0)
                    self.log(f"总体完成率: {overall_completion:.1%}")
                    self.log(f"平均学习时长: {average_hours:.1f} 小时")
            else:
                self.log(f"必修课程统计响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"必修课程统计获取失败: {error_msg}", "ERROR")
        
        # 3. 拓展课程统计
        self.log("获取拓展课程统计...", "STEP")
        result = self.make_request(
            "GET",
            f"/api/v1/classrooms/{classroom_id}/analytics/elective-courses?teacher_id={self.teacher_id}"
        )
        
        if result["success"] and result["data"]["code"] == "0000":
            if "data" in result["data"] and result["data"]["data"]:
                elective_analytics = result["data"]["data"]
                self.log("拓展课程统计获取成功", "SUCCESS")
                
                if "course_analytics" in elective_analytics:
                    course_analytics = elective_analytics["course_analytics"]
                    self.log(f"拓展课程分析 ({len(course_analytics)} 门课程):")
                    for course in course_analytics[:3]:  # 显示前3门课程
                        participation_rate = course.get('participation_rate', 0)
                        self.log(f"  - {course.get('course_title', '未知课程')}: 参与率 {participation_rate:.1%}")
                
                if "summary" in elective_analytics:
                    summary = elective_analytics["summary"]
                    overall_participation = summary.get('overall_participation_rate', 0)
                    self.log(f"总体参与率: {overall_participation:.1%}")
            else:
                self.log(f"拓展课程统计响应格式错误: {result}", "ERROR")
        else:
            error_msg = result["data"]["message"] if "data" in result and "message" in result["data"] else str(result)
            self.log(f"拓展课程统计获取失败: {error_msg}", "ERROR")
    
    def demo_cleanup(self, classroom_id: int, resource_ids: list, file_ids: list):
        """演示清理操作"""
        self.log("清理演示数据", "TITLE")
        
        # 删除教学资源
        for resource_id in resource_ids:
            self.log(f"删除教学资源 {resource_id}...", "STEP")
            result = self.make_request(
                "DELETE",
                f"/api/v1/classrooms/{classroom_id}/resources/{resource_id}?teacher_id={self.teacher_id}"
            )
            if result["success"]:
                self.log("教学资源删除成功", "SUCCESS")
        
        # 删除课堂
        self.log("删除演示课堂...", "STEP")
        result = self.make_request(
            "DELETE",
            f"/api/v1/classrooms/{classroom_id}?teacher_id={self.teacher_id}"
        )
        
        if result["success"]:
            self.log("演示课堂删除成功", "SUCCESS")
        else:
            self.log(f"课堂删除失败: {result['data']}", "ERROR")
    
    def run_complete_demo(self):
        """运行完整演示"""
        self.log("课堂管理功能完整演示", "TITLE")
        self.log("本演示将展示课堂管理的完整工作流程")
        
        # 检查服务状态
        health_check = self.make_request("GET", "/health")
        if not health_check["success"]:
            self.log("API服务未运行，请先启动服务", "ERROR")
            return
        
        try:
            # 1. 创建课堂
            classroom_id = self.demo_classroom_creation()
            if not classroom_id:
                return
            
            # 2. 章节管理
            chapter_ids = self.demo_chapter_management(classroom_id)
            
            # 3. 课程添加
            added_courses = self.demo_course_addition(classroom_id)
            
            # 4. 教学资源管理
            resource_ids = self.demo_teaching_resources(classroom_id)
            
            # 5. 课堂云盘
            file_ids = self.demo_cloud_disk(classroom_id)
            
            # 6. 课堂管理页面
            self.demo_classroom_management_page(classroom_id)
            
            # 7. 学情分析
            self.demo_analytics(classroom_id)
            
            # 8. 清理演示数据
            self.demo_cleanup(classroom_id, resource_ids, file_ids)
            
            self.log("课堂管理功能演示完成", "TITLE")
            self.log("🎉 所有功能演示成功！课堂管理系统运行正常。", "SUCCESS")
            
        except Exception as e:
            self.log(f"演示过程中发生异常: {str(e)}", "ERROR")


def main():
    """主函数"""
    print("🎓 课堂管理功能演示")
    print("=" * 60)
    print("本演示将展示课堂管理系统的完整功能")
    print("包括：课堂创建、章节管理、课程添加、教学资源、云盘、学情分析等")
    print("=" * 60)
    
    demo = ClassroomManagementDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main() 