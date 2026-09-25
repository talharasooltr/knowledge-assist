"""Require PDF identity and add retryable deletion state.

Revision ID: 0004_pdf_identity_delete_state
Revises: 0003_resolve_legacy_pdf_identity
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_pdf_identity_delete_state"
down_revision = "0003_resolve_legacy_pdf_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM ingest_state WHERE pdf_id IS NULL")
    op.execute("DELETE FROM pdf_chunks WHERE pdf_id IS NULL")
    op.alter_column("ingest_state", "pdf_id", nullable=False)
    op.alter_column("pdf_chunks", "pdf_id", nullable=False)
    op.add_column(
        "pdfs",
        sa.Column(
            "deletion_requested",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("pdfs", "deletion_requested")
    op.alter_column("pdf_chunks", "pdf_id", nullable=True)
    op.alter_column("ingest_state", "pdf_id", nullable=True)