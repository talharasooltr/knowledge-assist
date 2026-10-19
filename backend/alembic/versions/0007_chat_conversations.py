"""Persist independent chat conversations and associate existing messages."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0007_chat_conversations"
down_revision = "0006_server_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_conversations_user_id",
        "chat_conversations",
        ["user_id"],
    )
    op.create_index(
        "ix_chat_conversations_user_updated",
        "chat_conversations",
        ["user_id", "updated_at"],
    )
    op.add_column(
        "chat_memory",
        sa.Column("conversation_id", sa.String(length=36), nullable=True),
    )

    connection = op.get_bind()
    messages = sa.table(
        "chat_memory",
        sa.column("id", sa.String(length=64)),
        sa.column("user_id", sa.String(length=255)),
        sa.column("conversation_id", sa.String(length=36)),
    )
    conversations = sa.table(
        "chat_conversations",
        sa.column("id", sa.String(length=36)),
        sa.column("user_id", sa.String(length=255)),
        sa.column("title", sa.String(length=120)),
    )
    user_ids = connection.execute(
        sa.select(sa.distinct(messages.c.user_id))
    ).scalars().all()
    for user_id in user_ids:
        conversation_id = str(uuid4())
        connection.execute(
            conversations.insert().values(
                id=conversation_id,
                user_id=user_id,
                title="Previous conversation",
            )
        )
        connection.execute(
            messages.update()
            .where(messages.c.user_id == user_id)
            .values(conversation_id=conversation_id)
        )

    op.alter_column("chat_memory", "conversation_id", nullable=False)
    op.create_foreign_key(
        "fk_chat_memory_conversation_id",
        "chat_memory",
        "chat_conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_chat_memory_user_conversation_timestamp",
        "chat_memory",
        ["user_id", "conversation_id", "timestamp"],
    )
    op.create_index(
        "ix_chat_memory_conversation_id",
        "chat_memory",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_chat_memory_conversation_id", table_name="chat_memory")
    op.drop_index("ix_chat_memory_user_conversation_timestamp", table_name="chat_memory")
    op.drop_constraint("fk_chat_memory_conversation_id", "chat_memory", type_="foreignkey")
    op.drop_column("chat_memory", "conversation_id")
    op.drop_index("ix_chat_conversations_user_updated", table_name="chat_conversations")
    op.drop_index("ix_chat_conversations_user_id", table_name="chat_conversations")
    op.drop_table("chat_conversations")
