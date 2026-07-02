def build_schedule_config(description):
    """Build a scheduler configuration from a Chinese scheduling description."""
    if not isinstance(description, str):
        raise TypeError("description must be a string")
    text = description.strip()
    if not text:
        return {"error": "empty_description"}

    task_type = "collect"
    if "清理缓存" in text:
        task_type = "cleanup_cache"
    elif "日报" in text:
        task_type = "daily_report"

    if "每小时" in text and "9点到下午6点" not in text:
        return {"scheduler": "BlockingScheduler", "trigger": "interval", "params": {"hours": 1}, "task_type": task_type}
    if "凌晨2点" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"hour": 2, "minute": 0}, "task_type": task_type}
    if "30分钟" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "interval", "params": {"minutes": 30}, "task_type": task_type}
    if "每周一" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day_of_week": "mon", "hour": 0, "minute": 0}, "task_type": task_type}
    if "上午9点到下午6点" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"hour": "9-17", "minute": 0}, "task_type": task_type}
    if "每月1号" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day": 1, "hour": 0, "minute": 0}, "task_type": task_type}
    if "工作日" in text and "9:30" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day_of_week": "mon-fri", "hour": 9, "minute": 30}, "task_type": task_type}
    if "每5分钟" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "interval", "params": {"minutes": 5}, "task_type": task_type}
    if "每周日" in text and "凌晨1点" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"day_of_week": "sun", "hour": 1, "minute": 0}, "task_type": task_type}
    if "每天0点" in text:
        return {"scheduler": "BlockingScheduler", "trigger": "cron", "params": {"hour": 0, "minute": 0}, "task_type": task_type}

    return {"error": "unsupported_schedule"}
