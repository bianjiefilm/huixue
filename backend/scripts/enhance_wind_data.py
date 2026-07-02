#!/usr/bin/env python3
"""
增强风电齿轮箱数据集
- 提高异常率从0.68%到约3%
- 添加缺失值
- 添加故障类型分类
"""

import csv
import random
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "03-风电齿轮箱预警分析" / "datasets" / "gearbox_sensors.csv"
OUTPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "03-风电齿轮箱预警分析" / "datasets" / "gearbox_sensors_enhanced.csv"

# 故障类型
FAULT_TYPES = {
    "normal": "正常",
    "vibration_high": "振动过高",
    "bearing_overheat": "轴承过热",
    "speed_anomaly": "转速异常",
    "compound_fault": "复合故障"
}


def enhance_data():
    """增强数据集"""
    with open(INPUT_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"读取原始数据: {len(rows)} 条")

    # 统计原始异常数
    original_faults = sum(1 for r in rows if r['status_label'] == '1')
    print(f"原始异常数: {original_faults} ({original_faults/len(rows)*100:.2f}%)")

    output_rows = []
    added_faults = 0
    missing_count = 0

    for i, row in enumerate(rows):
        # 解析原始数据
        turbine_id = row['turbine_id']
        timestamp = row['timestamp']
        wind_speed = float(row['wind_speed_ms'])
        rotor_rpm = float(row['rotor_rpm'])
        vibration_x = float(row['vibration_x'])
        vibration_y = float(row['vibration_y'])
        bearing_temp = float(row['bearing_temp_c'])
        status = int(row['status_label'])

        # 添加新异常 (目标总异常率约3%)
        # 当前异常率0.68%，需要增加约2.3%
        if status == 0 and random.random() < 0.025:
            status = 1
            added_faults += 1

            # 根据故障类型修改数据特征
            fault_type = random.choice(['vibration_high', 'bearing_overheat', 'speed_anomaly', 'compound_fault'])

            if fault_type == 'vibration_high':
                vibration_x *= random.uniform(1.8, 3.0)
                vibration_y *= random.uniform(1.8, 3.0)
            elif fault_type == 'bearing_overheat':
                bearing_temp += random.uniform(15, 35)
            elif fault_type == 'speed_anomaly':
                rotor_rpm *= random.choice([0.3, 0.5, 1.5, 2.0])
            else:  # compound_fault
                vibration_x *= random.uniform(1.5, 2.5)
                bearing_temp += random.uniform(10, 25)
        else:
            fault_type = 'normal' if status == 0 else random.choice(['vibration_high', 'bearing_overheat', 'speed_anomaly', 'compound_fault'])

        # 添加缺失值 (2%概率)
        if random.random() < 0.02:
            field = random.choice(['wind_speed_ms', 'vibration_x', 'vibration_y'])
            if field == 'wind_speed_ms':
                wind_speed = ''
            elif field == 'vibration_x':
                vibration_x = ''
            else:
                vibration_y = ''
            missing_count += 1

        # 添加异常值 (0.5%概率) - 传感器故障
        if random.random() < 0.005:
            field = random.choice(['bearing_temp_c', 'rotor_rpm'])
            if field == 'bearing_temp_c':
                bearing_temp = random.choice([-999, 0, 999])
            else:
                rotor_rpm = random.choice([-100, 9999])

        output_row = {
            'turbine_id': turbine_id,
            'timestamp': timestamp,
            'wind_speed_ms': round(wind_speed, 2) if wind_speed != '' else '',
            'rotor_rpm': round(rotor_rpm, 2) if isinstance(rotor_rpm, float) else rotor_rpm,
            'vibration_x': round(vibration_x, 4) if vibration_x != '' else '',
            'vibration_y': round(vibration_y, 4) if vibration_y != '' else '',
            'bearing_temp_c': round(bearing_temp, 2) if isinstance(bearing_temp, float) else bearing_temp,
            'status_label': status,
            'fault_type': FAULT_TYPES[fault_type]
        }
        output_rows.append(output_row)

        if (i + 1) % 20000 == 0:
            print(f"已处理 {i+1}/{len(rows)} 条...")

    # 保存
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(output_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    # 统计
    total_faults = sum(1 for r in output_rows if r['status_label'] == 1)
    print(f"\n=== 增强完成 ===")
    print(f"总记录数: {len(output_rows)}")
    print(f"新增异常: {added_faults}")
    print(f"总异常数: {total_faults} ({total_faults/len(output_rows)*100:.2f}%)")
    print(f"缺失值数: {missing_count}")
    print(f"输出文件: {OUTPUT_PATH}")

    # 故障类型分布
    fault_dist = {}
    for r in output_rows:
        ft = r['fault_type']
        fault_dist[ft] = fault_dist.get(ft, 0) + 1
    print(f"\n故障类型分布: {fault_dist}")


if __name__ == "__main__":
    enhance_data()
