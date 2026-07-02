#!/usr/bin/env python3
"""
轮胎质量数据逐条生成器
模拟真实生产场景，每条记录独立生成，具有上下文关联性
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# 输出路径
OUTPUT_PATH = Path(__file__).parent.parent.parent / "ziyuan_data" / "实训资源" / "11-轮胎质量相关性分析" / "datasets" / "tire_quality_enhanced.csv"

# 生产线配置
PRODUCTION_LINES = {
    "L1": {"name": "一号线", "quality_bias": 0.02, "age_years": 2},
    "L2": {"name": "二号线", "quality_bias": 0.0, "age_years": 1},
    "L3": {"name": "三号线", "quality_bias": -0.03, "age_years": 5},  # 老旧设备
}

# 班次配置
SHIFTS = {
    "早班": {"start": 6, "end": 14, "fatigue_factor": 0.0},
    "中班": {"start": 14, "end": 22, "fatigue_factor": 0.01},
    "夜班": {"start": 22, "end": 6, "fatigue_factor": 0.03},  # 夜班疲劳影响
}

# 原材料批次 (模拟不同供应商)
MATERIAL_BATCHES = {
    "M001": {"supplier": "优质橡胶A", "quality_factor": 1.02},
    "M002": {"supplier": "标准橡胶B", "quality_factor": 1.0},
    "M003": {"supplier": "经济橡胶C", "quality_factor": 0.97},
}

# 缺陷类型及其触发条件
DEFECT_TYPES = ["无", "轻微气泡", "气泡", "轻微裂纹", "裂纹", "严重气泡", "严重裂纹"]


class TireDataGenerator:
    """轮胎数据逐条生成器"""

    def __init__(self):
        self.records = []
        self.current_date = datetime(2023, 1, 1)
        self.batch_counter = 0
        self.current_line = "L1"
        self.current_shift = "早班"
        self.current_material = "M001"
        self.equipment_status = {line: 1.0 for line in PRODUCTION_LINES}  # 设备状态系数
        self.weather_temp = 20  # 环境温度
        self.weather_humidity = 50  # 环境湿度

    def _update_context(self):
        """更新生产上下文（模拟时间推进）"""
        # 每生成几条数据，时间推进
        if self.batch_counter % 3 == 0:
            self.current_date += timedelta(hours=random.randint(1, 4))

        # 每天开始时更新环境
        if self.current_date.hour == 6 and self.batch_counter % 10 == 0:
            self.weather_temp = random.gauss(22, 8)  # 季节性温度变化
            self.weather_humidity = random.gauss(55, 15)

        # 确定当前班次
        hour = self.current_date.hour
        if 6 <= hour < 14:
            self.current_shift = "早班"
        elif 14 <= hour < 22:
            self.current_shift = "中班"
        else:
            self.current_shift = "夜班"

        # 随机切换生产线（模拟多线并行）
        if random.random() < 0.3:
            self.current_line = random.choice(list(PRODUCTION_LINES.keys()))

        # 定期更换原材料批次
        if self.batch_counter % 50 == 0:
            self.current_material = random.choice(list(MATERIAL_BATCHES.keys()))

        # 设备老化和维护（随机事件）
        for line in PRODUCTION_LINES:
            # 设备自然老化
            self.equipment_status[line] -= random.uniform(0, 0.001)
            # 维护恢复
            if random.random() < 0.02:
                self.equipment_status[line] = min(1.0, self.equipment_status[line] + 0.1)
            # 限制范围
            self.equipment_status[line] = max(0.85, min(1.0, self.equipment_status[line]))

    def generate_one_record(self):
        """生成单条轮胎质量记录"""
        self._update_context()
        self.batch_counter += 1

        # 获取当前上下文
        line_config = PRODUCTION_LINES[self.current_line]
        shift_config = SHIFTS[self.current_shift]
        material_config = MATERIAL_BATCHES[self.current_material]
        equipment_factor = self.equipment_status[self.current_line]

        # 计算综合影响因子
        quality_modifier = (
            line_config["quality_bias"] +
            shift_config["fatigue_factor"] * (-1) +
            (material_config["quality_factor"] - 1) +
            (equipment_factor - 1) * 0.5
        )

        # ========== 逐个生成各字段 ==========

        # 批次ID
        batch_id = f"B{self.batch_counter:04d}"

        # 生产日期
        production_date = self.current_date.strftime("%Y-%m-%d")

        # 生产时间
        production_time = self.current_date.strftime("%H:%M")

        # 生产线
        production_line = self.current_line

        # 班次
        shift = self.current_shift

        # 原材料批次
        material_batch = self.current_material

        # 操作员ID (每个班次3-4个操作员轮换)
        operator_id = f"OP{random.randint(1, 12):03d}"

        # ========== 工艺参数 ==========

        # 橡胶硬度 (受原材料和温度影响) - Shore A: 60-80
        base_hardness = 68.0  # 轮胎胎面典型值
        hardness_variation = random.gauss(0, 3.0)
        temp_effect = (self.weather_temp - 20) * (-0.08)  # 温度高，硬度略降
        rubber_hardness = base_hardness + hardness_variation + temp_effect + quality_modifier * 4
        rubber_hardness = max(58, min(82, rubber_hardness))  # 限制在合理范围

        # 帘线张力 (与硬度正相关) - 单位N
        base_tension = 900
        cord_tension = base_tension + (rubber_hardness - 68) * 12 + random.gauss(0, 25)

        # 硫化温度 (工艺控制参数) - 145-180°C (汽车轮胎145-160°C)
        base_vulc_temp = 155
        vulcanization_temp = base_vulc_temp + random.gauss(0, 5) + quality_modifier * 3
        vulcanization_temp = max(145, min(175, vulcanization_temp))

        # 硫化时间 (与温度负相关) - 10-20分钟
        base_vulc_time = 15  # 修正为工业标准
        vulcanization_time = base_vulc_time - (vulcanization_temp - 155) * 0.15 + random.gauss(0, 1.5)
        vulcanization_time = max(10, min(22, vulcanization_time))

        # 冷却速率 (受环境温度影响)
        base_cooling = 2.1
        cooling_rate = base_cooling + (self.weather_temp - 20) * 0.02 + random.gauss(0, 0.2)

        # ========== 产品特性 ==========

        # 胎面深度 (与硫化参数相关)
        base_depth = 12.5
        tread_depth = base_depth + (vulcanization_time - 45) * 0.1 + random.gauss(0, 0.5)

        # 胎侧厚度
        base_thickness = 8.0
        sidewall_thickness = base_thickness + (rubber_hardness - 65) * 0.05 + random.gauss(0, 0.3)

        # ========== 质量评估 ==========

        # 质量分数计算 (综合多个因素) - 校准后的参数
        base_score = 90

        # 各因素对质量的影响 (使用校准后的最佳值)
        hardness_score = -abs(rubber_hardness - 68) * 0.8  # 最佳硬度68 Shore A
        tension_score = -abs(cord_tension - 900) * 0.01  # 最佳张力900N
        temp_score = -abs(vulcanization_temp - 155) * 0.3  # 最佳温度155°C
        time_score = -abs(vulcanization_time - 15) * 0.5  # 最佳时间15分钟
        cooling_score = -abs(cooling_rate - 2.0) * 1.5  # 最佳冷却速率2.0

        quality_score = (base_score + hardness_score + tension_score +
                        temp_score + time_score + cooling_score +
                        quality_modifier * 8 + random.gauss(0, 3))
        quality_score = max(55, min(100, quality_score))

        # 缺陷类型判定
        if quality_score >= 90:
            defect_type = "无"
        elif quality_score >= 85:
            defect_type = random.choice(["无", "无", "轻微气泡", "轻微裂纹"])
        elif quality_score >= 78:
            defect_type = random.choice(["轻微气泡", "轻微裂纹", "气泡"])
        elif quality_score >= 70:
            defect_type = random.choice(["气泡", "裂纹"])
        else:
            defect_type = random.choice(["严重气泡", "严重裂纹"])

        # 是否通过检验
        if quality_score >= 75 and defect_type not in ["严重气泡", "严重裂纹", "气泡", "裂纹"]:
            pass_inspection = 1
        elif quality_score >= 80 and defect_type in ["轻微气泡", "轻微裂纹"]:
            pass_inspection = 1
        else:
            pass_inspection = 0 if quality_score < 75 or defect_type in ["严重气泡", "严重裂纹", "气泡", "裂纹"] else 1

        # ========== 添加缺失值和异常值 ==========

        # 5%概率产生缺失值
        if random.random() < 0.05:
            field_to_miss = random.choice(["rubber_hardness", "cord_tension", "cooling_rate"])
            if field_to_miss == "rubber_hardness":
                rubber_hardness = None
            elif field_to_miss == "cord_tension":
                cord_tension = None
            else:
                cooling_rate = None

        # 2%概率产生异常值（传感器故障）
        if random.random() < 0.02:
            field_to_error = random.choice(["vulcanization_temp", "rubber_hardness"])
            if field_to_error == "vulcanization_temp":
                vulcanization_temp = random.choice([0, 999, -50])  # 明显异常
            else:
                rubber_hardness = random.choice([0, 150, -10])

        # 构建记录
        record = {
            "batch_id": batch_id,
            "production_date": production_date,
            "production_time": production_time,
            "production_line": production_line,
            "shift": shift,
            "operator_id": operator_id,
            "material_batch": material_batch,
            "rubber_hardness": round(rubber_hardness, 1) if rubber_hardness is not None else "",
            "cord_tension": round(cord_tension, 0) if cord_tension is not None else "",
            "tread_depth": round(tread_depth, 2),
            "sidewall_thickness": round(sidewall_thickness, 2),
            "vulcanization_temp": round(vulcanization_temp, 0),
            "vulcanization_time": round(vulcanization_time, 0),
            "cooling_rate": round(cooling_rate, 2) if cooling_rate is not None else "",
            "ambient_temp": round(self.weather_temp, 1),
            "ambient_humidity": round(self.weather_humidity, 0),
            "quality_score": round(quality_score, 1),
            "defect_type": defect_type,
            "pass_inspection": pass_inspection
        }

        self.records.append(record)
        return record

    def save_to_csv(self):
        """保存到CSV文件"""
        if not self.records:
            print("没有记录可保存")
            return

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = list(self.records[0].keys())
        with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

        print(f"已保存 {len(self.records)} 条记录到 {OUTPUT_PATH}")

    def print_record(self, record):
        """打印单条记录"""
        print(f"[{record['batch_id']}] {record['production_date']} {record['production_time']} "
              f"| 线:{record['production_line']} 班:{record['shift']} "
              f"| 硬度:{record['rubber_hardness']} 张力:{record['cord_tension']} "
              f"| 质量:{record['quality_score']} 缺陷:{record['defect_type']} "
              f"| {'✓通过' if record['pass_inspection'] else '✗不通过'}")


def main():
    """主函数：逐条生成数据"""
    generator = TireDataGenerator()

    target_count = 500  # 目标生成数量

    print("=" * 80)
    print("开始逐条生成轮胎质量数据")
    print("=" * 80)

    for i in range(target_count):
        record = generator.generate_one_record()

        # 每50条显示一次进度
        if (i + 1) % 50 == 0:
            print(f"\n--- 已生成 {i + 1}/{target_count} 条 ---")
            generator.print_record(record)

    print("\n" + "=" * 80)
    print("生成完成，保存中...")
    generator.save_to_csv()

    # 统计信息
    passed = sum(1 for r in generator.records if r['pass_inspection'] == 1)
    defects = {}
    for r in generator.records:
        d = r['defect_type']
        defects[d] = defects.get(d, 0) + 1

    print(f"\n统计信息:")
    print(f"  总记录数: {len(generator.records)}")
    print(f"  通过率: {passed}/{len(generator.records)} ({passed/len(generator.records)*100:.1f}%)")
    print(f"  缺陷分布: {defects}")


if __name__ == "__main__":
    main()
