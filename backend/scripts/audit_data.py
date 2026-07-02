#!/usr/bin/env python3
"""
全站数据对账与防伪体检脚本
检查数据库中记录的课程文件、数据集是否存在"丢失、空壳(0KB)、残缺损坏"的情况
"""
import os
import sys
import json
import sqlite3
import subprocess

# 数据库路径
DB_PATH = '/app/huixue_local.db'

def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def check_file_exists(filepath):
    """检查文件是否存在且非空"""
    if not filepath:
        return {'exists': False, 'size': 0, 'error': 'Empty path'}

    # 规范化路径
    filepath = filepath.strip()

    # 检查是否是绝对路径还是相对路径
    if not filepath.startswith('/'):
        # 相对路径，基于静态资源目录
        filepath = f'/data{filepath}'

    # 检查文件是否存在
    if not os.path.exists(filepath):
        return {'exists': False, 'size': 0, 'error': 'File not found'}

    # 检查文件大小
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return {'exists': True, 'size': 0, 'error': 'Empty file (0KB)'}
        return {'exists': True, 'size': size, 'error': None}
    except Exception as e:
        return {'exists': False, 'size': 0, 'error': str(e)}

def audit_courses(db):
    """审计课程资源文件"""
    print("\n" + "="*60)
    print("📚 审计课程资源文件...")
    print("="*60)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, name, cover_image, description, course_type
        FROM courses
        WHERE is_deleted = 0
        ORDER BY id
    """)

    courses = cursor.fetchall()
    issues = []

    for course in courses:
        course_id, name, cover_image, description, course_type = course
        print(f"  检查课程 {course_id}: {name[:30]}...")

        # 检查封面图片
        if cover_image:
            result = check_file_exists(cover_image)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'course_cover',
                    'course_id': course_id,
                    'course_name': name,
                    'path': cover_image,
                    'issue': result['error'] or 'File not found'
                })

    return issues

def audit_course_resources(db):
    """审计课程资源表"""
    print("\n" + "="*60)
    print("📁 审计 course_resources 表...")
    print("="*60)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, course_id, title, resource_type, file_path, url
        FROM course_resources
        WHERE is_deleted = 0
        ORDER BY id
    """)

    resources = cursor.fetchall()
    issues = []
    total = len(resources)

    print(f"  共 {total} 条资源记录")

    for i, resource in enumerate(resources):
        resource_id, course_id, title, resource_type, file_path, url = resource
        if (i + 1) % 50 == 0:
            print(f"  已检查 {i+1}/{total}...")

        # 检查 file_path
        if file_path:
            result = check_file_exists(file_path)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'resource_file',
                    'resource_id': resource_id,
                    'course_id': course_id,
                    'title': title,
                    'path': file_path,
                    'size': result['size'],
                    'issue': result['error'] or 'File not found'
                })

        # 检查 url
        if url and url.startswith('/'):
            result = check_file_exists(url)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'resource_url',
                    'resource_id': resource_id,
                    'course_id': course_id,
                    'title': title,
                    'path': url,
                    'size': result['size'],
                    'issue': result['error'] or 'File not found'
                })

    return issues

def audit_training_assets(db):
    """审计实训资源文件"""
    print("\n" + "="*60)
    print("🎓 审计实训资源文件...")
    print("="*60)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, training_id, name, file_path, file_type
        FROM training_assets
        ORDER BY id
    """)

    assets = cursor.fetchall()
    issues = []
    total = len(assets)

    print(f"  共 {total} 条实训资源记录")

    for i, asset in enumerate(assets):
        asset_id, training_id, name, file_path, file_type = asset
        if (i + 1) % 50 == 0:
            print(f"  已检查 {i+1}/{total}...")

        if file_path:
            result = check_file_exists(file_path)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'training_asset',
                    'asset_id': asset_id,
                    'training_id': training_id,
                    'name': name,
                    'path': file_path,
                    'size': result['size'],
                    'issue': result['error'] or 'File not found'
                })

    return issues

def audit_training_datasets(db):
    """审计实训数据集"""
    print("\n" + "="*60)
    print("📊 审计实训数据集...")
    print("="*60)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, training_id, name, file_path, file_size
        FROM training_datasets
        ORDER BY id
    """)

    datasets = cursor.fetchall()
    issues = []
    total = len(datasets)

    print(f"  共 {total} 条数据集记录")

    for i, dataset in enumerate(datasets):
        dataset_id, training_id, name, file_path, file_size = dataset
        if (i + 1) % 50 == 0:
            print(f"  已检查 {i+1}/{total}...")

        if file_path:
            result = check_file_exists(file_path)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'training_dataset',
                    'dataset_id': dataset_id,
                    'training_id': training_id,
                    'name': name,
                    'path': file_path,
                    'size': result['size'],
                    'db_size': file_size,
                    'issue': result['error'] or 'File not found'
                })
            elif result['size'] != file_size and file_size:
                # 文件大小不匹配
                issues.append({
                    'type': 'dataset_size_mismatch',
                    'dataset_id': dataset_id,
                    'training_id': training_id,
                    'name': name,
                    'path': file_path,
                    'actual_size': result['size'],
                    'db_size': file_size,
                    'issue': 'Size mismatch'
                })

    return issues

