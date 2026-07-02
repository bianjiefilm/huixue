#!/usr/bin/env python3
"""
生成光伏发电预测增强数据集
- 包含气象数据和发电数据（需要合并）
- 注入阴天/多云天气样本（预测误差较大）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(2002)

def generate_pv_weather_data():
    """生成气象数据（小时级）"""
    start_date = datetime(2023, 1, 1)
    hours_per_year = 365 * 24

    timestamps = [start_date + timedelta(hours=i) for i in range(hours_per_year)]

    data = []

    for ts in timestamps:
        hour = ts.hour
        month = ts.month

        # 季节因子
        if month in [6, 7, 8]:  # 夏季
            season_factor = 1.2
            base_temp = 28
        elif month in [3, 4, 5]:  # 春季
            season_factor = 1.0
            base_temp = 18
        elif month in [9, 10, 11]:  # 秋季
            season_factor = 0.9
            base_temp = 15
        else:  # 冬季
            season_factor = 0.7
            base_temp = 5

        # 阴天标记（影响辐照度和预测误差）
        is_cloudy = np.random.random() < 0.15  # 15%的阴天概率

        # 辐照度（W/m²）- 白天有值，夜间为0
        if 6 <= hour <= 18:
            # 基础辐照度曲线（正弦形状）
            base_irradiance = 1000 * np.sin(np.pi * (hour - 6) / 12)
            # 加入随机波动
            irradiance = base_irradiance * season_factor * np.random.uniform(0.8, 1.2)

            if is_cloudy:
                irradiance *= np.random.uniform(0.2, 0.5)  # 阴天大幅降低
        else:
            irradiance = 0

        # 环境温度（°C）- 与时间、季节相关
        if 6 <= hour <= 18:
            temp_variation = 8 * np.sin(np.pi * (hour - 9) / 12)
        else:
            temp_variation = -2
        ambient_temp = base_temp + temp_variation + np.random.normal(0, 2)

        # 相对湿度（%）
        humidity = np.random.uniform(40, 90)
        if is_cloudy:
            humidity = np.random.uniform(70, 95)  # 阴天湿度高

        # 风速（m/s）
        wind_speed = np.random.uniform(1, 8)

        # 云量（0-10级）
        cloud_cover = np.random.uniform(0, 3)
        if is_cloudy:
            cloud_cover = np.random.uniform(7, 10)

        data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'hour': hour,
            'month': month,
            'irradiance_wm2': round(irradiance, 1),
            'ambient_temp_c': round(ambient_temp, 1),
            'relative_humidity_pct': round(humidity, 1),
            'wind_speed_ms': round(wind_speed, 1),
            'cloud_cover': round(cloud_cover, 1),
            'is_cloudy': 1 if is_cloudy else 0
        })

    return pd.DataFrame(data)

def generate_pv_power_data():
    """生成光伏发电数据（15分钟级）- 与气象数据不同源，需合并"""
    start_date = datetime(2023, 1, 1)
    intervals_per_hour = 4  # 15分钟间隔

    data = []

    for month in range(1, 13):
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]

        for day in range(1, days_in_month + 1):
            for hour in range(24):
                for minute in [0, 15, 30, 45]:
                    ts = datetime(2023, month, day, hour, minute)

                    # 读取对应小时的气象数据
                    weather_ts = ts.replace(minute=0)

                    # 计算理论发电功率
                    if 6 <= hour <= 18:
                        # 基础功率与辐照度成正比
                        irradiance_factor = irradiance_lookup.get(hour, 500)
                        theoretical_power = irradiance_factor * 0.15 * np.random.uniform(0.9, 1.0)

                        # 温度影响（温度过高会降低效率）
                        temp = temp_lookup.get(hour, 25)
                        temp_factor = 1 - 0.004 * max(0, temp - 25)
                        theoretical_power *= temp_factor
                    else:
                        theoretical_power = 0

                    # 实际发电功率（加入设备损耗和随机噪声）
                    if theoretical_power > 0:
                        efficiency = np.random.uniform(0.92, 0.98)
                        actual_power = theoretical_power * efficiency + np.random.normal(0, 2)
                        actual_power = max(0, actual_power)
                    else:
                        actual_power = 0

                    # 设备故障（低概率）
                    is_fault = 1 if np.random.random() < 0.002 else 0
                    if is_fault:
                        actual_power = 0

                    data.append({
                        'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                        'power_output_kw': round(actual_power, 2),
                        'is_fault': is_fault
                    })

    return pd.DataFrame(data)

#  lookup tables for realistic patterns
irradiance_lookup = {
    6: 150, 7: 350, 8: 550, 9: 750, 10: 900,
    11: 980, 12: 1000, 13: 980, 14: 900, 15: 750,
    16: 550, 17: 350, 18: 150
}

temp_lookup = {
    0: 10, 1: 8, 2: 7, 3: 6, 4: 6, 5: 7,
    6: 10, 7: 14, 8: 18, 9: 22, 10: 25, 11: 27,
    12: 28, 13: 29, 14: 28, 15: 27, 16: 25, 17: 22,
    18: 18, 19: 15, 20: 13, 21: 12, 22: 11, 23: 10
}

def main():
    print("生成光伏发电预测增强数据集...")

    output_dir = "/Users/jimfu/Work/huixue/ziyuan_data/实训资源/02-分布式光伏出力预测/datasets"

    # 生成气象数据
    print("\n📡 生成气象数据（小时级）...")
    df_weather = generate_pv_weather_data()
    weather_file = os.path.join(output_dir, "weather_data.csv")
    df_weather.to_csv(weather_file, index=False, encoding='utf-8')
    print(f"  已保存: {weather_file}")
    print(f"  记录数: {len(df_weather):,}")

    # 生成发电数据
    print("\n⚡ 生成光伏发电数据（15分钟级）...")
    df_power = generate_pv_power_data()
    power_file = os.path.join(output_dir, "pv_power.csv")
    df_power.to_csv(power_file, index=False, encoding='utf-8')
    print(f"  已保存: {power_file}")
    print(f"  记录数: {len(df_power):,}")

    # 生成合并后的完整数据
    print("\n🔗 合并气象与发电数据...")
    df_power['timestamp'] = pd.to_datetime(df_power['timestamp'])
    df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'])

    # 为气象数据添加时间戳（小时精度）用于合并
    df_weather_for_merge = df_weather.copy()
    df_weather_for_merge['timestamp_hour'] = df_weather_for_merge['timestamp']

    # 为发电数据添加时间戳（小时精度）用于合并
    df_power_for_merge = df_power.copy()
    df_power_for_merge['timestamp_hour'] = df_power_for_merge['timestamp'].dt.floor('h')

    # 合并数据
    df_merged = pd.merge(
        df_power_for_merge,
        df_weather_for_merge[['timestamp_hour', 'irradiance_wm2', 'ambient_temp_c',
                              'relative_humidity_pct', 'wind_speed_ms', 'cloud_cover', 'is_cloudy']],
        on='timestamp_hour',
        how='left'
    )

    merged_file = os.path.join(output_dir, "pv_power_merged.csv")
    df_merged.to_csv(merged_file, index=False, encoding='utf-8')
    print(f"  已保存: {merged_file}")
    print(f"  记录数: {len(df_merged):,}")

    # 统计信息
    print("\n📊 数据统计:")
    print(f"  气象数据字段: irradiance_wm2, ambient_temp_c, relative_humidity_pct, wind_speed_ms, cloud_cover")
    print(f"  发电数据字段: power_output_kw, is_fault")
    print(f"  阴天样本数: {df_weather['is_cloudy'].sum():,} ({df_weather['is_cloudy'].mean()*100:.1f}%)")
    print(f"  故障样本数: {df_power['is_fault'].sum():,} ({df_power['is_fault'].mean()*100:.1f}%)")

    # 保存schema
    import json
    schema = {
        "generated_at": datetime.now().isoformat(),
        "scenario": "pv_power_prediction",
        "seed": 2002,
        "files": [
            {
                "filename": "weather_data.csv",
                "description": "气象数据（小时级，需与发电数据合并）",
                "rows": len(df_weather),
                "frequency": "1小时"
            },
            {
                "filename": "pv_power.csv",
                "description": "光伏发电数据（15分钟级）",
                "rows": len(df_power),
                "frequency": "15分钟"
            },
            {
                "filename": "pv_power_merged.csv",
                "description": "合并后的完整数据集",
                "rows": len(df_merged)
            }
        ],
        "weather_features": [
            "irradiance_wm2 (辐照度)",
            "ambient_temp_c (环境温度)",
            "relative_humidity_pct (相对湿度)",
            "wind_speed_ms (风速)",
            "cloud_cover (云量)"
        ],
        "cloudy_ratio": float(df_weather['is_cloudy'].mean())
    }

    schema_file = os.path.join(output_dir, "_schema.json")
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"\nSchema已更新: {schema_file}")

if __name__ == "__main__":
    main()
