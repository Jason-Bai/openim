"""p0 schema

Revision ID: 0001_p0_schema
Revises:
Create Date: 2026-05-25 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_p0_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("employee_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("real_name", sa.String(length=128), nullable=False),
        sa.Column("online", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("addressee_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("requester_id", "addressee_id", name="uq_friendships_request_pair"),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=40), primary_key=True),
        sa.Column("conversation_type", sa.String(length=32), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("last_message_id", sa.String(length=64), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "uq_conversations_owner_target",
        "conversations",
        ["owner_user_id", "target_type", "target_id"],
        unique=True,
    )
    op.create_index(
        "idx_conversations_owner_sort",
        "conversations",
        ["owner_user_id", "last_message_at", "updated_at"],
        unique=False,
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=40), primary_key=True),
        sa.Column("conversation_id", sa.String(length=40), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_message_id", sa.String(length=40), nullable=True),
        sa.Column("sender_type", sa.String(length=16), nullable=False),
        sa.Column("sender_id", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at", "id"],
        unique=False,
    )
    op.create_table(
        "bots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot_id", sa.String(length=40), nullable=False, unique=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("bot_type", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("token_last4", sa.String(length=4), nullable=False),
        sa.Column("token_revealed_at", sa.DateTime(), nullable=True),
        sa.Column("token_regenerated_at", sa.DateTime(), nullable=True),
        sa.Column("connect_status", sa.String(length=32), nullable=False),
        sa.Column("protocol_version", sa.String(length=32), nullable=True),
        sa.Column("first_connected_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "user_bot_bindings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("bot_id", sa.String(length=40), nullable=False),
        sa.Column("binding_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "uq_user_bot_bindings_active",
        "user_bot_bindings",
        ["user_id", "bot_id"],
        unique=True,
    )
    op.create_table(
        "bot_connection_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot_id", sa.String(length=40), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("remote_addr", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("bot_connection_logs")
    op.drop_index("uq_user_bot_bindings_active", table_name="user_bot_bindings")
    op.drop_table("user_bot_bindings")
    op.drop_table("bots")
    op.drop_index("idx_messages_conversation_created", table_name="messages")
    op.drop_table("messages")
    op.drop_index("idx_conversations_owner_sort", table_name="conversations")
    op.drop_index("uq_conversations_owner_target", table_name="conversations")
    op.drop_table("conversations")
    op.drop_table("friendships")
    op.drop_table("users")
