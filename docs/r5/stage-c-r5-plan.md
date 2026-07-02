# Stage C R5 项目实训代码关规划

> 日期: 2026-05-02
> 状态: 设计稿。学校真实环境实查显示,当前 BI training schema 尚无可直接挂载 v2 fc / pytest_module 代码关的产品承载层;实施前需要先做 C0 能力层。

## 1. Phase 0 实查结论

- 学校 nginx `/api` 可达: `OPTIONS /api/v1/auth/login` 返回非 `000`。
- Phase 3.2 row count: `20 / 10 / 0`。
- 10 个 PUBLIC BI trainings 均存在,`training_type=DATA_ANALYSIS`。
- `trainings` 表没有 `direction` 字段,真实字段包括 `assignment_nodes`, `superset_dataset_refs`, `training_type`, `handbook_content` 等。
- 当前 training 相关表:
  - `classroom_trainings`
  - `training_datasets`
  - `training_assets`
  - `training_sessions`
  - `training_submissions`
  - `training_learning_logs`
  - `training_environments`
- 当前没有 `training_tasks` / `training_task_tests` / `tasks.training_id`。
- `tasks` + `task_tests` 仍以 `practice_id` 为父级;直接插入 task 无法挂到 BI training 页面。

## 2. R5 总目标

在 10 个项目实训方向中增加真实编程实训关卡,以 v2 `function_call` 和 `pytest_module` 协议评测,并复用 Stage 3 已上线数据集。

建议范围:10 个 BI 方向中选 9 个方向生产代码关,每方向 5 关,共 45 关;如保留 49 关目标,可为风电/光伏/公募基金/企业用能各增加 1 个扩展综合关。

## 3. C0 能力层(实施前置)

R5 不能直接从内容层开始。需要先补一个产品承载层,否则 Browser 闭环无法成立。

### C0.1 数据模型

新增表建议:

```sql
CREATE TABLE training_code_tasks (
  id SERIAL PRIMARY KEY,
  training_id INTEGER NOT NULL REFERENCES trainings(id),
  title VARCHAR(255) NOT NULL,
  order_in_training INTEGER NOT NULL,
  task_type VARCHAR(32) NOT NULL DEFAULT 'CODE',
  env_type VARCHAR(32) DEFAULT 'python3',
  difficulty VARCHAR(32),
  handbook_markdown TEXT,
  starter_code TEXT,
  reference_code TEXT,
  match_rule VARCHAR(64) NOT NULL DEFAULT 'function_call',
  is_published BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE training_code_task_tests (
  id SERIAL PRIMARY KEY,
  training_code_task_id INTEGER NOT NULL REFERENCES training_code_tasks(id) ON DELETE CASCADE,
  case_id VARCHAR(64) NOT NULL,
  input_data TEXT NOT NULL,
  expected_output TEXT NOT NULL,
  is_hidden BOOLEAN NOT NULL DEFAULT false,
  weight INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

也可复用 `tasks/task_tests` 表,但需要增加 `tasks.training_id` 且修改所有 ORM / evaluator / frontend 查询,风险更大。

### C0.2 Backend API

新增 endpoint:

- `GET /api/v1/trainings/{training_id}/code-tasks`
- `GET /api/v1/trainings/{training_id}/code-tasks/{task_id}`
- `GET /api/v1/trainings/{training_id}/code-tasks/{task_id}/tests`
- `POST /api/v1/trainings/{training_id}/code-tasks/{task_id}/evaluate`

评测实现复用 `code_executor.execute_function_call_code` / `execute_pytest_module`,但结果写入新表 `training_code_task_evaluation_results`,避免污染课程实践 TER。

### C0.3 Frontend UI

BI training 详情页 / workspace 增加「编程实训」Tab:

- 左侧: training handbook + 数据集资源
- 中间: code task list,按 `order_in_training` 排序
- 右侧: Monaco editor + 提交按钮 + 评测结果

路径建议:

- `/#/project/:trainingId/code/:taskId`
- 或 `/#/classroom/:classroomId/bi-training/:trainingId/code/:taskId`

### C0.4 Z1 安全

所有 evaluate / submission endpoint 必须:

- `Depends(get_current_user)`
- student 只能提交自己的结果
- teacher/admin 可查看课堂内结果
- classroom training ownership 校验沿用 `add-to-classroom` Z1 模式

