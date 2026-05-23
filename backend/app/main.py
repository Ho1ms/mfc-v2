from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .core.audit import AuditMiddleware
from .core.config import settings
from .core.errors import ApiError
from .core.http_headers import RequestIdMiddleware, SecurityHeadersMiddleware
from .core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="MFC-MAX API",
    version="0.1.0",
    description="Система обработки заявок и обращений МФЦ — backend (FastAPI).",
    lifespan=lifespan,
)

# Внимание: порядок add_middleware важен. Starlette оборачивает их в обратном порядке,
# поэтому RequestId должен быть «снаружи» (добавлен последним) — чтобы id был выставлен
# до того, как audit/headers что-то делают.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(RequestIdMiddleware)

if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/healthz", tags=["health"])
def healthz() -> dict:
    return {"status": "ok", "env": settings.APP_ENV}


app.include_router(api_router, prefix="/api")
