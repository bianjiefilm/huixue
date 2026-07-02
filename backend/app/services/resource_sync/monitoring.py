"""
监控和日志系统
"""
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from logging.handlers import RotatingFileHandler

from .models import HealthStatus, SyncResult


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics = {}
        self.logger = logging.getLogger(__name__)

    def record_operation(self, operation: str, resource_type: str,
                        duration: float, success: bool):
        """记录操作指标"""
        key = f"sync_{operation}_{resource_type}"

        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'success_count': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'last_success': None,
                'last_failure': None,
                'min_duration': float('inf'),
                'max_duration': 0
            }

        metric = self.metrics[key]
        metric['count'] += 1
        metric['total_duration'] += duration
        metric['avg_duration'] = metric['total_duration'] / metric['count']
        metric['min_duration'] = min(metric['min_duration'], duration)
        metric['max_duration'] = max(metric['max_duration'], duration)

        if success:
            metric['success_count'] += 1
            metric['last_success'] = datetime.now()
        else:
            metric['last_failure'] = datetime.now()

    def get_operation_stats(self, operation: str, resource_type: str) -> Dict[str, Any]:
        """获取操作统计"""
        key = f"sync_{operation}_{resource_type}"
        return self.metrics.get(key, {})

    def get_health_status(self) -> HealthStatus:
        """获取整体健康状态"""
        if not self.metrics:
            return HealthStatus(
                overall_health='unknown',
                success_rate=0.0,
                total_operations=0
            )

        total_operations = sum(m['count'] for m in self.metrics.values())
        successful_operations = sum(m['success_count'] for m in self.metrics.values())

        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        # 确定健康状态
        if success_rate >= 0.95:
            overall_health = 'healthy'
        elif success_rate >= 0.8:
            overall_health = 'warning'
        else:
            overall_health = 'critical'

        # 获取最后同步时间
        last_sync_time = None
        for metric in self.metrics.values():
            if metric.get('last_success'):
                if last_sync_time is None or metric['last_success'] > last_sync_time:
                    last_sync_time = metric['last_success']

        return HealthStatus(
            overall_health=overall_health,
            success_rate=success_rate,
            total_operations=total_operations,
            last_sync_time=last_sync_time,
            details=self.metrics
        )

    def reset(self):
        """重置指标"""
        self.metrics.clear()


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_path: str = "logs/resource_sync_audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # 设置审计日志记录器
        self.logger = logging.getLogger('resource_sync_audit')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()  # 清除现有处理器

        # 创建轮转文件处理器
        handler = RotatingFileHandler(
            self.log_path,
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10,
            encoding='utf-8'
        )

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # 避免重复记录
        self.logger.propagate = False

    def log_sync_operation(self, operation: str, resource_id: str,
                          user: str, details: Dict[str, Any]):
        """记录同步操作审计日志"""
        message = (
            f"SYNC_OPERATION: operation={operation}, "
            f"resource_id={resource_id}, user={user}, "
            f"details={details}"
        )
        self.logger.info(message)

    def log_sync_result(self, result: SyncResult, user: str):
        """记录同步结果"""
        details = {
            'total_actions': result.total_actions,
            'successful_actions': result.successful_actions,
            'failed_actions': result.failed_actions,
            'duration': (result.completed_at - result.started_at).total_seconds() if result.completed_at else None,
            'success': result.success
        }

        if result.errors:
            details['error_count'] = len(result.errors)
            details['first_error'] = result.errors[0]['error'] if result.errors else None

        self.log_sync_operation('batch_sync', 'all', user, details)

    def log_security_event(self, event_type: str, resource_id: str,
                          user: str, details: Dict[str, Any]):
        """记录安全事件"""
        message = (
            f"SECURITY_EVENT: type={event_type}, "
            f"resource_id={resource_id}, user={user}, "
            f"details={details}"
        )
        self.logger.warning(message)

    def log_file_operation(self, operation: str, resource_id: str,
                          file_path: str, user: str):
        """记录文件操作"""
        details = {
            'file_path': file_path,
            'operation': operation
        }
        self.log_sync_operation('file_operation', resource_id, user, details)


