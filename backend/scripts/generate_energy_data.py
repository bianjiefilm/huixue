#!/usr/bin/env python3
"""
生成企业用能环保监测高频数据
- 分钟级采样数据（用于重采样练习）
- 添加产量字段（用于产污系数计算）
- 注入偷排异常（用于规则检测练习）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(6006)  # 保持一致的随机种子

def generate_energy_data():
    """生成分钟级企业用能监测数据"""

    # 生成35天的分钟级数据 (35 * 24 * 60 = 50,400 条)
    start_date = datetime(2023, 1, 1)
    minutes = 35 * 24 * 60  # 约50,400条记录

    timestamps = [start_date + timedelta(minutes=i) for i in range(minutes)]

    data = []

    # 定义偷排异常日期（每隔几天在深夜有异常）
    anomaly_dates = [3, 7, 12, 18, 24, 30]  # 在这些天的深夜注入异常

    for i, ts in enumerate(timestamps):
        hour = ts.hour
        day = ts.day
        is_weekend = ts.weekday() >= 5

        # 基础用电模式（分钟级，单位kWh）
        # 白天高(8-18点)，晚上低
        if 8 <= hour <= 18:
            base_power = np.random.uniform(4.5, 6.5)  # 白天高峰
        elif 6 <= hour < 8 or 18 < hour <= 20:
            base_power = np.random.uniform(2.5, 4.0)  # 过渡时段
        else:
            base_power = np.random.uniform(1.5, 2.5)  # 深夜低谷

        # 周末降低
        if is_weekend:
            base_power *= 0.6

        # 产量（与白天用电正相关）
        if 8 <= hour <= 18 and not is_weekend:
            production = np.random.uniform(8, 15)  # 白天生产
        elif 6 <= hour < 8 or 18 < hour <= 20:
            production = np.random.uniform(3, 8)  # 过渡
        else:
            production = np.random.uniform(0, 2)  # 深夜基本停产

        # 注入偷排异常：深夜高用电但低产量
        is_anomaly = False
        if day in anomaly_dates and 0 <= hour <= 4:
            # 偷排：深夜用电量异常高，但产量很低
            base_power = np.random.uniform(5.0, 8.0)  # 深夜异常高用电
            production = np.random.uniform(0, 1)  # 产量很低
            is_anomaly = True

        # 碳排放（与用电量相关，碳排放因子约0.785）
        carbon = base_power * np.random.uniform(0.75, 0.85)

        # 用水量（与生产相关）
        water = production * np.random.uniform(0.08, 0.12)

        # PM2.5（正常10-60，偷排时可能更高）
        if is_anomaly:
            pm25 = np.random.uniform(80, 150)  # 偷排时PM2.5升高
        else:
            pm25 = np.random.uniform(10, 60) + (base_power * 2)

        # SO2（正常0.001-0.05，偷排时可能更高）
        if is_anomaly:
            so2 = np.random.uniform(0.08, 0.15)  # 偷排时SO2升高
        else:
            so2 = np.random.uniform(0.001, 0.05)

        data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'power_kwh': round(base_power, 3),
            'carbon_emission_kg': round(carbon, 3),
            'water_consumption_m3': round(water, 4),
            'production_units': round(production, 2),
            'pm25': round(pm25, 1),
            'so2_ppm': round(so2, 4)
        })

    df = pd.DataFrame(data)
    return df

def main():
    print("生成企业用能环保监测数据...")

    # 生成数据
    df = generate_energy_data()

    # 保存路径
    output_dir = "/Users/jimfu/Work/huixue/ziyuan_data/实训资源/06-企业用能环保监测分析/datasets"

    # 保存分钟级数据
    minute_file = os.path.join(output_dir, "energy_monitoring_minute.csv")
    df.to_csv(minute_file, index=False, encoding='utf-8')
    print(f"分钟级数据已保存: {minute_file}")
    print(f"  - 记录数: {len(df)}")
    print(f"  - 时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")

    # 同时生成小时级数据（作为参考答案）
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_hourly = df.set_index('timestamp').resample('H').agg({
        'power_kwh': 'sum',
        'carbon_emission_kg': 'sum',
        'water_consumption_m3': 'sum',
        'production_units': 'sum',
        'pm25': 'mean',
        'so2_ppm': 'mean'
    }).round(3).reset_index()

    hourly_file = os.path.join(output_dir, "energy_monitoring_hourly.csv")
    df_hourly.to_csv(hourly_file, index=False, encoding='utf-8')
    print(f"小时级数据已保存: {hourly_file}")
    print(f"  - 记录数: {len(df_hourly)}")

    # 更新schema
    schema = {
        "generated_at": datetime.now().isoformat(),
        "scenario": "energy_monitoring",
        "seed": 6006,
        "files": [
            {
                "filename": "energy_monitoring_minute.csv",
                "description": "分钟级能源监测数据（高频采样）",
                "rows": len(df),
                "columns": ["timestamp", "power_kwh", "carbon_emission_kg", "water_consumption_m3", "production_units", "pm25", "so2_ppm"]
            },
            {
                "filename": "energy_monitoring_hourly.csv",
                "description": "小时级能源监测数据（重采样后）",
                "rows": len(df_hourly),
                "columns": ["timestamp", "power_kwh", "carbon_emission_kg", "water_consumption_m3", "production_units", "pm25", "so2_ppm"]
            }
        ],
        "anomaly_injection": {
            "type": "night_discharge",
            "dates": [3, 7, 12, 18, 24, 30],
            "hours": "0-4",
            "description": "深夜高用电低产量异常（模拟偷排）"
        }
    }

    import json
    schema_file = os.path.join(output_dir, "_schema.json")
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"Schema已更新: {schema_file}")

    # 数据质量检查
    print("\n数据统计:")
    print(f"  - 用电量范围: {df['power_kwh'].min():.2f} - {df['power_kwh'].max():.2f} kWh")
    print(f"  - 产量范围: {df['production_units'].min():.2f} - {df['production_units'].max():.2f} units")
    print(f"  - PM2.5范围: {df['pm25'].min():.1f} - {df['pm25'].max():.1f} μg/m³")
    print(f"  - SO2范围: {df['so2_ppm'].min():.4f} - {df['so2_ppm'].max():.4f} ppm")

    # 检查异常数据
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    df['day'] = pd.to_datetime(df['timestamp']).dt.day
    anomaly_count = len(df[(df['day'].isin([3,7,12,18,24,30])) & (df['hour'] <= 4) & (df['power_kwh'] > 4)])
    print(f"  - 注入的偷排异常记录数: {anomaly_count}")

if __name__ == "__main__":
    main()
