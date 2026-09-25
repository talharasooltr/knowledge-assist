"""Link ingestion records to their PDF identity.

Revision ID: 0002_link_ingestion_to_pdf
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_link_ingestion_to_pdf"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingest_state", sa.Column("pdf_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ingest_state_pdf_id_pdfs",
        "ingest_state",
        "pdfs",
        ["pdf_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_ingest_state_pdf_id", "ingest_state", ["pdf_id"])


def downgrade() -> None:
    op.drop_index("ix_ingest_state_pdf_id", table_name="ingest_state")
    op.drop_constraint("fk_ingest_state_pdf_id_pdfs", "ingest_state", type_="foreignkey")
    op.drop_column("ingest_state", "pdf_id")
