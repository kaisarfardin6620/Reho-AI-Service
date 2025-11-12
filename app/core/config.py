import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv() 

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    SCHEDULER_API_KEY: str
    API_BASE_URL: str
    
    ALLOWED_HOST_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000" 
    
    REDIS_URL: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()