"""
Redis缓存管理模块 - 用于解决数据一致性问题
"""
import json
import redis
import logging
from typing import Any, Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis缓存管理类"""

    def __init__(self):
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # 测试连接
            self.redis_client.ping()
            logger.info("Redis缓存服务连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存缓存: {e}")
            self.redis_client = None

    def _get_memory_cache(self) -> Dict[str, Any]:
        """获取内存缓存（当Redis不可用时使用）"""
        if not hasattr(self, '_memory_cache'):
            self._memory_cache = {}
        return self._memory_cache

    def set_practice_status(self, practice_id: int, status_data: Dict[str, Any], ttl: int = 300) -> bool:
        """
        设置实践状态缓存

        Args:
            practice_id: 实践ID
            status_data: 状态数据
            ttl: 过期时间（秒），默认5分钟

        Returns:
            bool: 设置是否成功
        """
        try:
            key = f"practice:status:{practice_id}"
            value = json.dumps(status_data, ensure_ascii=False)

            if self.redis_client:
                return self.redis_client.setex(key, ttl, value)
            else:
                # 使用内存缓存
                self._get_memory_cache()[key] = value
                return True
        except Exception as e:
            logger.error(f"设置实践状态缓存失败: {e}")
            return False

    def get_practice_status(self, practice_id: int) -> Optional[Dict[str, Any]]:
        """
        获取实践状态缓存

        Args:
            practice_id: 实践ID

        Returns:
            Optional[Dict[str, Any]]: 状态数据，如果不存在返回None
        """
        try:
            key = f"practice:status:{practice_id}"

            if self.redis_client:
                value = self.redis_client.get(key)
            else:
                # 使用内存缓存
                value = self._get_memory_cache().get(key)

            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取实践状态缓存失败: {e}")
            return None

    def delete_practice_status(self, practice_id: int) -> bool:
        """
        删除实践状态缓存

        Args:
            practice_id: 实践ID

        Returns:
            bool: 删除是否成功
        """
        try:
            key = f"practice:status:{practice_id}"

            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                # 使用内存缓存
                cache = self._get_memory_cache()
                if key in cache:
                    del cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"删除实践状态缓存失败: {e}")
            return False

    def invalidate_user_practices(self, user_id: int) -> bool:
        """
        使某个用户的所有实践缓存失效

        Args:
            user_id: 用户ID

        Returns:
            bool: 操作是否成功
        """
        try:
            pattern = f"practice:status:*"

            if self.redis_client:
                # 获取所有匹配的键
                keys = self.redis_client.keys(pattern)
                if keys:
                    # 批量删除
                    return bool(self.redis_client.delete(*keys))
                return True
            else:
                # 使用内存缓存 - 简单清理所有缓存
                self._get_memory_cache().clear()
                return True
        except Exception as e:
            logger.error(f"使用户实践缓存失效失败: {e}")
            return False

    def set_excellent_work_stats(self, work_id: int, stats_data: Dict[str, Any], ttl: int = 300) -> bool:
        """
        设置优秀作业统计缓存

        Args:
            work_id: 作业ID
            stats_data: 统计数据 (view_count, like_count, favorite_count)
            ttl: 过期时间（秒），默认5分钟

        Returns:
            bool: 设置是否成功
        """
        try:
            key = f"excellent_work:stats:{work_id}"
            value = json.dumps(stats_data, ensure_ascii=False)

            if self.redis_client:
                return self.redis_client.setex(key, ttl, value)
            else:
                # 使用内存缓存
                self._get_memory_cache()[key] = value
                return True
        except Exception as e:
            logger.error(f"设置优秀作业统计缓存失败: {e}")
            return False

    def get_excellent_work_stats(self, work_id: int) -> Optional[Dict[str, Any]]:
        """
        获取优秀作业统计缓存

        Args:
            work_id: 作业ID

        Returns:
            Optional[Dict[str, Any]]: 统计数据，如果不存在返回None
        """
        try:
            key = f"excellent_work:stats:{work_id}"

            if self.redis_client:
                value = self.redis_client.get(key)
            else:
                # 使用内存缓存
                value = self._get_memory_cache().get(key)

            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"获取优秀作业统计缓存失败: {e}")
            return None

    def invalidate_excellent_work_stats(self, work_id: int) -> bool:
        """
        使优秀作业统计缓存失效

        Args:
            work_id: 作业ID

        Returns:
            bool: 删除是否成功
        """
        try:
            key = f"excellent_work:stats:{work_id}"

            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                # 使用内存缓存
                cache = self._get_memory_cache()
                if key in cache:
                    del cache[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"删除优秀作业统计缓存失败: {e}")
            return False

    # ==================== AI相关缓存方法 ====================

    def get_ai_response(self, query_hash: str) -> Optional[str]:
        """
        获取AI响应缓存

        Args:
            query_hash: 查询的哈希值

        Returns:
            Optional[str]: 缓存的响应内容
        """
        try:
            key = f"ai:response:{query_hash}"
            if self.redis_client:
                return self.redis_client.get(key)
            else:
                return self._get_memory_cache().get(key)
        except Exception as e:
            logger.error(f"获取AI响应缓存失败: {e}")
            return None

    def set_ai_response(self, query_hash: str, response: str, ttl: int = 604800) -> bool:  # 默认7天
        """
        设置AI响应缓存

        Args:
            query_hash: 查询的哈希值
            response: 响应内容
            ttl: 过期时间（秒），默认7天

        Returns:
            bool: 设置是否成功
        """
        try:
            key = f"ai:response:{query_hash}"
            if self.redis_client:
                return self.redis_client.setex(key, ttl, response)
            else:
                self._get_memory_cache()[key] = response
                return True
        except Exception as e:
            logger.error(f"设置AI响应缓存失败: {e}")
            return False

    def get_similar_query(self, query_hash: str, threshold: float = 0.8) -> Optional[str]:
        """
        查找相似查询的缓存

        Args:
            query_hash: 当前查询的哈希
            threshold: 相似度阈值

        Returns:
            Optional[str]: 相似查询的响应，如果没有找到返回None
        """
        # 简化实现：这里可以实现更复杂的相似度匹配
        # 目前直接返回完全匹配的结果
        return self.get_ai_response(query_hash)

    def set_operation_lock(self, practice_id: int, operation: str, ttl: int = 60) -> bool:
        """
        设置操作锁，防止并发冲突

        Args:
            practice_id: 实践ID
            operation: 操作类型
            ttl: 锁过期时间（秒）

        Returns:
            bool: 是否成功获取锁
        """
        try:
            key = f"practice:lock:{practice_id}:{operation}"

            if self.redis_client:
                # 使用setnx实现分布式锁
                return self.redis_client.set(key, "1", ex=ttl, nx=True)
            else:
                # 使用内存缓存 - 简单实现
                lock_key = f"{key}:{ttl}"
                if lock_key not in self._get_memory_cache():
                    self._get_memory_cache()[lock_key] = True
                    return True
                return False
        except Exception as e:
            logger.error(f"设置操作锁失败: {e}")
            return False

    def release_operation_lock(self, practice_id: int, operation: str) -> bool:
        """
        释放操作锁

        Args:
            practice_id: 实践ID
            operation: 操作类型

        Returns:
            bool: 是否成功释放锁
        """
        try:
            key = f"practice:lock:{practice_id}:{operation}"

            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                # 使用内存缓存
                lock_key = f"{key}:*"
                cache = self._get_memory_cache()
                keys_to_delete = [k for k in cache.keys() if k.startswith(f"{key}:")]
                for k in keys_to_delete:
                    del cache[k]
                return True
        except Exception as e:
            logger.error(f"释放操作锁失败: {e}")
            return False

# 全局缓存实例
redis_cache = RedisCache()

def get_cache() -> RedisCache:
    """获取缓存实例"""
    return redis_cache

