import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv() 

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    SCHEDULER_API_KEY: str
    API_BASE_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()