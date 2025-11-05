from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from app.utils.security import require_admin_user
from app.services import admin_service
from app.models.admin import AdminUserAIDashboard 

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_user)] 
)

@router.get("/user-dashboard/{user_id}", response_model=AdminUserAIDashboard)
async def get_single_user_admin_data(user_id: str):
    try:
        dashboard_data = await admin_service.get_single_user_admin_dashboard(user_id)
        return dashboard_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error fetching admin dashboard for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compile the user's AI dashboard data."
        )