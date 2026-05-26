from pydantic import BaseModel


class CommandRequest(BaseModel):
    conversation_id: str | None = None
    command: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    employee_id: str
    real_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class EnsureConversationRequest(BaseModel):
    target_type: str
    target_id: str


class SendConversationMessageRequest(BaseModel):
    content: str
    content_type: str = "text"
