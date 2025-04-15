from app.core.logger import setup_logger



# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, users
from app.core.config import settings
from app.db.init_db import init_db

setup_logger()

from app.core.logger import logger

logger.info('start test')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize the database
    await init_db()
    yield
    # Shutdown: add any cleanup operations here if needed
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User Registration API with JWT authentication",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)

@app.get("/")
def health_check():
    return {"status": "healthy"}