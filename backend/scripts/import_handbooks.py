#!/usr/bin/env python3
"""
导入实训手册内容到数据库
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

# 数据库连接
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://huixue:huixue123@localhost:5432/huixue")

# 实训ID与手册文件的映射
TRAINING_HANDBOOKS = {
    5: "/app/ziyuan_data/实训资源/01-某零售企业经营分析/handbook.md",
    6: "/app/ziyuan_data/实训资源/11-轮胎质量相关性分析/handbook.md",
    7: "/app/ziyuan_data/实训资源/12-设备重过载精准预测/handbook.md",
    8: "/app/ziyuan_data/实训资源/03-风电齿轮箱预警分析/handbook.md",
}

def main():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        for training_id, handbook_path in TRAINING_HANDBOOKS.items():
            try:
                # 读取手册内容
                with open(handbook_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 更新数据库
                conn.execute(
                    text("UPDATE trainings SET handbook_content = :content WHERE id = :id"),
                    {"content": content, "id": training_id}
                )
                print(f"✓ Training {training_id}: 导入成功 ({len(content)} 字符)")
            except FileNotFoundError:
                print(f"✗ Training {training_id}: 文件不存在 - {handbook_path}")
            except Exception as e:
                print(f"✗ Training {training_id}: 导入失败 - {e}")

        conn.commit()

    print("\n导入完成!")

if __name__ == "__main__":
    main()
