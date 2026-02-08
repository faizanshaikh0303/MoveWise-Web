from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # APIs
    GROQ_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "https://movewise-swart.vercel.app"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()