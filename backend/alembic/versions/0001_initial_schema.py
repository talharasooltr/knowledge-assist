"""Create initial PostgreSQL and pgvector schema.

Revision ID: 0001_initial_schema
Revises:
"""
import os

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("userid", sa.String(255), nullable=False, unique=True),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "pdfs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("filepath", sa.String(1024), nullable=False),
        sa.Column("uploaded_by", sa.String(255), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pdfs_uploaded_by", "pdfs", ["uploaded_by"])
    op.create_table(
        "ingest_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("ingested_by", sa.String(255), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ingest_state_ingested_by", "ingest_state", ["ingested_by"])
    op.create_table(
        "pdf_chunks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("pdf_id", sa.Integer(), sa.ForeignKey("pdfs.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=False),
        sa.Column("source", sa.String(512)),
        sa.Column("filename", sa.String(512)),
        sa.Column("user_id", sa.String(255)),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("chunk_index", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("pdf_id", "source", "filename", "user_id", "is_public"):
        op.create_index(f"ix_pdf_chunks_{column}", "pdf_chunks", [column])
    op.create_index(
        "ix_pdf_chunks_embedding_hnsw",
        "pdf_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_table(
        "chat_memory",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_chat_memory_user_id", "chat_memory", ["user_id"])
    op.create_index("ix_chat_memory_timestamp", "chat_memory", ["timestamp"])
    op.create_index(
        "ix_chat_memory_embedding_hnsw",
        "chat_memory",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_chat_memory_embedding_hnsw", table_name="chat_memory")
    op.drop_index("ix_chat_memory_timestamp", table_name="chat_memory")
    op.drop_index("ix_chat_memory_user_id", table_name="chat_memory")
    op.drop_table("chat_memory")
    op.drop_index("ix_pdf_chunks_embedding_hnsw", table_name="pdf_chunks")
    for column in ("is_public", "user_id", "filename", "source", "pdf_id"):
        op.drop_index(f"ix_pdf_chunks_{column}", table_name="pdf_chunks")
    op.drop_table("pdf_chunks")
    op.drop_index("ix_ingest_state_ingested_by", table_name="ingest_state")
    op.drop_table("ingest_state")
    op.drop_index("ix_pdfs_uploaded_by", table_name="pdfs")
    op.drop_table("pdfs")
    op.drop_table("users")
