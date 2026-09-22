from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./railway.db",
        validation_alias="DATABASE_URL"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-min-32-chars",
        validation_alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Weather
    weather_api_key: Optional[str] = Field(default=None, validation_alias="WEATHER_API_KEY")
    weather_provider: str = Field(default="open-meteo", validation_alias="WEATHER_PROVIDER")

    # AI Providers
    nvidia_api_key: Optional[str] = Field(default=None, validation_alias="NVIDIA_API_KEY")
    nvidia_model: str = Field(default="nvidia/nemotron-3-ultra", validation_alias="NVIDIA_MODEL")
    
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", validation_alias="GEMINI_MODEL")
    
    groq_api_key: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-70b-versatile", validation_alias="GROQ_MODEL")

    primary_ai_provider: str = Field(default="nvidia", validation_alias="PRIMARY_AI_PROVIDER")
    fallback_ai_provider: Optional[str] = Field(default="gemini", validation_alias="FALLBACK_AI_PROVIDER")

    ai_request_timeout: float = Field(default=30.0, validation_alias="AI_REQUEST_TIMEOUT")
    ai_max_retries: int = Field(default=3, validation_alias="AI_MAX_RETRIES")

    # Environment
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Simulation
    simulation_speed: float = Field(default=1.0, validation_alias="SIMULATION_SPEED")
    simulation_scenario: str = Field(default="NORMAL", validation_alias="SIMULATION_SCENARIO")

    # Frontend
    frontend_url: str = Field(default="http://localhost:5173")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()