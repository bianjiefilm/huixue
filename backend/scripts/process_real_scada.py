#!/usr/bin/env python3
"""
处理真实风电SCADA数据 (Kaggle Turkey Wind Turbine)
- 添加异常检测标签
- 计算功率偏差
- 添加时间特征
"""

import csv
import random
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "03-风电齿轮箱预警分析" / "datasets" / "T1.csv"
OUTPUT_PATH = BASE_DIR / "ziyuan_data" / "实训资源" / "03-风电齿轮箱预警分析" / "datasets" / "wind_turbine_scada_real.csv"


def parse_datetime(dt_str):
    """解析日期时间字符串"""
    # 格式: "01 01 2018 00:00"
    try:
        return datetime.strptime(dt_str.strip(), "%d %m %Y %H:%M")
    except:
        return None


def detect_anomaly(actual_power, theoretical_power, wind_speed):
    """
    基于功率曲线偏差检测异常
    真实的异常检测逻辑：
    1. 功率偏差过大
    2. 低风速高功率（不可能）
    3. 高风速低功率（可能故障）
    """
    if theoretical_power <= 0:
        return "normal", 0

    # 计算功率偏差百分比
    deviation = (actual_power - theoretical_power) / theoretical_power * 100

    # 异常检测规则
    if wind_speed < 3 and actual_power > 100:
        # 低风速不应该有高功率
        return "sensor_error", deviation

    if wind_speed > 10 and actual_power < theoretical_power * 0.3:
        # 高风速下功率过低，可能故障
        return "underperformance", deviation

    if actual_power < 0:
        # 负功率，消耗电力（可能是维护或故障）
        return "maintenance", deviation

    if abs(deviation) > 50:
        # 偏差超过50%
        return "high_deviation", deviation

    if abs(deviation) > 30:
        # 偏差30-50%，轻微异常
        return "moderate_deviation", deviation

    return "normal", deviation


def process_data():
    """处理SCADA数据"""
    with open(INPUT_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"读取原始数据: {len(rows)} 条")

    output_rows = []
    anomaly_counts = {}

    for i, row in enumerate(rows):
        # 解析原始字段
        dt = parse_datetime(row['Date/Time'])
        if not dt:
            continue

        actual_power = float(row['LV ActivePower (kW)'])
        wind_speed = float(row['Wind Speed (m/s)'])
        theoretical_power = float(row['Theoretical_Power_Curve (KWh)'])
        wind_direction = float(row['Wind Direction (°)'])

        # 检测异常
        anomaly_type, power_deviation = detect_anomaly(
            actual_power, theoretical_power, wind_speed
        )

        # 统计异常
        anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1

        # 添加时间特征
        hour = dt.hour
        is_daytime = 1 if 6 <= hour < 18 else 0
        month = dt.month
        season = {12: "冬", 1: "冬", 2: "冬",
                  3: "春", 4: "春", 5: "春",
                  6: "夏", 7: "夏", 8: "夏",
                  9: "秋", 10: "秋", 11: "秋"}.get(month, "未知")

        # 计算效率
        efficiency = (actual_power / theoretical_power * 100) if theoretical_power > 0 else 0

        # 构建输出记录
        output_row = {
            'record_id': f'WT{i+1:06d}',
            'timestamp': dt.strftime("%Y-%m-%d %H:%M"),
            'turbine_id': 'T01',  # 单台风机
            'wind_speed_ms': round(wind_speed, 2),
            'wind_direction_deg': round(wind_direction, 1),
            'actual_power_kw': round(actual_power, 2),
            'theoretical_power_kw': round(theoretical_power, 2),
            'power_deviation_pct': round(power_deviation, 2),
            'efficiency_pct': round(efficiency, 2),
            'hour': hour,
            'is_daytime': is_daytime,
            'month': month,
            'season': season,
            'anomaly_type': anomaly_type,
            'is_anomaly': 0 if anomaly_type == 'normal' else 1
        }
        output_rows.append(output_row)

        if (i + 1) % 10000 == 0:
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
    print(f"\n异常分布:")
    for atype, count in sorted(anomaly_counts.items(), key=lambda x: -x[1]):
        pct = count / len(output_rows) * 100
        print(f"  {atype}: {count} ({pct:.2f}%)")


if __name__ == "__main__":
    process_data()
