from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.core.exceptions import DomainException
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    #Aquí se maneja cualquier excepción de DomainException y se formatea la res en JSON
    return JSONResponse(
        status_code=400,
        content={
            "error_type": exc.__class__.__name__,
            "message": exc.message,
            "path": request.url.path
        }
    )


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "environment": settings.app_env}
