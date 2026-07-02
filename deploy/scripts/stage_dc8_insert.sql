-- DC8: 定时任务调度
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 8;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    '定时任务调度',
    'PRACTICE',
    8,
    'intermediate',
    $dc8$# 定时任务调度学习手册

## 一、任务类型

在日常开发中，很多场景需要自动执行任务：定时采集数据、定时生成报表、定时清理缓存等。本手册以「定时采集系统」为例，讲解如何用 APScheduler 和 crontab 实现定时任务。

## 二、学习环境

```bash
pip install apscheduler
```

APScheduler 是 Python 中最流行的定时任务库，支持 BlockingScheduler（阻塞式）和 AsyncIOScheduler（非阻塞式）两种调度器。

## 三、知识点讲解

### 1. APScheduler 基础

APScheduler 有三种调度器：
- `BlockingScheduler`：适用于命令行脚本，阻塞当前进程。
- `AsyncIOScheduler`：适用于 asyncio 项目，集成到事件循环中。
- `BackgroundScheduler`：在后台线程中运行，不阻塞主线程。

```python
# BlockingScheduler 示例
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

def job():
    print(f"[{datetime.now()}] 任务执行中...")

scheduler = BlockingScheduler()
scheduler.add_job(job, 'interval', seconds=10)
scheduler.start()
```

```python
# AsyncIOScheduler 示例
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

async def async_job():
    print("异步任务执行中")

scheduler = AsyncIOScheduler()
scheduler.add_job(async_job, IntervalTrigger(seconds=30))
scheduler.start()
asyncio.get_event_loop().run_forever()
```

### 2. 触发器类型

APScheduler 支持三种触发器：

| 触发器 | 说明 | 典型场景 |
|--------|------|----------|
| `date` | 一次性任务，在指定时间执行一次 | 延迟执行、一次性通知 |
| `interval` | 周期执行，固定间隔重复 | 每分钟检查、每10秒采集 |
| `cron` | 定时执行，crontab 风格 | 每天8点生成报表、每周一统计 |

```python
# date 触发器 - 一次性任务
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta

scheduler.add_job(
    job,
    DateTrigger(run_date=datetime.now() + timedelta(minutes=5))
)
```

```python
# interval 触发器 - 周期任务
from apscheduler.triggers.interval import IntervalTrigger

scheduler.add_job(
    job,
    IntervalTrigger(hours=1)  # 每小时执行
)

scheduler.add_job(
    job,
    IntervalTrigger(hours=1, minutes=30)  # 每1小时30分钟执行
)
```

### 3. cron 表达式

cron 表达式有 5 个字段，格式为：

```
分(0-59)  时(0-23)  日(1-31)  月(1-12)  周(0-6, 0=周日)
```

常用示例：

| 表达式 | 含义 |
|--------|------|
| `0 8 * * *` | 每天 8:00 |
| `30 9 * * 1-5` | 工作日 9:30 |
| `0 */2 * * *` | 每 2 小时 |
| `0 0 1 * *` | 每月 1 日 0:00 |
| `0 0 * * 0` | 每周日 0:00 |

```python
from apscheduler.triggers.cron import CronTrigger

# 每天早上8点执行
scheduler.add_job(
    job,
    CronTrigger(hour=8, minute=0)
)

# 工作日上午9:30执行
scheduler.add_job(
    job,
    CronTrigger(hour=9, minute=30, day_of_week='mon-fri')
)

# 每月1号凌晨执行
scheduler.add_job(
    job,
    CronTrigger(day=1, hour=0, minute=0)
)
```

### 4. 任务管理

```python
# 添加任务
job = scheduler.add_job(job_func, 'interval', seconds=60, id='my_job')

# 移除任务
scheduler.remove_job('my_job')

# 重新调度任务
scheduler.reschedule_job('my_job', trigger='cron', hour=9, minute=30)

# 暂停/恢复任务
scheduler.pause_job('my_job')
scheduler.resume_job('my_job')

# 查看所有任务
for job in scheduler.get_jobs():
    print(f"ID: {job.id}, Next run: {job.next_run_time}")
```

### 5. crontab 命令

crontab 是 Linux 系统级的定时任务工具：

```bash
# 编辑 crontab
crontab -e
# 分 时 日 月 周 命令
# 0 8 * * * /usr/bin/python3 /opt/backup.py

# 查看 crontab
crontab -l

# 删除所有 crontab
crontab -r
```

