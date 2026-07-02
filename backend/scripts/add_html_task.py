#!/usr/bin/env python3
"""
添加一个HTML前端实践任务
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Task, TaskTest, Practice, PracticeSkill
from app.models.models import TaskTypeEnum
from sqlalchemy.orm import Session


def add_html_task():
    """添加HTML前端实践任务"""
    db = SessionLocal()
    
    try:
        # 获取第一个实践（线性回归算法实现）
        practice = db.query(Practice).filter(Practice.id == 2).first()
        if not practice:
            print("❌ 找不到实践ID 2")
            return
        
        # 创建HTML任务
        html_task = Task(
            practice_id=practice.id,
            title="HTML个人简介页面",
            task_type=TaskTypeEnum.PRACTICE,
            order_in_practice=3,  # 作为第3个任务
            coin=40,
            env_type="HTML_PREVIEW",
            difficulty="intermediate",
            skills=json.dumps(["HTML", "CSS", "JavaScript", "响应式设计"]),
            handbook_markdown="""# HTML个人简介页面

## 任务目标
使用HTML、CSS和JavaScript创建一个个人简介页面，包含基本的响应式设计。

## 任务要求
1. 创建一个包含个人信息的HTML页面
2. 使用CSS进行样式设计
3. 实现基本的响应式布局
4. 添加简单的JavaScript交互

## 页面内容要求
- 个人基本信息（姓名、职业、简介）
- 教育背景
- 技能列表
- 兴趣爱好
- 联系方式

## 技术要求
- 使用HTML5语义化标签
- CSS样式使用相对单位（em、rem、%）
- 至少包含一个JavaScript交互功能
- 页面要能在不同宽度下正常显示

