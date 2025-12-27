from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.utils.logging import setup_logging
from app.utils.metrics import track_request_metrics
try:
    from app.routers import chat, admin, calculator, feedback, schedule
except ImportError:
    from app import chat, admin, calculator, feedback, schedule

setup_logging()

app = FastAPI(title="Reho AI Finance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(track_request_metrics())

app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(calculator.router)
app.include_router(feedback.router)
app.include_router(schedule.router)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}