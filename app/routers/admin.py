from fastapi import APIRouter, Depends, BackgroundTasks
from app.utils.security import require_admin_user
from app.services import admin_service
from app.db import queries as db_queries
from app.models.admin import AdminAlertResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_user)] 
)

@router.get("/alerts", response_model=AdminAlertResponse)
async def get_admin_alerts():
    alerts = await db_queries.get_all_admin_alerts()
    return {"alerts": alerts}

@router.post("/run-analysis")
async def trigger_full_analysis(background_tasks: BackgroundTasks):
    background_tasks.add_task(admin_service.run_analysis_for_all_users)
    return {"message": "Full user analysis job has been started in the background."}