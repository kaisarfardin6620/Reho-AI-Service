from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.routers import chat, feedback, admin, schedule
from app.utils.metrics import track_request_metrics

app = FastAPI(
    title="Financial AI Service",
    description="Backend AI service for the financial management application."
)

app.middleware("http")(track_request_metrics())

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(schedule.router)