#!/usr/bin/env python3
"""
处理ETDataset，转换为设备重过载预测教学数据集
原始数据: https://github.com/zhouhaoyi/ETDataset
"""

import csv
import random
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "12-设备重过载精准预测" / "datasets" / "ETTh1_original.csv"
OUTPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "12-设备重过载精准预测" / "datasets" / "equipment_load_enhanced.csv"

# 设备配置 (模拟多台设备)
EQUIPMENT = {
    "TR001": {"name": "1号主变压器", "rated_power": 10000, "location": "东区"},
    "TR002": {"name": "2号主变压器", "rated_power": 10000, "location": "东区"},
    "TR003": {"name": "3号配变", "rated_power": 2000, "location": "西区"},
    "TR004": {"name": "4号配变", "rated_power": 2000, "location": "西区"},
    "TR005": {"name": "5号配变", "rated_power": 1000, "location": "南区"},
}


def calculate_load_factor(hufl, hull, mufl, mull, lufl, lull):
    """根据原始特征计算负载因子"""
    # 归一化各电压等级负载
    high_load = (hufl + hull) / 2
    medium_load = (mufl + mull) / 2
    low_load = (lufl + lull) / 2

    # 综合负载因子 (归一化到0-1范围)
    total = (high_load * 0.5 + medium_load * 0.3 + low_load * 0.2)
    # 映射到0.4-1.1范围
    load_factor = 0.4 + (total + 5) / 20 * 0.7
    return max(0.3, min(1.15, load_factor))


def calculate_overload_risk(load_factor, oil_temp, equipment_age_factor=1.0):
    """计算过载风险等级 - 基于相对排名"""
    # 风险评分 (0-100)
    score = 0

    # 负载因子影响 (权重40%) - 使用相对阈值
    # 原始数据load_factor范围约0.5-0.9
    if load_factor >= 0.85:
        score += 40
    elif load_factor >= 0.75:
        score += 30
    elif load_factor >= 0.68:
        score += 20
    elif load_factor >= 0.60:
        score += 10
    else:
        score += 5

    # 油温影响 (权重35%) - 使用相对阈值
    # 原始数据oil_temp范围约15-45
    if oil_temp >= 40:
        score += 35
    elif oil_temp >= 35:
        score += 28
    elif oil_temp >= 30:
        score += 20
    elif oil_temp >= 25:
        score += 12
    else:
        score += 5

    # 设备老化影响 (权重25%)
    age_score = 25 * (1 - equipment_age_factor)
    score += age_score

    # 加入随机扰动 (增大扰动范围使分布更均匀)
    score += random.gauss(0, 12)

    # 风险等级判定 (调整阈值使分布更均匀)
    if score >= 55:
        return "critical"
    elif score >= 42:
        return "high"
    elif score >= 30:
        return "medium"
    else:
        return "low"


def process_data():
    """处理原始数据，逐条转换"""
    with open(INPUT_PATH, 'r') as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)

    print(f"读取原始数据: {len(rows)} 条")

    # 准备输出
    output_rows = []

    # 设备老化因子 (模拟不同设备的健康状态)
    equipment_age = {eq: random.uniform(0.85, 1.0) for eq in EQUIPMENT}

    # 取前5000条数据
    target_count = min(5000, len(rows))
    equipment_list = list(EQUIPMENT.keys())

    for i, row in enumerate(rows[:target_count]):
        record_id = i + 1

        # 随机分配设备 (但保持一定连续性)
        if i % 20 == 0:
            current_equipment = random.choice(equipment_list)
        eq_id = current_equipment
        eq_info = EQUIPMENT[eq_id]

        # 解析原始数据
        timestamp = row['date']
        hufl = float(row['HUFL'])
        hull = float(row['HULL'])
        mufl = float(row['MUFL'])
        mull = float(row['MULL'])
        lufl = float(row['LUFL'])
        lull = float(row['LULL'])
        oil_temp = float(row['OT'])

        # 计算派生字段
        load_factor = calculate_load_factor(hufl, hull, mufl, mull, lufl, lull)

        # 根据设备额定功率计算当前负载
        rated_power = eq_info['rated_power']
        current_load = rated_power * load_factor

        # 电压和电流估算
        voltage = 380 + random.gauss(0, 5)
        current = current_load / (voltage * 0.9 * 1.732) * 1000  # 三相电流

        # 功率因数
        power_factor = 0.85 + random.gauss(0, 0.03)
        power_factor = max(0.7, min(0.98, power_factor))

        # 环境参数
        ambient_temp = 20 + (oil_temp - 30) * 0.3 + random.gauss(0, 3)
        humidity = 50 + random.gauss(0, 15)

        # 运行时间 (累计)
        runtime_hours = 1000 + i * 24 + random.randint(0, 100)

        # 距上次维护天数
        maintenance_days = random.randint(10, 180)

        # 计算过载风险
        overload_risk = calculate_overload_risk(
            load_factor, oil_temp, equipment_age[eq_id]
        )

        # 设备老化 (每1000条数据老化一点)
        if record_id % 1000 == 0:
            for eq in equipment_age:
                equipment_age[eq] -= random.uniform(0.005, 0.015)

        # 添加缺失值 (3%概率)
        if random.random() < 0.03:
            field = random.choice(['current_load_kw', 'oil_temp_c', 'current_a'])
            if field == 'current_load_kw':
                current_load = ''
            elif field == 'oil_temp_c':
                oil_temp = ''
            else:
                current = ''

        # 添加异常值 (1%概率)
        if random.random() < 0.01:
            field = random.choice(['voltage_v', 'oil_temp_c'])
            if field == 'voltage_v':
                voltage = random.choice([0, 999, -100])
            else:
                oil_temp = random.choice([-50, 200, 999])

        output_row = {
            'record_id': f'R{record_id:05d}',
            'timestamp': timestamp,
            'equipment_id': eq_id,
            'equipment_name': eq_info['name'],
            'location': eq_info['location'],
            'rated_power_kw': rated_power,
            'current_load_kw': round(current_load, 1) if current_load != '' else '',
            'load_factor': round(load_factor, 3),
            'voltage_v': round(voltage, 1) if isinstance(voltage, float) else voltage,
            'current_a': round(current, 1) if current != '' and isinstance(current, float) else '',
            'power_factor': round(power_factor, 3),
            'oil_temp_c': round(oil_temp, 1) if oil_temp != '' and isinstance(oil_temp, float) else oil_temp,
            'ambient_temp_c': round(ambient_temp, 1),
            'humidity_pct': round(humidity, 0),
            'runtime_hours': runtime_hours,
            'maintenance_days': maintenance_days,
            'overload_risk': overload_risk
        }
        output_rows.append(output_row)

        # 进度显示
        if record_id % 1000 == 0:
            print(f"已处理 {record_id}/{target_count} 条...")

    # 写入输出文件
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f_out:
        fieldnames = list(output_rows[0].keys())
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"已保存 {len(output_rows)} 条记录到 {OUTPUT_PATH}")

    # 统计
    risk_counts = {}
    for row in output_rows:
        r = row['overload_risk']
        risk_counts[r] = risk_counts.get(r, 0) + 1

    print(f"\n风险等级分布: {risk_counts}")


if __name__ == "__main__":
    process_data()
