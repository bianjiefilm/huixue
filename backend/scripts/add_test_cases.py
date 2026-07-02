#!/usr/bin/env python3
"""
添加测试用例到任务中
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Task, TaskTest
from sqlalchemy.orm import Session


def add_test_cases():
    """为现有任务添加测试用例"""
    db = SessionLocal()
    
    try:
        # 获取所有任务
        tasks = db.query(Task).all()
        
        for task in tasks:
            print(f"=== 为任务添加测试用例: {task.title} (ID: {task.id}) ===")
            
            # 检查是否已有测试用例
            existing_tests = db.query(TaskTest).filter(TaskTest.task_id == task.id).all()
            if existing_tests:
                print(f"⏭️  任务 {task.id} 已有测试用例，跳过")
                continue
            
            # 根据任务类型添加不同的测试用例
            test_cases = []
            
            if "NumPy" in task.title:
                test_cases = [
                    {
                        "input_data": "import numpy as np\narr = np.array([1, 2, 3, 4, 5])",
                        "expected_output": "[1 2 3 4 5]",
                        "is_hidden": False
                    },
                    {
                        "input_data": "arr.shape",
                        "expected_output": "(5,)",
                        "is_hidden": False
                    },
                    {
                        "input_data": "np.sum(arr)",
                        "expected_output": "15",
                        "is_hidden": True
                    }
                ]
            elif "Pandas" in task.title:
                test_cases = [
                    {
                        "input_data": "import pandas as pd\ndf = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})",
                        "expected_output": "   A  B\n0  1  4\n1  2  5\n2  3  6",
                        "is_hidden": False
                    },
                    {
                        "input_data": "df.shape",
                        "expected_output": "(3, 2)",
                        "is_hidden": False
                    },
                    {
                        "input_data": "df['A'].sum()",
                        "expected_output": "6",
                        "is_hidden": True
                    }
                ]
            elif "Hadoop" in task.title:
                if "环境" in task.title:
                    test_cases = [
                        {
                            "input_data": "hadoop version",
                            "expected_output": "Hadoop 3.3.4",
                            "is_hidden": False
                        },
                        {
                            "input_data": "jps",
                            "expected_output": "NameNode\nDataNode\nSecondaryNameNode",
                            "is_hidden": False
                        }
                    ]
                elif "HDFS" in task.title:
                    test_cases = [
                        {
                            "input_data": "hdfs dfs -ls /",
                            "expected_output": "Found 3 items\ndrwxr-xr-x   - root supergroup          0 /tmp\ndrwxr-xr-x   - root supergroup          0 /user\ndrwxr-xr-x   - root supergroup          0 /var",
                            "is_hidden": False
                        },
                        {
                            "input_data": "hdfs dfs -mkdir /test",
                            "expected_output": "",
                            "is_hidden": False
                        }
                    ]
                else:  # MapReduce
                    test_cases = [
                        {
                            "input_data": "hadoop jar examples.jar wordcount input output",
                            "expected_output": "Job completed successfully",
                            "is_hidden": False
                        }
                    ]
            else:
                # 通用测试用例
                test_cases = [
                    {
                        "input_data": "print('Hello World')",
                        "expected_output": "Hello World",
                        "is_hidden": False
                    },
                    {
                        "input_data": "2 + 2",
                        "expected_output": "4",
                        "is_hidden": False
                    },
                    {
                        "input_data": "len('test')",
                        "expected_output": "4",
                        "is_hidden": True
                    }
                ]
            
            # 添加测试用例到数据库
            for i, test_case in enumerate(test_cases, 1):
                db_test_case = TaskTest(
                    task_id=task.id,
                    input_data=test_case["input_data"],
                    expected_output=test_case["expected_output"],
                    is_hidden=test_case["is_hidden"],
                    order_index=i
                )
                db.add(db_test_case)
                print(f"✅ 添加测试用例 {i}: {'隐藏' if test_case['is_hidden'] else '公开'}")
            
            print(f"✅ 成功为任务 {task.id} 添加了 {len(test_cases)} 个测试用例\n")
        
        # 提交所有更改
        db.commit()
        print("🎉 所有测试用例添加完成！")
        
    except Exception as e:
        print(f"❌ 添加测试用例时发生错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_test_cases()