from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class DocChunk(Base):
    __tablename__ = "doc_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_key = Column(String(100), unique=True, index=True, nullable=False)
    section = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024), nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
