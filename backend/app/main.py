from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uuid
from app.core.config import settings
from app.api.routes import auth, students, staff, classes, videos, fees, exams, reports, chat, bus, notifications
from app.api.routes.homework_notices import hw_router, notice_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 {settings.APP_NAME} v5.0 — {settings.APP_ENV}")
    yield

app = FastAPI(
    title="SchoolSaaS API", version="5.0.0",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["Authorization","Content-Type","X-Requested-With"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers.update({
        "X-Request-ID": rid,
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    })
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.exception_handler(RequestValidationError)
async def val_err(req, exc):
    return JSONResponse(422, {"detail": "Validation error", "errors": exc.errors()})

@app.exception_handler(500)
async def srv_err(req, exc):
    return JSONResponse(500, {"detail": "Internal server error"})

P = "/api"
app.include_router(auth.router,          prefix=P)
app.include_router(students.router,      prefix=P)
app.include_router(staff.router,         prefix=P)
app.include_router(classes.router,       prefix=P)
app.include_router(hw_router,            prefix=P)
app.include_router(notice_router,        prefix=P)
app.include_router(videos.router,        prefix=P)
app.include_router(fees.router,          prefix=P)
app.include_router(exams.router,         prefix=P)
app.include_router(reports.router,       prefix=P)
app.include_router(chat.router,          prefix=P)
app.include_router(bus.router,           prefix=P)
app.include_router(notifications.router, prefix=P)

@app.get("/api/health")
async def health():
    return {
        "status": "ok", "app": settings.APP_NAME, "version": "5.0.0",
        "modules": ["auth","students","staff","classes","videos","fees",
                    "exams","reports","chat","bus","notifications"]
    }
