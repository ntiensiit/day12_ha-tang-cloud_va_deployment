from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Production AI Agent"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    API_KEY: str = "admin-secret-key"
    
    # Rate Limiting & Cost Guard limits
    RATE_LIMIT_PER_MIN: int = 10
    MONTHLY_COST_LIMIT_USD: float = 10.0
    
    # Mock cost per token or call
    COST_PER_REQUEST_USD: float = 0.05
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
