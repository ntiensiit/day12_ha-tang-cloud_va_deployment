import redis
from fastapi import HTTPException, status
from app.config import settings

class CostGuard:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_and_record_cost(self, user_id: str) -> float:
        # Check current month's cost key, e.g. "cost:user_id:YYYYMM"
        from datetime import datetime
        month_str = datetime.utcnow().strftime("%Y%m")
        key = f"cost:{user_id}:{month_str}"
        
        current_cost = self.redis.get(key)
        current_cost_val = float(current_cost) if current_cost else 0.0
        
        if current_cost_val >= settings.MONTHLY_COST_LIMIT_USD:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Monthly cost limit of ${settings.MONTHLY_COST_LIMIT_USD} exceeded for this user."
            )
            
        # Add the cost of this request
        new_cost = self.redis.incrbyfloat(key, settings.COST_PER_REQUEST_USD)
        # Keep keys for at least 60 days
        self.redis.expire(key, 60 * 24 * 3600)
        return new_cost
