from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_sqlite_runtime_schema(engine: Engine) -> None:
    if engine.url.get_backend_name() != "sqlite":
        return
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "users" not in table_names:
        return
    with engine.begin() as connection:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "online" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN online BOOLEAN NOT NULL DEFAULT 0"))
        if "last_seen_at" not in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN last_seen_at DATETIME "
                    "NOT NULL DEFAULT '1970-01-01 00:00:00'"
                )
            )
        if "conversations" in table_names:
            conversation_columns = {
                column["name"] for column in inspector.get_columns("conversations")
            }
            if "title" not in conversation_columns:
                connection.execute(
                    text("ALTER TABLE conversations ADD COLUMN title VARCHAR(120) NOT NULL DEFAULT ''")
                )
            connection.execute(
                text("UPDATE conversations SET conversation_type = 'direct' WHERE conversation_type = 'bot'")
            )
            connection.execute(
                text("UPDATE conversations SET target_type = 'openclaw_bot' WHERE target_type = 'bot'")
            )
        if "messages" not in table_names:
            connection.execute(
                text(
                    "CREATE TABLE messages ("
                    "id VARCHAR(40) NOT NULL PRIMARY KEY, "
                    "conversation_id VARCHAR(40) NOT NULL, "
                    "client_message_id VARCHAR(40), "
                    "sender_type VARCHAR(16) NOT NULL, "
                    "sender_id VARCHAR(64) NOT NULL, "
                    "content_type VARCHAR(16) NOT NULL, "
                    "content TEXT NOT NULL, "
                    "status VARCHAR(16) NOT NULL, "
                    "created_at DATETIME NOT NULL, "
                    "FOREIGN KEY(conversation_id) REFERENCES conversations (id) ON DELETE CASCADE"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX idx_messages_conversation_created "
                    "ON messages (conversation_id, created_at, id)"
                )
            )