## 评分标准
- HTML结构完整且语义化（30分）
- CSS样式美观且响应式（40分）
- JavaScript交互功能正常（30分）
""",
            answer_content_markdown="""```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>个人简介 - 张三</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid #eee;
        }
        
        .profile-img {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            margin: 0 auto 1rem;
            background: #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: #666;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #7f8c8d;
            font-size: 1.2rem;
        }
        
        .section {
            margin: 2rem 0;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 1rem;
            border-left: 4px solid #3498db;
            padding-left: 1rem;
        }
        
        .skills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .skill-tag {
            background: #3498db;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .contact-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .contact-item {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            transition: transform 0.3s ease;
            cursor: pointer;
        }
        
        .contact-item:hover {
            transform: translateY(-5px);
            background: #e9ecef;
        }
        
        .toggle-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 1rem;
            transition: background 0.3s ease;
        }
        
        .toggle-btn:hover {
            background: #2980b9;
        }
        
        .hidden {
            display: none;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 1rem;
                padding: 1rem;
            }
            
            .profile-img {
                width: 100px;
                height: 100px;
                font-size: 2rem;
            }
            
            h1 {
                font-size: 1.5rem;
            }
            
            .contact-info {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="profile-img">👤</div>
            <h1>张三</h1>
            <p class="subtitle">前端开发工程师</p>
        </header>
        
        <section class="section">
            <h2>个人简介</h2>
            <p>我是一名热爱技术的前端开发工程师，拥有3年的Web开发经验。专注于用户体验和界面设计，熟练掌握现代前端技术栈。</p>
        </section>
        
        <section class="section">
            <h2>教育背景</h2>
            <p><strong>计算机科学与技术学士</strong> - 某某大学 (2018-2022)</p>
            <p>主修课程：数据结构、算法设计、Web开发、数据库原理</p>
        </section>
        
        <section class="section">
            <h2>技能专长</h2>
            <div class="skills">
                <span class="skill-tag">HTML5</span>
                <span class="skill-tag">CSS3</span>
                <span class="skill-tag">JavaScript</span>
                <span class="skill-tag">Vue.js</span>
                <span class="skill-tag">React</span>
                <span class="skill-tag">TypeScript</span>
                <span class="skill-tag">Node.js</span>
            </div>
        </section>
        
        <section class="section">
            <h2>兴趣爱好</h2>
            <div id="hobbies">
                <p>阅读技术博客、开源项目贡献、摄影、旅行</p>
            </div>
            <button class="toggle-btn" onclick="toggleHobbies()">显示更多爱好</button>
            <div id="moreHobbies" class="hidden">
                <p>编程、学习新技术、参加技术meetup、写技术文章</p>
            </div>
        </section>
        
        <section class="section">
            <h2>联系方式</h2>
            <div class="contact-info">
                <div class="contact-item" onclick="alert('邮箱: zhangsan@example.com')">
                    <strong>📧 邮箱</strong>
                    <p>点击查看邮箱</p>
                </div>
                <div class="contact-item" onclick="alert('电话: 138-0000-0000')">
                    <strong>📱 电话</strong>
                    <p>点击查看电话</p>
                </div>
                <div class="contact-item" onclick="alert('GitHub: github.com/zhangsan')">
                    <strong>💻 GitHub</strong>
                    <p>点击查看GitHub</p>
                </div>
            </div>
        </section>
    </div>
    
    <script>
        function toggleHobbies() {
            const moreHobbies = document.getElementById('moreHobbies');
            const btn = document.querySelector('.toggle-btn');
            
            if (moreHobbies.classList.contains('hidden')) {
                moreHobbies.classList.remove('hidden');
                btn.textContent = '收起';
            } else {
                moreHobbies.classList.add('hidden');
                btn.textContent = '显示更多爱好';
            }
        }
        
        // 页面加载完成后的欢迎动画
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('.container');
            container.style.opacity = '0';
            container.style.transform = 'translateY(50px)';
            
            setTimeout(() => {
                container.style.transition = 'all 0.8s ease';
                container.style.opacity = '1';
                container.style.transform = 'translateY(0)';
            }, 100);
        });
    </script>
</body>
</html>
```""",
            evaluation_timeout_seconds=30
        )
        
        db.add(html_task)
        db.commit()
        db.refresh(html_task)
        
        print(f"✅ 创建HTML任务成功: {html_task.title} (ID: {html_task.id})")
        
        # 为HTML任务添加测试用例
        test_cases = [
            {
                "input_data": "检查HTML文档结构",
                "expected_output": "包含完整的HTML5文档结构",
                "is_hidden": False
            },
            {
                "input_data": "检查页面内容完整性",
                "expected_output": "包含个人信息、教育背景、技能、兴趣爱好、联系方式",
                "is_hidden": False
            },
            {
                "input_data": "检查响应式设计",
                "expected_output": "页面能在不同宽度下正常显示",
                "is_hidden": False
            },
            {
                "input_data": "检查JavaScript交互",
                "expected_output": "包含可工作的JavaScript交互功能",
                "is_hidden": True
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            db_test_case = TaskTest(
                task_id=html_task.id,
                input_data=test_case["input_data"],
                expected_output=test_case["expected_output"],
                is_hidden=test_case["is_hidden"],
                order_index=i
            )
            db.add(db_test_case)
            print(f"✅ 添加测试用例 {i}: {'隐藏' if test_case['is_hidden'] else '公开'}")
        
        # 为实践添加HTML相关技能
        html_skills = ["HTML", "CSS", "JavaScript", "响应式设计"]
        for skill_name in html_skills:
            # 检查技能是否已存在
            existing_skill = db.query(PracticeSkill).filter(
                PracticeSkill.practice_id == practice.id,
                PracticeSkill.skill_name == skill_name
            ).first()
            
            if not existing_skill:
                skill = PracticeSkill(
                    practice_id=practice.id,
                    skill_name=skill_name
                )
                db.add(skill)
                print(f"✅ 添加技能: {skill_name}")
        
        db.commit()
        print("\n🎉 HTML任务创建完成！")
        
    except Exception as e:
        print(f"❌ 创建HTML任务时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_html_task()