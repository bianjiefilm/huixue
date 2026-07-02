#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查当前注册的路由
"""

from main import app

def check_routes():
    print("🔍 检查当前注册的路由...")
    print("=" * 50)
    
    # 获取所有路由
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                'path': route.path,
                'methods': getattr(route, 'methods', [])
            })
    
    # 按路径排序
    routes.sort(key=lambda x: x['path'])
    
    print(f"📊 总共注册了 {len(routes)} 个路由")
    print()
    
    # 查找任务相关路由
    task_routes = [r for r in routes if '/api/v1/tasks' in r['path']]
    print(f"🎯 任务相关路由 ({len(task_routes)} 个):")
    for route in task_routes:
        methods = ', '.join(route['methods']) if route['methods'] else 'ALL'
        print(f"  {methods:10} {route['path']}")
    
    print()
    
    # 查找Session相关路由
    session_routes = [r for r in routes if '/api/v1/sessions' in r['path']]
    print(f"🖥️ Session相关路由 ({len(session_routes)} 个):")
    for route in session_routes:
        methods = ', '.join(route['methods']) if route['methods'] else 'ALL'
        print(f"  {methods:10} {route['path']}")
    
    print()
    
    # 查找其他API路由
    other_api_routes = [r for r in routes if '/api/v1/' in r['path'] and '/api/v1/tasks' not in r['path'] and '/api/v1/sessions' not in r['path']]
    print(f"🔧 其他API路由 ({len(other_api_routes)} 个):")
    for route in other_api_routes:
        methods = ', '.join(route['methods']) if route['methods'] else 'ALL'
        print(f"  {methods:10} {route['path']}")
    
    print()
    print("=" * 50)
    
    # 检查是否缺少关键路由
    expected_task_routes = [
        '/api/v1/tasks/{task_id}',
        '/api/v1/tasks/{task_id}/tests',
        '/api/v1/tasks/{task_id}/evaluate',
        '/api/v1/tasks/{task_id}/snapshots',
        '/api/v1/tasks/{task_id}/answer'
    ]
    
    expected_session_routes = [
        '/api/v1/sessions/{session_id}/close',
        '/api/v1/sessions/{session_id}/heartbeat',
        '/api/v1/sessions/{session_id}/font-size',
        '/api/v1/sessions/{session_id}/reset-code'
    ]
    
    print("🔍 检查关键路由是否存在:")
    
    task_paths = [r['path'] for r in task_routes]
    for expected in expected_task_routes:
        found = any(expected.replace('{task_id}', '{task_id}') in path for path in task_paths)
        status = "✅" if found else "❌"
        print(f"  {status} {expected}")
    
    session_paths = [r['path'] for r in session_routes]
    for expected in expected_session_routes:
        found = any(expected.replace('{session_id}', '{session_id}') in path for path in session_paths)
        status = "✅" if found else "❌"
        print(f"  {status} {expected}")

if __name__ == "__main__":
    check_routes() 