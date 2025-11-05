from fastapi import FastAPI
from app.routers import chat, feedback, admin, schedule 

app = FastAPI(
    title="Financial AI Service",
    description="Backend AI service for the financial management application."
)

app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(schedule.router)