crontab 特殊字符：
- `*` 任意值
- `,` 列表，如 `1,15`
- `-` 范围，如 `1-5`
- `/` 步长，如 `*/5` 表示每5个单位

## 四、实战代码：完整定时采集示例

```python
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模拟数据采集函数
def collect_data():
    """每小时数据采集任务"""
    logger.info(f"[{datetime.now()}] 开始采集数据...")
    # 实际场景：调用 API、读取文件、查询数据库等
    logger.info(f"[{datetime.now()}] 数据采集完成")

def generate_report():
    """每天生成日报"""
    logger.info(f"[{datetime.now()}] 生成日报...")

def cleanup_cache():
    """每周清理缓存"""
    logger.info(f"[{datetime.now()}] 清理缓存...")

# 配置持久化
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}
executors = {
    'default': ThreadPoolExecutor(10)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

# 创建调度器
scheduler = BlockingScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

# 添加任务
# 每小时采集数据
scheduler.add_job(
    collect_data,
    IntervalTrigger(hours=1),
    id='hourly_collect',
    replace_existing=True,
    misfire_grace_time=3600  # 允许1小时延迟
)

# 每天早上8点生成日报
scheduler.add_job(
    generate_report,
    CronTrigger(hour=8, minute=0),
    id='daily_report',
    replace_existing=True
)

# 每周一凌晨2点清理缓存
scheduler.add_job(
    cleanup_cache,
    CronTrigger(day_of_week='mon', hour=2, minute=0),
    id='weekly_cleanup',
    replace_existing=True
)

if __name__ == '__main__':
    logger.info("调度器启动...")
    logger.info("查看所有任务:")
    for job in scheduler.get_jobs():
        print(f"  - {job.id}: 下次执行 {job.next_run_time}")
    scheduler.start()
```

## 五、crontab 进阶

### 特殊字符详解

| 字符 | 含义 | 示例 |
|------|------|------|
| `*` | 任意值 | `* * * * *` 每一分钟 |
| `,` | 列表分隔 | `0,30 * * * *` 每半小时 |
| `-` | 范围 | `9-17 * * *` 9点到17点每小时 |
| `/` | 步长 | `*/15 * * * *` 每15分钟 |

### 常用 crontab 示例

```bash
# 每分钟执行
* * * * * /path/to/script.sh

# 每小时执行
0 * * * * /path/to/script.sh

# 每天凌晨2点
0 2 * * * /path/to/script.sh

# 每周一凌晨2点
0 2 * * 1 /path/to/script.sh

# 每月1号凌晨2点
0 2 1 * * /path/to/script.sh

# 每5分钟执行
*/5 * * * * /path/to/script.sh

# 工作日上午9点到下午6点每30分钟
*/30 9-18 * * 1-5 /path/to/script.sh
```

### 异常与重试配置

APScheduler 任务异常处理关键参数：

```python
job_defaults = {
    'misfire_grace_time': 3600,   # 错过触发时间后1小时内仍执行
    'coalesce': False,             # 合并错过的多次执行为一次
    'max_instances': 3            # 同一任务最多同时运行3个实例
}

scheduler = BlockingScheduler(job_defaults=job_defaults)
```

## 六、任务持久化

### SQLite 持久化

```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///scheduler.db')
}
scheduler = BlockingScheduler(jobstores=jobstores)
```

### Redis 持久化

```python
from apscheduler.jobstores.redis import RedisJobStore

jobstores = {
    'default': RedisJobStore(host='localhost', port=6379, db=0)
}
scheduler = BlockingScheduler(jobstores=jobstores)
```

## 七、总结

| 工具 | 适用场景 | 优点 |
|------|----------|------|
| APScheduler | Python 应用内调度 | 编程控制、持久化、重试 |
| crontab | Linux 系统级任务 | 简单、系统管理 |

