"""Configuration management for the Options Analytics Platform"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Options Analytics Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "options_user"
    POSTGRES_PASSWORD: str = "options_password"
    POSTGRES_DB: str = "options_db"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Broker Settings
    DEFAULT_BROKER: str = "mock"
    
    # Market Data
    RISK_FREE_RATE: float = 0.05  # 5% default risk-free rate
    
    # Backtesting
    INITIAL_CAPITAL: float = 100000.0
    COMMISSION_PER_CONTRACT: float = 0.65
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
