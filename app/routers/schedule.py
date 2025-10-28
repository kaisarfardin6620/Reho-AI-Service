from fastapi import APIRouter, Depends, BackgroundTasks
from app.services import admin_service, feedback_service
from app.utils.security import verify_scheduler_key

router = APIRouter(
    prefix="/schedule",
    tags=["Scheduled Jobs"],
    dependencies=[Depends(verify_scheduler_key)]
)

@router.post("/run-daily-ai-jobs")
async def trigger_all_daily_jobs(background_tasks: BackgroundTasks):
    
    background_tasks.add_task(feedback_service.generate_optimization_reports_for_all_users)
    
    background_tasks.add_task(admin_service.run_analysis_for_all_users)

    return {"message": "Daily AI analysis and reporting jobs have been started in the background."}