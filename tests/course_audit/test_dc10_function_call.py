import importlib
import os

import pytest


def _student():
    return importlib.import_module(os.environ.get("DC10_MODULE", "content_orchestrator.stages_config.data_collection.student_dc10"))


CASES = [
    ("配置每小时执行一次采集任务", {"scheduler": "BlockingScheduler", "trigger": "interval", "params": {"hours": 1}, "task_type": "collect"}),
    ("配置每天凌晨2点执行采集任务", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"hour": 2, "minute": 0}, "task_type": "collect"}),
    ("配置每30分钟执行一次", {"scheduler": "BlockingScheduler", "trigger": "interval", "params": {"minutes": 30}, "task_type": "collect"}),
    ("配置每周一凌晨执行", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day_of_week": "mon", "hour": 0, "minute": 0}, "task_type": "collect"}),
    ("配置每天上午9点到下午6点每小时执行", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"hour": "9-17", "minute": 0}, "task_type": "collect"}),
    ("配置每月1号凌晨执行", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day": 1, "hour": 0, "minute": 0}, "task_type": "collect"}),
    ("配置工作日上午9:30执行", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day_of_week": "mon-fri", "hour": 9, "minute": 30}, "task_type": "collect"}),
    ("配置每5分钟执行一次采集", {"scheduler": "BlockingScheduler", "trigger": "interval", "params": {"minutes": 5}, "task_type": "collect"}),
    ("配置每周日凌晨1点清理缓存", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day_of_week": "sun", "hour": 1, "minute": 0}, "task_type": "cleanup_cache"}),
    ("配置每天0点执行日报生成", {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"hour": 0, "minute": 0}, "task_type": "daily_report"}),
    ("暂不支持的调度规则", {"error": "unsupported_schedule"}),
    ("", {"error": "empty_description"}),
]


@pytest.mark.parametrize(("description", "expected"), CASES)
def test_build_schedule_config(description, expected):
    assert _student().build_schedule_config(description) == expected


def test_rejects_non_string_description():
    with pytest.raises(TypeError):
        _student().build_schedule_config(None)
