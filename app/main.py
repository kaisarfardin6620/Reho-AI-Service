from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.utils.logging import setup_logging
from app.utils.metrics import track_request_metrics
from app.db.client import client, redis_client
from loguru import logger

from app.routers import chat, admin, calculator, feedback

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Reho AI Finance API...")
    yield
    logger.info("Shutting down... Closing database connections.")
    client.close()
    await redis_client.aclose()

app = FastAPI(title="Reho AI Finance API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(track_request_metrics)

app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(calculator.router)
app.include_router(feedback.router)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}