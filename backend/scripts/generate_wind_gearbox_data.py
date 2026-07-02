#!/usr/bin/env python3
"""
生成风电齿轮箱传感器增强数据
- 包含原始SCADA数据
- 新增振动信号（带噪声，用于降噪练习）
- 新增温度信号
- 注入故障标签
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(3003)

def generate_wind_turbine_data():
    """生成风电齿轮箱传感器增强数据"""

    # 生成1年的10分钟级数据（每台风机约 52,560 条）
    start_date = datetime(2023, 1, 1)
    minutes_per_year = 365 * 24 * 60  # 525,600分钟
    turbines = ['T01', 'T02', 'T03', 'T04', 'T05']

    data = []
    record_id = 1

    for turbine in turbines:
        # 每台风机稍微错开起始时间
        turbine_start = start_date + timedelta(hours=turbines.index(turbine) * 12)

        for i in range(52 * 24 * 6):  # 52周，每周采样
            ts = turbine_start + timedelta(minutes=i * 10)
            hour = ts.hour
            month = ts.month

            # 季节影响因子
            if month in [12, 1, 2]:
                season = '冬'
                season_factor = 0.9
            elif month in [3, 4, 5]:
                season = '春'
                season_factor = 1.0
            elif month in [6, 7, 8]:
                season = '夏'
                season_factor = 1.1
            else:
                season = '秋'
                season_factor = 1.0

            # 风速（基于时间变化，加入噪声）
            base_wind = 8 + 4 * np.sin(2 * np.pi * hour / 24)  # 日变化
            wind_speed = base_wind * season_factor + np.random.normal(0, 1.5)
            wind_speed = max(0, min(25, wind_speed))  # 限制范围

            # 理论功率（基于风速的立方关系）
            if wind_speed < 3:
                theoretical_power = 0
            elif wind_speed > 25:
                theoretical_power = 3000
            else:
                # 功率曲线近似
                theoretical_power = 0.5 * 3000 * ((wind_speed - 3) / 22) ** 3

            # 实际功率（加入正常运行波动）
            efficiency = np.random.uniform(0.85, 0.98)
            actual_power = theoretical_power * efficiency

            # 注入故障（在特定时间段）
            is_fault = False
            fault_prob = 0.008  # 约0.8%的故障率
            if np.random.random() < fault_prob:
                is_fault = True

            # ==========================================
            # 振动信号（带高斯噪声）
            # ==========================================
            if is_fault:
                # 故障时振动增大
                base_vibration_x = np.random.uniform(3.5, 6.0)
                base_vibration_y = np.random.uniform(3.0, 5.5)
                # 添加周期性冲击特征
                impact = np.random.uniform(0, 2) * np.sin(np.random.uniform(0, 10) * np.arange(10) / 10)
                base_vibration_x += impact[0]
                base_vibration_y += impact[1]
            else:
                # 正常振动
                base_vibration_x = np.random.uniform(0.5, 2.0)
                base_vibration_y = np.random.uniform(0.5, 2.0)

            # 添加高斯噪声（模拟传感器噪声）
            noise_level = 0.3
            vibration_x = base_vibration_x + np.random.normal(0, noise_level)
            vibration_y = base_vibration_y + np.random.normal(0, noise_level)
            vibration_x = max(0, min(10, vibration_x))
            vibration_y = max(0, min(10, vibration_y))

            # ==========================================
            # 温度信号（带噪声）
            # ==========================================
            if is_fault:
                # 故障时温度升高
                base_temp = np.random.uniform(70, 90)
                # 添加缓慢上升趋势
                temp_trend = np.random.uniform(0, 5)
            else:
                base_temp = np.random.uniform(45, 60)
                temp_trend = 0

            # 温度随风速略有变化（高风速时冷却更好）
            temp_adjustment = -0.5 * (wind_speed - 8)
            bearing_temp_c = base_temp + temp_adjustment + temp_trend + np.random.normal(0, 1.5)
            bearing_temp_c = max(30, min(100, bearing_temp_c))

            # ==========================================
            # 转子转速
            # ==========================================
            if wind_speed < 3:
                rotor_rpm = 0
            elif wind_speed > 25:
                rotor_rpm = 18
            else:
                rotor_rpm = 5 + 13 * (wind_speed - 3) / 22 + np.random.normal(0, 0.5)

            # ==========================================
            # 功率偏差
            # ==========================================
            if theoretical_power > 0:
                power_deviation_pct = (actual_power - theoretical_power) / theoretical_power * 100
            else:
                power_deviation_pct = 0

            efficiency_pct = (actual_power / theoretical_power * 100) if theoretical_power > 0 else 100

            # 确定异常类型
            if is_fault:
                if vibration_x > 4 or vibration_y > 4:
                    anomaly_type = 'vibration_anomaly'
                elif bearing_temp_c > 75:
                    anomaly_type = 'temperature_anomaly'
                else:
                    anomaly_type = 'power_anomaly'
            else:
                anomaly_type = 'normal'

            data.append({
                'record_id': f'WT{record_id:06d}',
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'turbine_id': turbine,
                'wind_speed_ms': round(wind_speed, 2),
                'wind_direction_deg': round(np.random.uniform(180, 360), 1),
                'actual_power_kw': round(actual_power, 2),
                'theoretical_power_kw': round(theoretical_power, 2),
                'power_deviation_pct': round(power_deviation_pct, 2),
                'efficiency_pct': round(efficiency_pct, 2),
                'rotor_rpm': round(rotor_rpm, 2),
                'vibration_x': round(vibration_x, 3),
                'vibration_y': round(vibration_y, 3),
                'bearing_temp_c': round(bearing_temp_c, 2),
                'hour': hour,
                'is_daytime': 1 if 6 <= hour <= 18 else 0,
                'month': month,
                'season': season,
                'anomaly_type': anomaly_type,
                'is_anomaly': 1 if is_fault else 0
            })
            record_id += 1

    df = pd.DataFrame(data)
    return df

def main():
    print("生成风电齿轮箱传感器增强数据...")

    # 生成数据
    df = generate_wind_turbine_data()

    # 保存路径
    output_dir = "/Users/jimfu/Work/huixue/ziyuan_data/实训资源/03-风电齿轮箱预警分析/datasets"

    # 保存数据
    output_file = os.path.join(output_dir, "gearbox_sensors.csv")
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"数据已保存: {output_file}")
    print(f"  - 记录数: {len(df):,}")
    print(f"  - 风机数量: {df['turbine_id'].nunique()}")

    # 数据统计
    print(f"\n数据统计:")
    print(f"  - 时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
    print(f"  - 异常样本: {df['is_anomaly'].sum():,} ({df['is_anomaly'].mean()*100:.2f}%)")
    print(f"  - 正常样本: {(~df['is_anomaly'].astype(bool)).sum():,}")

    print(f"\n特征统计:")
    print(f"  - 振动X范围: {df['vibration_x'].min():.2f} - {df['vibration_x'].max():.2f} mm/s")
    print(f"  - 振动Y范围: {df['vibration_y'].min():.2f} - {df['vibration_y'].max():.2f} mm/s")
    print(f"  - 轴承温度范围: {df['bearing_temp_c'].min():.1f} - {df['bearing_temp_c'].max():.1f} °C")

    # 异常类型分布
    print(f"\n异常类型分布:")
    anomaly_types = df[df['is_anomaly']==1]['anomaly_type'].value_counts()
    for atype, count in anomaly_types.items():
        print(f"  - {atype}: {count:,}")

    # 保存schema
    import json
    schema = {
        "generated_at": datetime.now().isoformat(),
        "scenario": "wind_gearbox",
        "seed": 3003,
        "files": [
            {
                "filename": "gearbox_sensors.csv",
                "description": "风电齿轮箱传感器数据（含振动、温度、功率）",
                "rows": len(df),
                "columns": list(df.columns)
            }
        ],
        "class_distribution": {
            "normal": int((~df['is_anomaly'].astype(bool)).sum()),
            "anomaly": int(df['is_anomaly'].sum()),
            "imbalance_ratio": round((~df['is_anomaly'].astype(bool)).sum() / df['is_anomaly'].sum(), 1)
        }
    }

    schema_file = os.path.join(output_dir, "_schema.json")
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"\nSchema已更新: {schema_file}")

if __name__ == "__main__":
    main()