实际项目中，小型脚本可用 crontab，大型应用推荐 APScheduler 结合持久化存储。
$dc8$,
    $dc8${"questions": [{"id": "q_mc_01", "type": "multiple_choice", "question": "APScheduler 中，以下哪个调度器适用于 asyncio 项目？", "options": ["A) BlockingScheduler", "B) AsyncIOScheduler", "C) ThreadScheduler", "D) BackgroundScheduler"], "answer": "B", "explanation": "AsyncIOScheduler 专门为 asyncio 项目设计，可集成到事件循环中。BlockingScheduler 适用于命令行脚本阻塞模式，BackgroundScheduler 在后台线程运行。"}, {"id": "q_mc_02", "type": "multiple_choice", "question": "APScheduler 的 DateTrigger 用于什么场景？", "options": ["A) 周期执行任务", "B) cron 风格定时执行", "C) 一次性任务，在指定时间执行一次", "D) 每秒执行任务"], "answer": "C", "explanation": "DateTrigger 是 date 触发器，用于一次性任务，指定时间执行一次后不再重复。interval 用于周期执行，cron 用于定时执行。"}, {"id": "q_mc_03", "type": "multiple_choice", "question": "cron 表达式 `0 */2 * * *` 的含义是？", "options": ["A) 每分钟执行", "B) 每2分钟执行", "C) 每2小时执行", "D) 每天凌晨2点执行"], "answer": "C", "explanation": "五字段格式为 分(0-59) 时(0-23) 日(1-31) 月(1-12) 周(0-6)。`*/2` 表示每2个单位，即每2小时执行一次。"}, {"id": "q_mc_04", "type": "multiple_choice", "question": "以下哪个 crontab 命令可以查看当前用户的定时任务？", "options": ["A) crontab -e", "B) crontab -l", "C) crontab -r", "D) crontab -v"], "answer": "B", "explanation": "crontab -e 编辑，crontab -l 列出（list），crontab -r 删除（remove）。"}, {"id": "q_mc_05", "type": "multiple_choice", "question": "在 APScheduler 中，misfire_grace_time 参数的作用是？", "options": ["A) 控制任务并发实例数", "B) 允许错过触发时间后延迟执行", "C) 合并多次错过的执行为一次", "D) 设置任务超时时间"], "answer": "B", "explanation": "misfire_grace_time 指定当任务错过预定触发时间后，仍可在多少秒内执行。coalesce 控制是否合并错过的执行，max_instances 控制并发数。"}, {"id": "q_mc_06", "type": "multiple_choice", "question": "使用 BlockingScheduler 添加一个每30分钟执行一次的任务，正确的方式是？", "options": ["A) scheduler.add_job(job, 'interval', minutes=30)", "B) scheduler.add_job(job, 'cron', minute=30)", "C) scheduler.add_job(job, 'date', minutes=30)", "D) scheduler.add_job(job, 'interval', hours=0.5)"], "answer": "A", "explanation": "interval 触发器支持 minutes=30 参数。cron 的 minute=30 只在每小时的第30分钟执行，不是每30分钟。hour=0.5 不是 interval 支持的格式。"}, {"id": "q_mc_07", "type": "multiple_choice", "question": "APScheduler 支持以下哪些持久化存储？", "options": ["A) SQLite", "B) Redis", "C) MongoDB", "D) 以上全部"], "answer": "D", "explanation": "APScheduler 内置支持 SQLAlchemy（支持 SQLite、PostgreSQL、MySQL 等）和 Redis 作为 jobstore，也支持自定义 jobstore。"}, {"id": "q_mc_08", "type": "multiple_choice", "question": "crontab 表达式 `0 9-17 * * 1-5` 表示什么？", "options": ["A) 每天9点到17点每小时执行", "B) 工作日上午9点到下午5点每小时执行", "C) 每月1日到5日9点执行", "D) 每周一到周五9点到17点执行"], "answer": "B", "explanation": "分=0，时=9-17（9点到17点），日=*，月=*，周=1-5（周一到周五）。即工作日上午9点到下午5点每小时执行。"}, {"id": "q_prog_01", "type": "programming", "question": "请编写代码，使用 APScheduler 的 BlockingScheduler 实现以下定时任务：\n\n1. 创建一个 BlockingScheduler 实例\n2. 定义一个函数 `hourly_task`，打印 \"Hourly task executed\"\n3. 使用 `add_job` 添加该任务，触发器类型为 `interval`，每 10 分钟执行一次\n4. 任务 ID 为 `hourly_job`\n\n返回 scheduler 对象（不需要启动）。", "starter_code": "from apscheduler.schedulers.blocking import BlockingScheduler\n\ndef hourly_task():\n    print(\"Hourly task executed\")\n\n# 请完成下面的代码\nscheduler = None  # TODO: 创建 BlockingScheduler 实例\n# TODO: 使用 add_job 添加任务\n", "answer_code": "from apscheduler.schedulers.blocking import BlockingScheduler\n\ndef hourly_task():\n    print(\"Hourly task executed\")\n\nscheduler = BlockingScheduler()\nscheduler.add_job(hourly_task, 'interval', minutes=10, id='hourly_job')\n", "test_cases": [{"id": "tc_prog_01_01", "input": "启动 scheduler 后等待 15 秒检查任务执行情况", "expected": "任务在 0s, 10s 时各执行一次，next_run_time 显示下一次执行在约 10 秒后", "hidden": false}, {"id": "tc_prog_01_02", "input": "检查任务 ID", "expected": "scheduler.get_job('hourly_job') 返回该任务", "hidden": false}, {"id": "tc_prog_01_03", "input": "移除任务后再次检查", "expected": "scheduler.get_job('hourly_job') 返回 None", "hidden": true}, {"id": "tc_prog_01_04", "input": "重新调度任务为每5分钟执行", "expected": "scheduler.reschedule_job('hourly_job', trigger='interval', minutes=5) 成功", "hidden": true}]}, {"id": "q_prog_02", "type": "programming", "question": "请编写代码，实现以下定时任务调度：\n\n1. 创建一个 BlockingScheduler 实例\n2. 定义一个函数 `daily_report`，打印 \"Daily report generated\"\n3. 使用 CronTrigger 添加任务：\n   - 每天早上 8 点执行\n   - 任务 ID 为 `daily_report_job`\n4. 再添加一个任务 `weekly_backup`：\n   - 使用 cron 表达式配置\n   - 每周一凌晨 2 点执行\n   - 任务 ID 为 `weekly_backup_job`\n\n返回 scheduler 对象。", "starter_code": "from apscheduler.schedulers.blocking import BlockingScheduler\nfrom apscheduler.triggers.cron import CronTrigger\n\ndef daily_report():\n    print(\"Daily report generated\")\n\ndef weekly_backup():\n    print(\"Weekly backup executed\")\n\n# 请完成下面的代码\nscheduler = None  # TODO\n", "answer_code": "from apscheduler.schedulers.blocking import BlockingScheduler\nfrom apscheduler.triggers.cron import CronTrigger\n\ndef daily_report():\n    print(\"Daily report generated\")\n\ndef weekly_backup():\n    print(\"Weekly backup executed\")\n\nscheduler = BlockingScheduler()\nscheduler.add_job(daily_report, CronTrigger(hour=8, minute=0), id='daily_report_job')\nscheduler.add_job(weekly_backup, CronTrigger(day_of_week='mon', hour=2, minute=0), id='weekly_backup_job')\n", "test_cases": [{"id": "tc_prog_02_01", "input": "检查 daily_report_job 任务", "expected": "scheduler.get_job('daily_report_job') 不为 None", "hidden": false}, {"id": "tc_prog_02_02", "input": "检查 weekly_backup_job 任务", "expected": "scheduler.get_job('weekly_backup_job') 不为 None", "hidden": false}, {"id": "tc_prog_02_03", "input": "列出所有任务", "expected": "get_jobs() 返回包含两个任务的列表", "hidden": true}, {"id": "tc_prog_02_04", "input": "移除 daily_report_job 后检查", "expected": "只剩 weekly_backup_job 一个任务", "hidden": true}, {"id": "tc_prog_02_05", "input": "获取任务下次执行时间", "expected": "daily_report_job.next_run_time 显示约在次日 8:00", "hidden": true}, {"id": "tc_prog_02_06", "input": "配置 misfire_grace_time=3600 后重新添加", "expected": "任务可以容忍错过触发后1小时内执行", "hidden": true}]}], "baseline_code": "import datetime\nfrom apscheduler.schedulers.blocking import BlockingScheduler\nfrom apscheduler.triggers.interval import IntervalTrigger\nfrom apscheduler.triggers.cron import CronTrigger\n\ndef scheduled_collection():\n    \"\"\"定时采集任务 - 需实现\"\"\"\n    pass\n\n# 任务1: 使用 interval 触发器，每小时执行一次\nscheduler = BlockingScheduler()\n# TODO: 使用 scheduler.add_job() 添加定时任务\n# scheduler.add_job(...)\n\n# 任务2: 使用 cron 触发器，每天凌晨2点执行\n# scheduler.add_job(...)"}$dc8$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 8;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, 'tc1', $dc8$"配置每小时执行一次采集任务"$dc8$, $dc8$"BlockingScheduler with interval(hours=1)"$dc8$, False, '', 'CONTAINS', 1),
    (new_task_id, 'tc2', $dc8$"配置每天凌晨2点执行采集任务"$dc8$, $dc8$"BlockingScheduler with cron trigger at hour=2"$dc8$, False, '', 'CONTAINS', 2),
    (new_task_id, 'tc3', $dc8$"配置每30分钟执行一次"$dc8$, $dc8$"BlockingScheduler with interval(minutes=30)"$dc8$, True, '', 'CONTAINS', 3),
    (new_task_id, 'tc4', $dc8$"配置每周一凌晨执行"$dc8$, $dc8$"BlockingScheduler with cron day_of_week='mon'"$dc8$, True, '', 'CONTAINS', 4),
    (new_task_id, 'tc5', $dc8$"配置每天上午9点到下午6点每小时执行"$dc8$, $dc8$"BlockingScheduler with cron hour='9-17'"$dc8$, True, '', 'CONTAINS', 5),
    (new_task_id, 'tc6', $dc8$"配置每月1号凌晨执行"$dc8$, $dc8$"BlockingScheduler with cron day=1"$dc8$, True, '', 'CONTAINS', 6),
    (new_task_id, 'tc7', $dc8$"配置工作日上午9:30执行"$dc8$, $dc8$"BlockingScheduler with cron hour=9, minute=30, day_of_week='mon-fri'"$dc8$, True, '', 'CONTAINS', 7),
    (new_task_id, 'tc8', $dc8$"配置每5分钟执行一次采集"$dc8$, $dc8$"BlockingScheduler with interval(minutes=5)"$dc8$, True, '', 'CONTAINS', 8),
    (new_task_id, 'tc9', $dc8$"配置每周日凌晨1点清理缓存"$dc8$, $dc8$"BlockingScheduler with cron day_of_week='sun', hour=1"$dc8$, True, '', 'CONTAINS', 9),
    (new_task_id, 'tc10', $dc8$"配置每天0点执行日报生成"$dc8$, $dc8$"BlockingScheduler with cron hour=0, minute=0"$dc8$, True, '', 'CONTAINS', 10),
    (new_task_id, 'tc_prog_01_01', $dc8$"启动 scheduler 后等待 15 秒检查任务执行情况"$dc8$, $dc8$"任务在 0s, 10s 时各执行一次，next_run_time 显示下一次执行在约 10 秒后"$dc8$, False, '', 'CONTAINS', 11),
    (new_task_id, 'tc_prog_01_02', $dc8$"检查任务 ID"$dc8$, $dc8$"scheduler.get_job('hourly_job') 返回该任务"$dc8$, False, '', 'CONTAINS', 12),
    (new_task_id, 'tc_prog_01_03', $dc8$"移除任务后再次检查"$dc8$, $dc8$"scheduler.get_job('hourly_job') 返回 None"$dc8$, True, '', 'CONTAINS', 13),
    (new_task_id, 'tc_prog_01_04', $dc8$"重新调度任务为每5分钟执行"$dc8$, $dc8$"scheduler.reschedule_job('hourly_job', trigger='interval', minutes=5) 成功"$dc8$, True, '', 'CONTAINS', 14),
    (new_task_id, 'tc_prog_02_01', $dc8$"检查 daily_report_job 任务"$dc8$, $dc8$"scheduler.get_job('daily_report_job') 不为 None"$dc8$, False, '', 'CONTAINS', 15),
    (new_task_id, 'tc_prog_02_02', $dc8$"检查 weekly_backup_job 任务"$dc8$, $dc8$"scheduler.get_job('weekly_backup_job') 不为 None"$dc8$, False, '', 'CONTAINS', 16),
    (new_task_id, 'tc_prog_02_03', $dc8$"列出所有任务"$dc8$, $dc8$"get_jobs() 返回包含两个任务的列表"$dc8$, True, '', 'CONTAINS', 17),
    (new_task_id, 'tc_prog_02_04', $dc8$"移除 daily_report_job 后检查"$dc8$, $dc8$"只剩 weekly_backup_job 一个任务"$dc8$, True, '', 'CONTAINS', 18),
    (new_task_id, 'tc_prog_02_05', $dc8$"获取任务下次执行时间"$dc8$, $dc8$"daily_report_job.next_run_time 显示约在次日 8:00"$dc8$, True, '', 'CONTAINS', 19),
    (new_task_id, 'tc_prog_02_06', $dc8$"配置 misfire_grace_time=3600 后重新添加"$dc8$, $dc8$"任务可以容忍错过触发后1小时内执行"$dc8$, True, '', 'CONTAINS', 20);
END $$;