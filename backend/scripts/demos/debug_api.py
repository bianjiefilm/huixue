#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试API响应格式
"""

import requests
import json
from datetime import datetime, timedelta

def test_create_classroom():
    """测试创建课堂API的响应格式"""
    
    classroom_data = {
        "name": "调试测试课堂",
        "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "credit": 3,
        "academic_year": "2024-2025",
        "semester": "第一学期"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/classrooms?teacher_id=1",
            json=classroom_data,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"JSON解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查数据结构
            if "data" in result:
                print(f"data字段内容: {result['data']}")
                print(f"data字段类型: {type(result['data'])}")
                if isinstance(result['data'], dict):
                    print(f"data字段的键: {list(result['data'].keys())}")
        
    except Exception as e:
        print(f"请求异常: {str(e)}")

if __name__ == "__main__":
    test_create_classroom() 