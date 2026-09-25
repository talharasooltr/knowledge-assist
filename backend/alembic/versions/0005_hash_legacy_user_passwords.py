"""Hash existing user passwords with scrypt.

Revision ID: 0005_hash_legacy_passwords
Revises: 0004_pdf_identity_delete_state
"""
from alembic import context, op
import sqlalchemy as sa

from app.core.passwords import hash_password

revision = "0005_hash_legacy_passwords"
down_revision = "0004_pdf_identity_delete_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        raise RuntimeError(
            "Password hashing migration requires an online database connection."
        )

    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id, password FROM users")).all()
    for user_id, stored_password in users:
        if not stored_password.startswith("scrypt$"):
            connection.execute(
                sa.text("UPDATE users SET password = :password WHERE id = :user_id"),
                {"password": hash_password(stored_password), "user_id": user_id},
            )


def downgrade() -> None:
    raise RuntimeError("Hashed user passwords cannot be safely downgraded to plaintext.")