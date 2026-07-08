"""
Redis Cache Manager
캐싱, 세션, 분산 락 관리
"""
import json
import pickle
from typing import Any, Optional, Callable
from functools import wraps
import redis.asyncio as aioredis
from redis.asyncio import Redis
from app.core.config import settings
from app.core.logging import log


class RedisManager:
    """Redis 연결 및 캐싱 관리"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """Redis 연결"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # bytes로 받아서 pickle 사용
                max_connections=50,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            await self.redis.ping()
            log.info("✅ Redis connected successfully")
        except Exception as e:
            log.error(f"❌ Redis connection failed: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Redis 연결 종료"""
        if self.redis:
            await self.redis.close()
            log.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            log.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 300):
        """
        캐시에 데이터 저장
        :param key: 캐시 키
        :param value: 저장할 값
        :param expire: 만료 시간(초), 기본 5분
        """
        if not self.redis:
            return False
        
        try:
            serialized = pickle.dumps(value)
            await self.redis.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            log.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str):
        """캐시 삭제"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            log.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        if not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            log.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """카운터 증가"""
        if not self.redis:
            return 0
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            log.error(f"Redis INCR error for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int):
        """키 만료 시간 설정"""
        if not self.redis:
            return False
        
        try:
            await self.redis.expire(key, seconds)
            return True
        except Exception as e:
            log.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    # Session 관리
    async def set_session(self, session_id: str, user_id: int):
        """세션 저장"""
        key = f"session:{session_id}"
        await self.set(key, user_id, expire=settings.SESSION_EXPIRE_SECONDS)
    
    async def get_session(self, session_id: str) -> Optional[int]:
        """세션 조회"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str):
        """세션 삭제"""
        key = f"session:{session_id}"
        await self.delete(key)
    
    # 분산 락
    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """분산 락 획득"""
        if not self.redis:
            return True  # Redis 없으면 락 없이 진행
        
        try:
            return await self.redis.set(f"lock:{lock_name}", "1", nx=True, ex=timeout)
        except Exception as e:
            log.error(f"Lock acquire error for {lock_name}: {e}")
            return False
    
    async def release_lock(self, lock_name: str):
        """분산 락 해제"""
        await self.delete(f"lock:{lock_name}")
    
    # 캐시 무효화 (패턴 매칭)
    async def invalidate_pattern(self, pattern: str):
        """
        패턴에 매칭되는 모든 키 삭제
        예: invalidate_pattern("post_detail:123:*") -> 해당 게시글의 모든 캐시 삭제
        """
        if not self.redis:
            return
        
        try:
            cursor = 0
            keys_to_delete = []
            
            # SCAN으로 패턴 매칭 키 찾기
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                keys_to_delete.extend(keys)
                if cursor == 0:
                    break
            
            # 일괄 삭제
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
                log.info(f"Invalidated {len(keys_to_delete)} cache keys matching: {pattern}")
        except Exception as e:
            log.error(f"Cache invalidation error for pattern {pattern}: {e}")


# 전역 Redis 인스턴스
redis_manager = RedisManager()


def cache(key_prefix: str, expire: int = 300):
    """
    캐싱 데코레이터
    
    사용 예:
    @cache(key_prefix="user", expire=600)
    async def get_user(user_id: int):
        return user_data
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{':'.join(map(str, args))}:{':'.join(f'{k}={v}' for k, v in kwargs.items())}"
            
            # 캐시 조회
            cached = await redis_manager.get(cache_key)
            if cached is not None:
                log.debug(f"Cache HIT: {cache_key}")
                return cached
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 캐시 저장
            if result is not None:
                await redis_manager.set(cache_key, result, expire=expire)
                log.debug(f"Cache SET: {cache_key}")
            
            return result
        
        return wrapper
    return decorator
