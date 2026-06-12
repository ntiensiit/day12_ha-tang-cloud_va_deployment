import time
import redis
from fastapi import HTTPException, status
from app.config import settings

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_rate_limit(self, user_id: str):
        now = int(time.time())
        # Use a rolling or fixed window. For simplicity, we use a 1-minute fixed window key
        window = now // 60
        key = f"rate_limit:{user_id}:{window}"
        
        # Increment request count for this window
        requests = self.redis.incr(key)
        if requests == 1:
            self.redis.expire(key, 60)
            
        if requests > settings.RATE_LIMIT_PER_MIN:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MIN} requests per minute."
            )
