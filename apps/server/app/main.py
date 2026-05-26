from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api import auth, bot_messages, bots, conversations, default_bot, friends, users
from app.core.errors import ApiError, ERROR_SPECS
from app.core.response import error_response, request_id_from
from app.db.base import Base
from app.db.runtime_schema import ensure_sqlite_runtime_schema
from app.db.session import engine
from app.ws import bot_gateway, employee


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_runtime_schema(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="OpenIM", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return error_response(
            request_id=request_id_from(request),
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            status_code=exc.http_status,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, _: IntegrityError) -> JSONResponse:
        spec = ERROR_SPECS["VALIDATION_FAILED"]
        return error_response(
            request_id=request_id_from(request),
            code="VALIDATION_FAILED",
            message="数据已存在或不合法",
            retryable=spec.retryable,
            status_code=spec.http_status,
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(conversations.router)
    app.include_router(bots.router)
    app.include_router(bot_messages.router)
    app.include_router(friends.router)
    app.include_router(default_bot.router)
    app.include_router(bot_gateway.router)
    app.include_router(employee.router)
    return app


app = create_app()
