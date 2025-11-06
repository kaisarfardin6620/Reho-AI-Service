from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.security import get_user_id_from_token
from app.services import feedback_service
from app.models.feedback import OptimizationResponse
from app.models.request_models import OptimizationRequest

router = APIRouter(prefix="/feedback", tags=["AI Optimization Feedback"])

@router.post("/optimize-expenses", response_model=OptimizationResponse)
async def get_expense_optimization(
    request: OptimizationRequest,
    current_user_id: str = Depends(get_user_id_from_token)
):
    # Validate user can only access their own data
    if request.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's optimization data"
        )
    report = await feedback_service.get_expense_optimization_feedback(request.user_id)
    return report

@router.post("/optimize-budget", response_model=OptimizationResponse)
async def get_budget_optimization(user_id: str = Depends(get_user_id_from_token)):
    report = await feedback_service.get_budget_optimization_feedback(user_id)
    return report

@router.post("/optimize-debt", response_model=OptimizationResponse)
async def get_debt_optimization(user_id: str = Depends(get_user_id_from_token)):
    report = await feedback_service.get_debt_optimization_feedback(user_id)
    return report