"""Link uniquely identifiable legacy PDF index rows to their PDF records.

Revision ID: 0003_resolve_legacy_pdf_identity
Revises: 0002_link_ingestion_to_pdf
"""
from alembic import op

revision = "0003_resolve_legacy_pdf_identity"
down_revision = "0002_link_ingestion_to_pdf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        WITH matches AS (
            SELECT state.id AS state_id, MIN(pdf.id) AS pdf_id
            FROM ingest_state AS state
            JOIN pdfs AS pdf
              ON pdf.filename = state.filename
             AND (
                pdf.uploaded_by = state.ingested_by
                OR (pdf.is_public AND state.ingested_by = 'public')
             )
            WHERE state.pdf_id IS NULL
            GROUP BY state.id
            HAVING COUNT(pdf.id) = 1
        )
        UPDATE ingest_state AS state
        SET pdf_id = matches.pdf_id
        FROM matches
        WHERE state.id = matches.state_id
        """
    )
    op.execute(
        """
        WITH matches AS (
            SELECT chunk.id AS chunk_id, MIN(pdf.id) AS pdf_id
            FROM pdf_chunks AS chunk
            JOIN pdfs AS pdf
              ON pdf.filename = COALESCE(chunk.filename, chunk.source)
             AND (
                pdf.uploaded_by = chunk.user_id
                OR (pdf.is_public AND chunk.user_id = 'public')
             )
            WHERE chunk.pdf_id IS NULL
            GROUP BY chunk.id
            HAVING COUNT(pdf.id) = 1
        )
        UPDATE pdf_chunks AS chunk
        SET pdf_id = matches.pdf_id
        FROM matches
        WHERE chunk.id = matches.chunk_id
        """
    )
    op.execute("DELETE FROM ingest_state WHERE pdf_id IS NULL")
    op.execute("DELETE FROM pdf_chunks WHERE pdf_id IS NULL")


def downgrade() -> None:
    # Deleted legacy rows were ambiguous; their source PDFs can be reindexed.
    pass