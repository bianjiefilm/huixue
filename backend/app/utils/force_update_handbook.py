from sqlalchemy import text
from app.core.database import engine
import os

def fix_and_update():
    print("开始执行强制修复...")
    try:
        with engine.connect() as conn:
            # 1. 修复脏数据 (Enum 大小写问题)
            print("正在修复枚举值大小写...")
            conn.execute(text("UPDATE trainings SET difficulty = 'beginner' WHERE difficulty = 'BEGINNER'"))
            conn.execute(text("UPDATE trainings SET difficulty = 'intermediate' WHERE difficulty = 'INTERMEDIATE'"))
            conn.execute(text("UPDATE trainings SET difficulty = 'advanced' WHERE difficulty = 'ADVANCED'"))
            
            # 2. 读取手册内容
            handbook_path = "ziyuan/实训资源/02-公募基金精准营销案例/handbook.md"
            print(f"读取手册文件: {handbook_path}")
            if os.path.exists(handbook_path):
                with open(handbook_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 3. 更新目标实训记录
                print("正在更新实训介绍(Intro)...")
                query = text("UPDATE trainings SET intro = :intro, difficulty = 'beginner' WHERE title = :title")
                result = conn.execute(query, {"intro": content, "title": "02-公募基金精准营销案例"})
                print(f"更新影响行数: {result.rowcount}")
                
                conn.commit()
                print("修复并更新成功！")
            else:
                print(f"错误: 找不到文件 {handbook_path}")
                
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    fix_and_update()

