from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.limiter import limiter
from app.api import auth, profile, analysis, chat, stream

# Enable pgvector extension before creating tables
with engine.connect() as _conn:
    _conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    _conn.commit()

# Create database tables (DocChunk requires vector extension to exist first)
Base.metadata.create_all(bind=engine)

# Create HNSW index for fast cosine similarity search on doc_chunks
with engine.connect() as _conn:
    _conn.execute(text(
        "CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx "
        "ON doc_chunks USING hnsw (embedding vector_cosine_ops)"
    ))
    _conn.commit()

# Add new columns to existing deployments without a full Alembic migration
with engine.connect() as _conn:
    _conn.execute(text(
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'completed'"
    ))
    _conn.execute(text(
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS error_message TEXT"
    ))
    # Any analysis left 'processing' means the service was restarted mid-run — mark as failed
    _conn.execute(text(
        "UPDATE analyses SET status='failed', error_message='Service restarted during processing' "
        "WHERE status='processing'"
    ))
    _conn.commit()

# Seed RAG knowledge base (idempotent — skips unchanged chunks)
try:
    from app.services.rag_seeder import seed_knowledge_base
    with SessionLocal() as _db:
        seed_knowledge_base(_db)
except Exception as _e:
    print(f"[RAG] Seeding failed (non-fatal): {_e}")

# Initialize FastAPI app
app = FastAPI(
    title="MoveWise API",
    description="AI-powered relocation decision assistant",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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