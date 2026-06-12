import signal
import sys
import time
import json
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import redis

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import RateLimiter
from app.cost_guard import CostGuard

# Configure Structured JSON Logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

logger = logging.getLogger("production-agent")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Setup state signals and redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

rate_limiter = RateLimiter(redis_client)
cost_guard = CostGuard(redis_client)

is_shutting_down = threading.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup check
    try:
        redis_client.ping()
        logger.info("Successfully connected to Redis at startup.")
    except Exception as e:
        logger.error(f"Cannot connect to Redis at startup: {e}")
    yield
    # Shutdown cleanups if any
    logger.info("Lifespan shutdown complete.")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

class AskRequest(BaseModel):
    user_id: str
    question: str

class AskResponse(BaseModel):
    answer: str
    estimated_cost_usd: float

def shutdown_handler(signum, frame):
    logger.info("Received SIGTERM, initiating graceful shutdown...")
    is_shutting_down.set()
    # Allow some buffer time for current requests to finish
    time.sleep(2)
    logger.info("Graceful shutdown sequence complete. Exiting.")
    sys.exit(0)

# Register shutdown handler
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

@app.get("/health")
def health():
    """Liveness check: returns 200 OK immediately if service is running"""
    if is_shutting_down.is_set():
        raise HTTPException(status_code=503, detail="Server is shutting down")
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    """Readiness check: checks external dependencies like Redis"""
    if is_shutting_down.is_set():
        raise HTTPException(status_code=503, detail="Server is shutting down")
    try:
        redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis connection offline")

@app.post("/ask", response_model=AskResponse)
def ask(
    req: AskRequest,
    api_key: str = Depends(verify_api_key)
):
    if is_shutting_down.is_set():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is shutting down")

    user_id = req.user_id

    # 1. Rate Limit Check
    rate_limiter.check_rate_limit(user_id)

    # 2. Cost Guard Check & Track
    new_total_cost = cost_guard.check_and_record_cost(user_id)

    # 3. Handle Stateless Conversation History with Redis
    history_key = f"chat_history:{user_id}"

    # Get previous conversation context
    history = redis_client.lrange(history_key, 0, -1)

    # Simple Mock AI Agent logic including context
    context_str = " ".join(history)
    mock_reply = f"Hello {user_id}. You asked: '{req.question}'. Previously we talked about: {len(history)} messages."

    # Store conversation state back to Redis
    redis_client.rpush(history_key, f"User: {req.question}")
    redis_client.rpush(history_key, f"Agent: {mock_reply}")
    # Retain only last 10 turns
    redis_client.ltrim(history_key, -20, -1)
    # Expire history after 24 hours of inactivity
    redis_client.expire(history_key, 24 * 3600)

    logger.info(f"Successfully processed request for user {user_id}", extra={"user_id": user_id})

    return AskResponse(
        answer=mock_reply,
        estimated_cost_usd=settings.COST_PER_REQUEST_USD
    )
