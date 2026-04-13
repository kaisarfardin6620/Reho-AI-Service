from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_DB_NAME: str = "finance-management"
    OPENAI_API_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    API_BASE_URL: str

    ALLOWED_HOST_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    REDIS_URL: str = "redis://redis:6379/0"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.startswith("mongodb"):
            raise ValueError("DATABASE_URL must be a valid MongoDB connection string")
        return v

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v or len(v) < 20:
            raise ValueError("OPENAI_API_KEY appears to be missing or invalid")
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v) < 16:
            raise ValueError("JWT_SECRET must be at least 16 characters long")
        return v

    @property
    def allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_HOST_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()