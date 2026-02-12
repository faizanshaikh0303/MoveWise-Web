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
    
    # Optional APIs (with fallbacks)
    SPOTCRIME_API_KEY: Optional[str] = "public"
    FBI_API_KEY: Optional[str] = None          # ← MAKE SURE THIS IS HERE
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
        extra = "allow"  # ← IMPORTANT


settings = Settings()