## 4. 第 1 方向:风电齿轮箱预警分析(training_id=112)

数据集:

- `fault_log.csv`: 13 行,字段 `fault_id,turbine_id,fault_type,detected_date,repaired_date,severity`
- `scada_readings.csv`: 78,625 行,字段 `timestamp,turbine_id,wind_speed_ms,wind_dir_deg,ambient_temp_c,humidity_pct,active_power_kw,rotor_rpm,gearbox_oil_temp_c,bearing_temp_c,vibration_mms,generator_temp_c,yaw_error_deg,cumulative_kwh,status,anomaly_label`
- `turbine_specs.csv`: 4 行,字段 `turbine_id,rated_power_kw,cut_in_ms,rated_wind_ms,cut_out_ms,rotor_diam_m,hub_height_m,gearbox_model,install_date,location`

### R5-WIND-01: SCADA 数据清洗

函数签名:

```python
def clean_scada_readings(rows: list[dict]) -> list[dict]:
    """返回清洗后的 SCADA 记录列表。"""
```

能力点:

- timestamp 可解析
- 核心数值字段转 float
- 删除 turbine_id / timestamp 缺失行
- 过滤物理不可能值,如负风速、负功率、异常温度
- 按 timestamp + turbine_id 去重并排序

测试策略:12-15 cases,覆盖正常、缺字段、负值、重复、乱序、字符串数值、空输入。

### R5-WIND-02: 故障检测特征工程

函数签名:

```python
def build_fault_features(rows: list[dict], window_size: int = 3) -> list[dict]:
    """按机组生成温度、振动、功率相关的故障特征。"""
```

能力点:

- 按 turbine_id 分组
- 计算 rolling 平均/最大值
- 温度-环境温度差
- 振动阈值 flag
- 异常标签统计

测试策略:12-15 cases,覆盖单机组、多机组、窗口边界、空组、异常输入。

### R5-WIND-03: 预测模型评估

函数签名:

```python
def evaluate_fault_predictions(y_true: list[int], y_score: list[float], threshold: float = 0.5) -> dict:
    """返回故障预警分类指标。"""
```

能力点:

- precision / recall / f1
- false_alarm_rate
- missed_alarm_rate
- confusion matrix
- threshold 边界

测试策略:12-15 cases,覆盖完美预测、全负、全正、阈值变化、长度不一致。

### R5-WIND-04: 维护规划优化

函数签名:

```python
def plan_maintenance(alerts: list[dict], specs: list[dict], max_daily_tasks: int = 2) -> list[dict]:
    """根据告警严重度和机组信息生成维护排期。"""
```

能力点:

- severity 排序
- 同日任务上限
- 按 turbine_id 合并重复告警
- 高风险优先
- 输出稳定排序

测试策略:12-15 cases,覆盖容量限制、重复告警、未知机组、空输入、severity 平级排序。

### R5-WIND-05: 综合项目 pytest_module

模块名建议:`student_wind05.py`

测试模块:`test_wind05_warning_system.py`

学生需实现:

- `load_and_clean_scada`
- `build_health_features`
- `score_fault_risk`
- `generate_maintenance_plan`
- `summarize_warning_report`

测试规模:28-35 cases。攻击要求:stub 100% fail, hardcode / shape-only / identity 均 ≥70% fail。

## 5. 单关红绿 TDD 标准

每关入库前必须输出:

- 攻击表:stub / hardcode / shape-only / identity / ref
- 红线表:每函数至少 3 输入、边界、负例、浮点 tolerance、dict/list 全字段断言
- 学校 C2-B stub/ref 实证
- Browser Use 真实 workspace 显示与提交结果

## 6. 当前阻塞判断

内容设计可继续,但**不能直接入库为可验收 R5 关卡**,因为现有产品没有 training code task 承载层。若绕过 C0 直接创建 `practice` 或复用已下架 XQ01 模式,会改变 Phase 3.2 `20/10/0` 口径,且不属于 training 页面闭环。

建议下一步:

1. Jim 审 C0 能力层方案。
2. 先做 C0 最小闭环:1 个 training code task 表 + 1 个 evaluate endpoint + 1 个 frontend code tab。
3. 用 WIND-01 作为模板关做端到端验证。
4. C0 通过后再批量生产 WIND-02~05。
