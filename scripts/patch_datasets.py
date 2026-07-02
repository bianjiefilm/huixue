#!/usr/bin/env python3
"""
patch_datasets.py - 精准修复 datasets 挂载问题
"""
import os
import subprocess
import re

DB_CONTAINER = 'huixue-db-test' # 根据之前 ssot_deep_syncer.py，目前是这个。或者 huixue-db
DB_USER = 'huixue'
DB_NAME = 'huixue'
TRAINING_DIR = '/data/huixue_storage/static/ziyuan_data_full/实训资源'

def run_sql(sql):
    cmd = ['docker', 'exec', 'huixue-db-test', 'psql', '-U', DB_USER, '-d', DB_NAME, '-t', '-c', sql]
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0, result.stdout.strip(), result.stderr

def escape_sql(s):
    if s:
        return s.replace("'", "''")
    return ''

def main():
    print("="*50)
    print("开始精准补丁：修复 datasets 挂载")
    print("="*50)
    
    # 获取所有的 training ids and titles
    ok, out, err = run_sql("SELECT id, title FROM trainings;")
    if not ok:
        print(f"获取 trainings 失败: {err}")
        return
        
    trainings = {}
    for line in out.split('\n'):
        if not line.strip(): continue
        parts = line.split('|', 1)
        if len(parts) == 2:
            tid_str = parts[0].strip()
            title = parts[1].strip()
            try:
                tid = int(tid_str)
                trainings[title] = tid
            except ValueError:
                pass
                
    print(f"从数据库获取到 {len(trainings)} 个实训记录")
    if not trainings:
        return

    # 遍历物理目录匹配
    if not os.path.exists(TRAINING_DIR):
        print(f"错误: 目录不存在 {TRAINING_DIR}")
        return
        
    folders = [f for f in os.listdir(TRAINING_DIR) 
              if os.path.isdir(os.path.join(TRAINING_DIR, f)) and not f.startswith('.')]
              
    total_inserted = 0
    for folder in folders:
        folder_path = os.path.join(TRAINING_DIR, folder)
        ds_path = os.path.join(folder_path, 'datasets')
        
        # 尝试使用 metadata 的 title，或者文件夹名
        title_to_match = folder
        meta_path = os.path.join(folder_path, 'metadata.json')
        if os.path.exists(meta_path):
             import json
             try:
                 with open(meta_path, 'r', encoding='utf-8') as f:
                     meta = json.load(f)
                     title_to_match = meta.get('title', folder)
             except:
                 pass
                 
        tid = trainings.get(title_to_match)
        if not tid:
            # 模糊匹配
            for db_title, db_id in trainings.items():
                if db_title in title_to_match or title_to_match in db_title:
                    tid = db_id
                    break
        
        if not tid:
            continue
            
        if os.path.exists(ds_path):
            files = [f for f in os.listdir(ds_path) if os.path.isfile(os.path.join(ds_path, f))]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in ['.csv', '.xlsx', '.json', '.sql', '.txt']:
                    continue
                fp = os.path.join(ds_path, f)
                size = os.path.getsize(fp)
                rel_path = f"trainings/{folder}/datasets/{f}"
                
                # Check if already exists
                check_sql = f"SELECT id FROM training_datasets WHERE training_id = {tid} AND name = '{escape_sql(f)}';"
                ok, check_out, _ = run_sql(check_sql)
                if check_out:
                    continue # 已经有了
                    
                insert_sql = f"""
                INSERT INTO training_datasets (training_id, name, file_path, file_size, file_type, created_at)
                VALUES ({tid}, '{escape_sql(f)}', '{escape_sql(rel_path)}', {size}, '{ext}', NOW())
                ON CONFLICT DO NOTHING;
                """
                ok, _, _ = run_sql(insert_sql)
                if ok:
                    total_inserted += 1
                    print(f"成功挂载: {title_to_match} -> {f}")
                    
    print("\n" + "="*50)                
    ok, count_out, _ = run_sql("SELECT COUNT(*) FROM training_datasets;")
    print(f"Patch 完成! 新插入 {total_inserted} 条记录。目前 training_datasets 表总行数: {count_out}")

if __name__ == '__main__':
    main()
