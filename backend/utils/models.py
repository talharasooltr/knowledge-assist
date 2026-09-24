from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.config import EMBEDDING_DIMENSION


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    userid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Pdf(Base):
    __tablename__ = "pdfs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    filepath: Mapped[str] = mapped_column(String(1024), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks: Mapped[list["PdfChunk"]] = relationship(
        back_populates="pdf", cascade="all, delete-orphan"
    )


class IngestState(Base):
    __tablename__ = "ingest_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    ingested_by: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PdfChunk(Base):
    __tablename__ = "pdf_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pdf_id: Mapped[int | None] = mapped_column(
        ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    source: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pdf: Mapped[Pdf | None] = relationship(back_populates="chunks")


class ChatMemory(Base):
    __tablename__ = "chat_memory"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    timestamp: Mapped[float] = mapped_column(nullable=False, index=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
