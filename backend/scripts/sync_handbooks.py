#!/usr/bin/env python3
"""
同步实训手册内容到数据库
将 ziyuan_data/实训资源/*/handbook.md 的内容更新到 trainings 表的 handbook_content 字段
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "backend" / "huixue_local.db"
RESOURCE_DIR = BASE_DIR / "ziyuan_data" / "实训资源"

# project_path 到目录名的映射
TRAINING_DIRS = {
    "01-某零售企业经营分析": "01-某零售企业经营分析",
    "02-分布式光伏出力预测": "02-分布式光伏出力预测",
    "03-风电齿轮箱预警分析": "03-风电齿轮箱预警分析",
    "04-公募基金精准营销案例": "04-公募基金精准营销案例",
    "05-某高校校情管理分析案例": "05-某高校校情管理分析案例",
    "06-企业用能环保监测分析": "06-企业用能环保监测分析",
    "07-某公司人力薪酬分析": "07-某公司人力薪酬分析",
    "08-某公司财务报表分析案例": "08-某公司财务报表分析案例",
    "09-某电商货品销售分析案例": "09-某电商货品销售分析案例",
    "10-某公司应收账款分析案例": "10-某公司应收账款分析案例",
}


def sync_handbooks():
    """同步所有handbook内容到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated_count = 0
    errors = []

    for project_path, dir_name in TRAINING_DIRS.items():
        handbook_path = RESOURCE_DIR / dir_name / "handbook.md"

        if not handbook_path.exists():
            errors.append(f"文件不存在: {handbook_path}")
            continue

        # 读取handbook内容
        try:
            with open(handbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            errors.append(f"读取失败 {handbook_path}: {e}")
            continue

        # 更新数据库
        try:
            cursor.execute("""
                UPDATE trainings
                SET handbook_content = ?,
                    updated_at = ?
                WHERE project_path = ?
            """, (content, datetime.now().isoformat(), project_path))

            if cursor.rowcount > 0:
                updated_count += 1
                print(f"✓ 更新成功: {project_path}")
            else:
                errors.append(f"未找到记录: {project_path}")
        except Exception as e:
            errors.append(f"更新失败 {project_path}: {e}")

    conn.commit()
    conn.close()

    print(f"\n=== 同步完成 ===")
    print(f"成功更新: {updated_count} 条")
    if errors:
        print(f"错误数量: {len(errors)}")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    sync_handbooks()
