"""Add indexed full-text search for hybrid document retrieval."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_hybrid_document_search"
down_revision = "0007_chat_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pdf_chunks",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', content)", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_pdf_chunks_search_vector",
        "pdf_chunks",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_pdf_chunks_search_vector", table_name="pdf_chunks")
    op.drop_column("pdf_chunks", "search_vector")
