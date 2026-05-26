from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorSpec:
    http_status: int
    retryable: bool = False


ERROR_SPECS: dict[str, ErrorSpec] = {
    "AUTH_FAILED": ErrorSpec(401),
    "AUTH_TIMEOUT": ErrorSpec(401),
    "UNAUTHORIZED": ErrorSpec(401),
    "FORBIDDEN": ErrorSpec(403),
    "VALIDATION_FAILED": ErrorSpec(400),
    "NOT_FOUND": ErrorSpec(404),
    "BOT_NOT_FOUND": ErrorSpec(404),
    "BOT_NOT_OWNED": ErrorSpec(403),
    "BOT_REVOKED": ErrorSpec(403),
    "BOT_ALREADY_CONNECTED": ErrorSpec(409),
    "TOKEN_INVALID": ErrorSpec(401),
    "TOKEN_REGENERATED": ErrorSpec(401),
    "HANDSHAKE_FAILED": ErrorSpec(400),
    "PROTOCOL_VERSION_UNSUPPORTED": ErrorSpec(400),
    "HEARTBEAT_TIMEOUT": ErrorSpec(400, retryable=True),
    "MESSAGE_FORMAT_INVALID": ErrorSpec(400),
    "MESSAGE_SEND_FAILED": ErrorSpec(500, retryable=True),
    "CONVERSATION_NOT_FOUND": ErrorSpec(404),
    "CONVERSATION_LOAD_FAILED": ErrorSpec(500, retryable=True),
    "MESSAGE_DELIVERY_FAILED": ErrorSpec(500, retryable=True),
    "AUTH_EXPIRED": ErrorSpec(401),
    "BOT_STATUS_SYNC_FAILED": ErrorSpec(500, retryable=True),
    "RATE_LIMITED": ErrorSpec(429, retryable=True),
    "INTERNAL_ERROR": ErrorSpec(500),
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, retryable: bool | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        spec = ERROR_SPECS.get(code, ERROR_SPECS["INTERNAL_ERROR"])
        self.http_status = spec.http_status
        self.retryable = spec.retryable if retryable is None else retryable
