from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


def request_id_from(request: Request) -> str:
    return request.headers.get("x-request-id") or f"req_{uuid4().hex}"


def ok(data: object, request_id: str) -> dict[str, object]:
    return {"request_id": request_id, "ok": True, "data": data}


def error_response(
    *,
    request_id: str,
    code: str,
    message: str,
    retryable: bool,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "request_id": request_id,
            "ok": False,
            "error": {"code": code, "message": message, "retryable": retryable},
        },
    )

