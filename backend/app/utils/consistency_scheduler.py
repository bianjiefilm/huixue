"""
数据一致性定时检查调度器
定期运行一致性检查并生成报告
"""
import asyncio
import logging
from datetime import datetime, timedelta
import schedule
import time
import threading
from typing import Dict, Any, Optional

from app.utils.consistency_monitor import get_consistency_monitor
from app.core.config import settings

logger = logging.getLogger(__name__)

class ConsistencyScheduler:
    """数据一致性定时调度器"""

    def __init__(self):
        self.monitor = get_consistency_monitor()
        self.is_running = False
        self.check_interval_minutes = getattr(settings, 'CONSISTENCY_CHECK_INTERVAL', 30)  # 默认30分钟
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """启动定时调度器"""
        if self.is_running:
            logger.warning("一致性调度器已在运行")
            return

        logger.info(f"启动数据一致性定时调度器，检查间隔: {self.check_interval_minutes}分钟")

        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

    def stop(self):
        """停止定时调度器"""
        logger.info("停止数据一致性定时调度器")
        self.is_running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

    def _run_scheduler(self):
        """运行调度器主循环"""
        # 设置定时任务
        schedule.every(self.check_interval_minutes).minutes.do(self._run_check)

        # 立即运行一次
        self._run_check()

        # 主循环
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次是否有待执行的任务
            except Exception as e:
                logger.error(f"调度器运行出错: {e}")
                time.sleep(300)  # 出错后等待5分钟再试

    def _run_check(self):
        """执行一致性检查"""
        try:
            logger.info("开始定时一致性检查...")

            start_time = time.time()
            results = self.monitor.run_full_check()
            duration = time.time() - start_time

            # 记录检查结果
            self._log_check_results(results, duration)

            # 根据结果执行相应动作
            self._handle_check_results(results)

        except Exception as e:
            logger.error(f"定时一致性检查执行失败: {e}")

    def _log_check_results(self, results: Dict[str, Any], duration: float):
        """记录检查结果"""
        health_score = results.get("summary", {}).get("health_score", 0)
        total_issues = results.get("summary", {}).get("total_issues", 0)
        auto_fixed = results.get("summary", {}).get("auto_fixed", 0)

        log_level = logging.INFO
        if health_score < 70:
            log_level = logging.WARNING
        elif health_score < 50:
            log_level = logging.ERROR

        logger.log(log_level,
            f"一致性检查完成 - 健康评分: {health_score}, "
            f"发现问题: {total_issues}, 自动修复: {auto_fixed}, "
            f"耗时: {duration:.2f}秒"
        )

        # 存储结果用于监控
        setattr(self.monitor, '_last_check_time', datetime.now())
        setattr(self.monitor, '_last_health_score', health_score)
        setattr(self.monitor, '_last_check_results', results)

    def _handle_check_results(self, results: Dict[str, Any]):
        """处理检查结果"""
        health_score = results.get("summary", {}).get("health_score", 0)
        total_issues = results.get("summary", {}).get("total_issues", 0)

        # 如果健康评分低于60，发送告警
        if health_score < 60:
            self._send_alert(results)

        # 如果发现太多问题，执行紧急修复
        if total_issues > 10:
            logger.warning(f"发现 {total_issues} 个一致性问题，执行紧急修复")
            self._emergency_fix()

    def _send_alert(self, results: Dict[str, Any]):
        """发送告警通知"""
        try:
            # 这里可以集成邮件、微信、钉钉等告警通知
            # 暂时只记录日志
            logger.warning("数据一致性健康评分过低，请检查系统状态")
            logger.warning(f"详细结果: {results}")

            # TODO: 实现实际的告警通知机制

        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")

    def _emergency_fix(self):
        """执行紧急修复"""
        try:
            logger.info("开始执行紧急一致性修复...")

            # 清理所有缓存，强制重新加载
            self.monitor.cache.invalidate_user_practices(None)  # 清理所有用户缓存

            logger.info("紧急一致性修复完成")

        except Exception as e:
            logger.error(f"紧急修复执行失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "check_interval_minutes": self.check_interval_minutes,
            "next_check_time": self._get_next_check_time(),
            "last_health_score": getattr(self.monitor, '_last_health_score', 0),
            "last_check_time": getattr(self.monitor, '_last_check_time', None)
        }

    def _get_next_check_time(self) -> Optional[datetime]:
        """获取下次检查时间"""
        try:
            # 计算下次执行时间
            now = datetime.now()
            interval_minutes = self.check_interval_minutes
            next_check = now + timedelta(minutes=interval_minutes)
            return next_check
        except Exception:
            return None

    def manual_check(self) -> Dict[str, Any]:
        """手动执行一致性检查"""
        logger.info("执行手动一致性检查...")
        results = self.monitor.run_full_check()
        self._log_check_results(results, 0)
        return results

# 全局调度器实例
consistency_scheduler = ConsistencyScheduler()

def get_consistency_scheduler() -> ConsistencyScheduler:
    """获取一致性调度器实例"""
    return consistency_scheduler

def start_consistency_monitoring():
    """启动数据一致性监控"""
    scheduler = get_consistency_scheduler()
    scheduler.start()
    logger.info("数据一致性监控服务已启动")

def stop_consistency_monitoring():
    """停止数据一致性监控"""
    scheduler = get_consistency_scheduler()
    scheduler.stop()
    logger.info("数据一致性监控服务已停止")

# 如果直接运行此脚本，启动监控服务
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("启动数据一致性监控服务...")
    start_consistency_monitoring()

    try:
        # 保持运行
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
        stop_consistency_monitoring()
        logger.info("数据一致性监控服务已关闭")

