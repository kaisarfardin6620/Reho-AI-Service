from fastapi import FastAPI, Request
from app.routers import chat, feedback, admin, schedule
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Financial AI Service",
    description="Backend AI service for the financial management application."
)

origins = settings.ALLOWED_HOST_ORIGINS.split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(schedule.router)