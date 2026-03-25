from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # Required APIs
    GROQ_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    
    # Redis (Upstash or any Redis-compatible URL)
    REDIS_URL: Optional[str] = None

    # "development" | "production" — controls cookie security flags
    ENVIRONMENT: str = "development"

    # Embeddings (for RAG knowledge base)
    COHERE_API_KEY: Optional[str] = None

    # Optional APIs (with fallbacks)
    SPOTCRIME_API_KEY: Optional[str] = "public"
    FBI_API_KEY: Optional[str] = None          
    HUD_API_KEY: Optional[str] = None
    BLS_API_KEY: Optional[str] = None
    OSM_USER_AGENT: Optional[str] = "movewise_app_v1"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://movewise-web.vercel.app"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow" # Allow extra fields in .env without raising errors


settings = Settings()