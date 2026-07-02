#!/usr/bin/env python3
"""
环境冲突检测测试脚本
测试场景：学生在有活跃环境时尝试启动新环境
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def login(session: aiohttp.ClientSession, username: str, password: str) -> str:
    """登录获取token"""
    async with session.post(
        f"{BASE_URL}/api/login",
        json={"username": username, "password": password}
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("token", {}).get("access_token", "")
    return ""

async def check_active(session: aiohttp.ClientSession, token: str) -> dict:
    """检查活跃环境"""
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{BASE_URL}/api/v1/environments/active", headers=headers) as resp:
        return await resp.json()

async def launch_env(session: aiohttp.ClientSession, token: str, practice_id: int, env_type: str = "desktop") -> dict:
    """启动环境"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with session.post(
        f"{BASE_URL}/api/v1/environments/launch",
        headers=headers,
        json={"practiceId": practice_id, "environmentType": env_type}
    ) as resp:
        return await resp.json()

async def stop_env(session: aiohttp.ClientSession, token: str, session_id: str) -> dict:
    """停止环境"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with session.post(
        f"{BASE_URL}/api/v1/environments/{session_id}/stop",
        headers=headers,
        json={}
    ) as resp:
        return await resp.json()

async def test_conflict_detection():
    """测试环境冲突检测"""
    print(f"\n{'='*60}")
    print("环境冲突检测测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    async with aiohttp.ClientSession() as session:
        # 使用测试学生01
        username = "test_student_01"
        token = await login(session, username, "password123")
        
        if not token:
            print("❌ 登录失败")
            return
        
        print(f"✓ 登录成功: {username}")
        
        # 测试1: 清理现有环境
        print("\n--- 测试1: 清理现有活跃环境 ---")
        active = await check_active(session, token)
        if active.get("data"):
            session_id = active["data"]["id"]
            print(f"  发现活跃环境: {session_id[:8]}...")
            await stop_env(session, token, session_id)
            print("  ✓ 已停止")
        else:
            print("  无活跃环境")
        
        # 测试2: 启动Shell环境
        print("\n--- 测试2: 启动Shell环境 (practice 22) ---")
        result1 = await launch_env(session, token, 22, "shell")
        if result1.get("code") == "0000":
            shell_session_id = result1["data"]["id"]
            print(f"  ✓ Shell环境启动成功: {shell_session_id[:8]}...")
        else:
            print(f"  ❌ 失败: {result1}")
            return
        
        # 测试3: 检查活跃环境
        print("\n--- 测试3: 检查活跃环境 ---")
        active = await check_active(session, token)
        if active.get("data"):
            print(f"  ✓ 检测到活跃环境: {active['data']['environmentType']}")
            print(f"    Practice ID: {active['data']['practiceId']}")
            print(f"    Practice Name: {active['data'].get('practiceName', 'N/A')}")
        else:
            print("  ❌ 未检测到活跃环境")
        
        # 测试4: 尝试启动VDI环境 (应该检测到冲突)
        print("\n--- 测试4: 尝试启动VDI环境 (应检测到冲突) ---")
        result2 = await launch_env(session, token, 23, "desktop")
        if result2.get("code") == "0000":
            print(f"  ⚠ VDI环境启动成功 (已自动处理冲突)")
            print(f"    新Session ID: {result2['data']['id'][:8]}...")
            vdi_session_id = result2["data"]["id"]
        else:
            print(f"  结果: {result2.get('message', 'Unknown')}")
        
        # 测试5: 验证旧Shell环境已被停止
        print("\n--- 测试5: 验证旧Shell环境状态 ---")
        active = await check_active(session, token)
        if active.get("data"):
            current_type = active["data"]["environmentType"]
            if current_type == "desktop":
                print(f"  ✓ 当前活跃环境已切换为: {current_type}")
            else:
                print(f"  当前活跃环境类型: {current_type}")
        
        # 清理
        print("\n--- 清理测试环境 ---")
        active = await check_active(session, token)
        if active.get("data"):
            await stop_env(session, token, active["data"]["id"])
            print("  ✓ 已清理")
        
        print(f"\n{'='*60}")
        print("冲突检测测试完成!")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_conflict_detection())

