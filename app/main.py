from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs import scheduler_jobs
from app.routers import chat, health, suggestion, feedback, admin

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        scheduler_jobs.generate_suggestions_for_all_users,
        trigger="cron",
        hour=2,
        minute=0
    )
    scheduler.add_job(
        scheduler_jobs.run_admin_alert_analysis,
        trigger="cron",
        hour=3,
        minute=0
    )
    
    scheduler.start()
    print("Scheduler started...")
    
    yield
    
    scheduler.shutdown()
    print("Scheduler shut down.")


app = FastAPI(
    lifespan=lifespan,
    title="Financial AI Service",
    description="Backend AI service for the financial management application."
)

app.include_router(chat.router)
app.include_router(health.router)
app.include_router(suggestion.router)
app.include_router(feedback.router)
app.include_router(admin.router)