from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, profile, analysis, chat, stream

# Create database tables
Base.metadata.create_all(bind=engine)

# Add new columns to existing deployments without a full Alembic migration
with engine.connect() as _conn:
    _conn.execute(text(
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'completed'"
    ))
    _conn.execute(text(
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS error_message TEXT"
    ))
    _conn.commit()

# Initialize FastAPI app
app = FastAPI(
    title="MoveWise API",
    description="AI-powered relocation decision assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(stream.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to MoveWise API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "MoveWise API is running"}