@contextmanager
def performance_monitor(operation_name: str, metrics_collector: MetricsCollector):
    """性能监控上下文管理器"""
    start_time = time.time()
    success = False

    try:
        yield
        success = True
    finally:
        duration = time.time() - start_time
        # 这里需要从上下文获取资源类型，暂时使用通用类型
        metrics_collector.record_operation(operation_name, 'resource', duration, success)


class AlertManager:
    """告警管理器"""

    def __init__(self, alert_thresholds: Optional[Dict[str, Any]] = None):
        self.alert_thresholds = alert_thresholds or {
            'max_failure_rate': 0.1,  # 最大失败率10%
            'max_sync_duration': 3600,  # 最长同步时间1小时
            'min_success_rate': 0.8,  # 最低成功率80%
        }
        self.logger = logging.getLogger(__name__)
        self.alerts = []

    def check_and_alert(self, sync_result: SyncResult, health_status: HealthStatus):
        """检查并发出告警"""
        alerts = []

        # 检查失败率
        failure_rate = sync_result.failed_actions / sync_result.total_actions if sync_result.total_actions > 0 else 0
        if failure_rate > self.alert_thresholds['max_failure_rate']:
            alerts.append({
                'level': 'critical',
                'message': f'同步失败率过高: {failure_rate:.2%} (阈值: {self.alert_thresholds["max_failure_rate"]:.2%})',
                'details': {
                    'failure_rate': failure_rate,
                    'failed_actions': sync_result.failed_actions,
                    'total_actions': sync_result.total_actions
                }
            })

        # 检查同步时长
        if sync_result.completed_at and sync_result.started_at:
            duration = (sync_result.completed_at - sync_result.started_at).total_seconds()
            if duration > self.alert_thresholds['max_sync_duration']:
                alerts.append({
                    'level': 'warning',
                    'message': f'同步耗时过长: {duration:.2f}秒 (阈值: {self.alert_thresholds["max_sync_duration"]}秒)',
                    'details': {'duration': duration}
                })

        # 检查整体健康状态
        if health_status.overall_health == 'critical':
            alerts.append({
                'level': 'critical',
                'message': f'系统健康状态异常: {health_status.overall_health}',
                'details': {
                    'success_rate': health_status.success_rate,
                    'total_operations': health_status.total_operations
                }
            })

        # 记录告警
        for alert in alerts:
            self.logger.warning(f"告警触发: {alert['message']}")
            self.alerts.append({
                **alert,
                'timestamp': datetime.now()
            })

        return alerts

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if alert['timestamp'] > cutoff_time
        ]


class ResourceSyncMonitor:
    """资源同步监控器"""

    def __init__(self, log_path: str = "logs/resource_sync_audit.log"):
        self.metrics = MetricsCollector()
        self.audit_logger = AuditLogger(log_path)
        self.alert_manager = AlertManager()
        self.logger = logging.getLogger(__name__)

    def record_sync_attempt(self, operation: str, resource_type: str = 'resource'):
        """记录同步尝试"""
        return performance_monitor(operation, self.metrics)

    def log_sync_result(self, result: SyncResult, user: str = 'system'):
        """记录同步结果"""
        self.audit_logger.log_sync_result(result, user)

        # 检查告警
        health_status = self.metrics.get_health_status()
        alerts = self.alert_manager.check_and_alert(result, health_status)

        if alerts:
            self.logger.warning(f"检测到 {len(alerts)} 个告警条件")

    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        health_status = self.metrics.get_health_status()
        recent_alerts = self.alert_manager.get_recent_alerts(hours=24)

        return {
            'health_status': health_status.dict(),
            'recent_alerts': recent_alerts,
            'metrics_summary': {
                'total_operations': sum(m['count'] for m in self.metrics.metrics.values()),
                'success_rate': health_status.success_rate,
                'last_sync_time': health_status.last_sync_time
            }
        }

    def reset_metrics(self):
        """重置指标（用于测试或维护）"""
        self.metrics.reset()
        self.alert_manager.alerts.clear()