def audit_practices(db):
    """审计实践课程"""
    print("\n" + "="*60)
    print("🔧 审计实践课程...")
    print("="*60)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, title, cover_image, environment_config
        FROM practices
        WHERE is_deleted = 0
        ORDER BY id
    """)

    practices = cursor.fetchall()
    issues = []

    for practice in practices:
        practice_id, title, cover_image, env_config = practice
        print(f"  检查实践 {practice_id}: {title[:30]}...")

        if cover_image:
            result = check_file_exists(cover_image)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'practice_cover',
                    'practice_id': practice_id,
                    'title': title,
                    'path': cover_image,
                    'issue': result['error'] or 'File not found'
                })

    return issues

def audit_handbooks(db):
    """审计实训手册"""
    print("\n" + "="*60)
    print("📖 审计实训手册...")
    print("="*60)

    cursor = db.cursor()
    cursor.execute("""
        SELECT id, training_id, name, file_path
        FROM training_assets
        WHERE file_type = 'handbook' OR file_type = 'pdf'
        ORDER BY id
    """)

    handbooks = cursor.fetchall()
    issues = []

    for handbook in handbooks:
        handbook_id, training_id, name, file_path = handbook
        if file_path:
            result = check_file_exists(file_path)
            if not result['exists'] or result['error']:
                issues.append({
                    'type': 'handbook',
                    'handbook_id': handbook_id,
                    'training_id': training_id,
                    'name': name,
                    'path': file_path,
                    'issue': result['error'] or 'File not found'
                })

    return issues

def generate_report(all_issues):
    """生成体检报告"""
    print("\n" + "="*60)
    print("📋 全站课程文件健康体检报告")
    print("="*60)

    # 统计各类问题
    type_counts = {}
    for issue in all_issues:
        issue_type = issue['type']
        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

    print(f"\n总问题数: {len(all_issues)}")
    print("\n问题分类统计:")
    for issue_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  - {issue_type}: {count} 个")

    # 详细问题列表
    if all_issues:
        print("\n详细问题列表:")
        for i, issue in enumerate(all_issues, 1):
            print(f"\n  [{i}] {issue['type']}")
            if 'course_id' in issue:
                print(f"      课程ID: {issue['course_id']}")
            if 'resource_id' in issue:
                print(f"      资源ID: {issue['resource_id']}")
            if 'training_id' in issue:
                print(f"      实训ID: {issue['training_id']}")
            if 'path' in issue:
                print(f"      路径: {issue['path']}")
            if 'size' in issue and issue['size'] is not None:
                print(f"      文件大小: {issue['size']} bytes")
            print(f"      问题: {issue['issue']}")

    # 保存报告到文件
    report_path = '/tmp/health_audit_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_issues': len(all_issues),
            'type_counts': type_counts,
            'issues': all_issues
        }, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存到: {report_path}")

    return len(all_issues) == 0

def main():
    print("="*60)
    print("🔍 全站数据对账与防伪体检")
    print("="*60)

    # 切换到正确的目录
    os.chdir('/app')

    try:
        db = get_db_connection()
        print(f"✅ 数据库连接成功: {DB_PATH}")

        # 执行各项审计
        all_issues = []

        # 1. 审计课程
        all_issues.extend(audit_courses(db))

        # 2. 审计课程资源
        all_issues.extend(audit_course_resources(db))

        # 3. 审计实训资源
        all_issues.extend(audit_training_assets(db))

        # 4. 审计数据集
        all_issues.extend(audit_training_datasets(db))

        # 5. 审计实践课程
        all_issues.extend(audit_practices(db))

        # 6. 审计手册
        all_issues.extend(audit_handbooks(db))

        # 生成报告
        is_healthy = generate_report(all_issues)

        db.close()

        if is_healthy:
            print("\n✅ 体检通过！所有文件正常！")
            return 0
        else:
            print(f"\n⚠️ 体检发现 {len(all_issues)} 个问题，请检查！")
            return 1

    except Exception as e:
        print(f"❌ 体检失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
