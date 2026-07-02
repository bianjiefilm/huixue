#!/usr/bin/env python3
"""
VDI环境生产级负载测试脚本
模拟50个学生同时访问VDI环境
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import statistics

BASE_URL = "http://localhost:8000"

# 测试结果收集
results = {
    "login": [],
    "check_active": [],
    "launch_env": [],
    "stop_env": [],
    "errors": []
}

async def login(session: aiohttp.ClientSession, username: str, password: str) -> str:
    """登录获取token"""
    start = time.time()
    try:
        async with session.post(
            f"{BASE_URL}/api/login",
            json={"username": username, "password": password}
        ) as resp:
            elapsed = (time.time() - start) * 1000
            results["login"].append(elapsed)
            
            if resp.status == 200:
                data = await resp.json()
                return data.get("token", {}).get("access_token", "")
            else:
                results["errors"].append(f"Login failed for {username}: {resp.status}")
                return ""
    except Exception as e:
        results["errors"].append(f"Login error for {username}: {str(e)}")
        return ""

async def check_active_environment(session: aiohttp.ClientSession, token: str) -> Dict:
    """检查活跃环境"""
    start = time.time()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(
            f"{BASE_URL}/api/v1/environments/active",
            headers=headers
        ) as resp:
            elapsed = (time.time() - start) * 1000
            results["check_active"].append(elapsed)
            return await resp.json()
    except Exception as e:
        results["errors"].append(f"Check active error: {str(e)}")
        return {}

async def launch_environment(session: aiohttp.ClientSession, token: str, practice_id: int) -> Dict:
    """启动VDI环境"""
    start = time.time()
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with session.post(
            f"{BASE_URL}/api/v1/environments/launch",
            headers=headers,
            json={"practiceId": practice_id, "environmentType": "desktop"}
        ) as resp:
            elapsed = (time.time() - start) * 1000
            results["launch_env"].append(elapsed)
            return await resp.json()
    except Exception as e:
        results["errors"].append(f"Launch error: {str(e)}")
        return {}

async def stop_environment(session: aiohttp.ClientSession, token: str, session_id: str) -> Dict:
    """停止环境"""
    start = time.time()
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with session.post(
            f"{BASE_URL}/api/v1/environments/{session_id}/stop",
            headers=headers,
            json={}
        ) as resp:
            elapsed = (time.time() - start) * 1000
            results["stop_env"].append(elapsed)
            return await resp.json()
    except Exception as e:
        results["errors"].append(f"Stop error: {str(e)}")
        return {}

async def simulate_student(student_num: int, practice_id: int = 23):
    """模拟单个学生的完整流程"""
    username = f"test_student_{student_num:02d}"
    password = "password123"
    
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 1. 登录
        token = await login(session, username, password)
        if not token:
            return {"success": False, "error": "Login failed", "student": username}
        
        # 2. 检查活跃环境
        active_result = await check_active_environment(session, token)
        
        # 3. 如果有活跃环境，先停止
        if active_result.get("data"):
            session_id = active_result["data"].get("id")
            if session_id:
                await stop_environment(session, token, session_id)
        
        # 4. 启动新环境
        launch_result = await launch_environment(session, token, practice_id)
        
        # 5. 获取新的session_id并停止（清理）
        if launch_result.get("code") == "0000" and launch_result.get("data"):
            session_id = launch_result["data"].get("id")
            if session_id:
                await asyncio.sleep(0.5)  # 模拟使用
                await stop_environment(session, token, session_id)
        
        return {
            "success": launch_result.get("code") == "0000",
            "student": username,
            "access_url": launch_result.get("data", {}).get("access_url")
        }

async def run_concurrent_test(num_students: int = 50, batch_size: int = 10):
    """运行并发测试"""
    print(f"\n{'='*60}")
    print(f"VDI 生产环境负载测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试学生数: {num_students}")
    print(f"并发批次大小: {batch_size}")
    print(f"{'='*60}\n")
    
    all_results = []
    total_start = time.time()
    
    # 分批执行，避免一次性创建太多连接
    for batch_start in range(1, num_students + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, num_students)
        batch_num = (batch_start - 1) // batch_size + 1
        
        print(f"批次 {batch_num}: 学生 {batch_start}-{batch_end}")
        
        tasks = [simulate_student(i) for i in range(batch_start, batch_end + 1)]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in batch_results if isinstance(r, dict) and r.get("success"))
        print(f"  ✓ 成功: {success_count}/{len(batch_results)}")
        
        all_results.extend(batch_results)
        
        # 批次间短暂间隔
        if batch_end < num_students:
            await asyncio.sleep(0.5)
    
    total_time = time.time() - total_start
    
    # 统计结果
    print(f"\n{'='*60}")
    print("测试结果统计")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in all_results if isinstance(r, dict) and r.get("success"))
    print(f"\n总体成功率: {success_count}/{num_students} ({100*success_count/num_students:.1f}%)")
    print(f"总耗时: {total_time:.2f}秒")
    
    # API响应时间统计
    for api_name, times in results.items():
        if api_name == "errors" or not times:
            continue
        print(f"\n{api_name} API:")
        print(f"  调用次数: {len(times)}")
        print(f"  平均响应: {statistics.mean(times):.1f}ms")
        print(f"  最小响应: {min(times):.1f}ms")
        print(f"  最大响应: {max(times):.1f}ms")
        if len(times) > 1:
            print(f"  标准差: {statistics.stdev(times):.1f}ms")
    
    # 错误统计
    if results["errors"]:
        print(f"\n错误列表 ({len(results['errors'])}个):")
        for err in results["errors"][:10]:  # 只显示前10个
            print(f"  - {err}")
    
    print(f"\n{'='*60}")
    print("测试完成!")
    print(f"{'='*60}\n")
    
    return {
        "total_students": num_students,
        "success_count": success_count,
        "total_time": total_time,
        "api_stats": {k: {"count": len(v), "avg": statistics.mean(v) if v else 0} 
                      for k, v in results.items() if k != "errors"},
        "errors": results["errors"]
    }

if __name__ == "__main__":
    # 运行50学生并发测试
    asyncio.run(run_concurrent_test(num_students=50, batch_size=10))



