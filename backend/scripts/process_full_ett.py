#!/usr/bin/env python3
"""
处理完整ETDataset，保留原始字段语义
ETT: Electricity Transformer Temperature Dataset
来源: https://github.com/zhouhaoyi/ETDataset

原始字段含义:
- date: 时间戳
- HUFL: High UseFul Load (高压有功负载)
- HULL: High UseLess Load (高压无功负载)
- MUFL: Middle UseFul Load (中压有功负载)
- MULL: Middle UseLess Load (中压无功负载)
- LUFL: Low UseFul Load (低压有功负载)
- LULL: Low UseLess Load (低压无功负载)
- OT: Oil Temperature (油温，目标变量)
"""

import csv
import random
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "12-设备重过载精准预测" / "datasets" / "ETTh1_original.csv"
OUTPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "12-设备重过载精准预测" / "datasets" / "transformer_load_real.csv"


def calculate_overload_risk(hufl, hull, mufl, mull, lufl, lull, oil_temp):
    """
    基于实际物理意义计算过载风险

    风险因素:
    1. 油温: 变压器核心指标，>65°C警告，>80°C危险
    2. 有功负载: HUFL+MUFL+LUFL，反映实际功率消耗
    3. 无功负载: HULL+MULL+LULL，反映功率因数
    4. 负载不平衡: 各电压等级负载差异
    """
    # 计算总有功和无功负载
    total_useful = hufl + mufl + lufl
    total_useless = hull + mull + lull

    # 功率因数 (近似)
    if total_useful + total_useless > 0:
        power_factor = total_useful / (total_useful + abs(total_useless) + 0.001)
    else:
        power_factor = 0.9

    # 风险评分
    score = 0

    # 油温评分 (权重40%)
    if oil_temp >= 80:
        score += 40
    elif oil_temp >= 70:
        score += 32
    elif oil_temp >= 60:
        score += 24
    elif oil_temp >= 50:
        score += 16
    else:
        score += 8

    # 有功负载评分 (权重30%)
    # ETT数据范围约-5到15
    if total_useful >= 12:
        score += 30
    elif total_useful >= 8:
        score += 24
    elif total_useful >= 4:
        score += 18
    elif total_useful >= 0:
        score += 12
    else:
        score += 6

    # 功率因数评分 (权重20%)
    if power_factor < 0.7:
        score += 20
    elif power_factor < 0.8:
        score += 15
    elif power_factor < 0.9:
        score += 10
    else:
        score += 5

    # 负载不平衡评分 (权重10%)
    loads = [hufl + hull, mufl + mull, lufl + lull]
    if len(set(loads)) > 0:
        imbalance = (max(loads) - min(loads)) / (max(abs(l) for l in loads) + 0.001)
        score += imbalance * 10

    # 风险等级判定
    if score >= 70:
        return "critical", score
    elif score >= 55:
        return "high", score
    elif score >= 40:
        return "medium", score
    else:
        return "low", score


def process_data():
    """处理完整ETDataset"""
    with open(INPUT_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"读取原始数据: {len(rows)} 条")

    output_rows = []
    risk_counts = {}

    for i, row in enumerate(rows):
        # 解析原始字段
        timestamp = row['date']
        hufl = float(row['HUFL'])
        hull = float(row['HULL'])
        mufl = float(row['MUFL'])
        mull = float(row['MULL'])
        lufl = float(row['LUFL'])
        lull = float(row['LULL'])
        oil_temp = float(row['OT'])

        # 计算派生指标
        total_useful_load = hufl + mufl + lufl
        total_useless_load = hull + mull + lull
        total_load = total_useful_load + total_useless_load

        # 功率因数
        if abs(total_useful_load) + abs(total_useless_load) > 0:
            power_factor = abs(total_useful_load) / (abs(total_useful_load) + abs(total_useless_load))
        else:
            power_factor = 0.9

        # 负载率 (假设额定总负载为20)
        load_factor = total_load / 20

        # 计算过载风险
        risk_level, risk_score = calculate_overload_risk(
            hufl, hull, mufl, mull, lufl, lull, oil_temp
        )
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

        # 解析时间特征
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            hour = dt.hour
            month = dt.month
            weekday = dt.weekday()
        except:
            hour = 0
            month = 1
            weekday = 0

        # 构建输出记录 (保留原始字段 + 添加派生字段)
        output_row = {
            'record_id': f'ETT{i+1:06d}',
            'timestamp': timestamp,
            # 原始字段 (保留英文+中文注释)
            'HUFL': round(hufl, 4),  # 高压有功负载
            'HULL': round(hull, 4),  # 高压无功负载
            'MUFL': round(mufl, 4),  # 中压有功负载
            'MULL': round(mull, 4),  # 中压无功负载
            'LUFL': round(lufl, 4),  # 低压有功负载
            'LULL': round(lull, 4),  # 低压无功负载
            'OT': round(oil_temp, 2),  # 油温
            # 派生字段
            'total_useful_load': round(total_useful_load, 4),
            'total_useless_load': round(total_useless_load, 4),
            'total_load': round(total_load, 4),
            'power_factor': round(power_factor, 4),
            'load_factor': round(load_factor, 4),
            # 时间特征
            'hour': hour,
            'month': month,
            'weekday': weekday,
            # 风险评估
            'risk_score': round(risk_score, 2),
            'overload_risk': risk_level
        }
        output_rows.append(output_row)

        if (i + 1) % 5000 == 0:
            print(f"已处理 {i+1}/{len(rows)} 条...")

    # 保存
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(output_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\n=== 处理完成 ===")
    print(f"总记录数: {len(output_rows)}")
    print(f"输出文件: {OUTPUT_PATH}")
    print(f"\n风险等级分布:")
    for level, count in sorted(risk_counts.items(), key=lambda x: -x[1]):
        pct = count / len(output_rows) * 100
        print(f"  {level}: {count} ({pct:.2f}%)")


if __name__ == "__main__":
    process_data()
