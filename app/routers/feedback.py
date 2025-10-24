from fastapi import APIRouter, Depends
from app.utils.security import get_user_id_from_token
from app.services import feedback_service
from app.models.feedback import OptimizationResponse

router = APIRouter(prefix="/feedback", tags=["AI Optimization Feedback"])

@router.post("/optimize-expenses", response_model=OptimizationResponse)
async def get_expense_optimization(user_id: str = Depends(get_user_id_from_token)):
    """
    Triggers a deep-dive analysis of the user's expenses and returns
    a structured report with actionable insights and suggestions.
    """
    report = await feedback_service.get_expense_optimization_feedback(user_id)
    return report

@router.post("/optimize-budget", response_model=OptimizationResponse)
async def get_budget_optimization(user_id: str = Depends(get_user_id_from_token)):
    """
    Triggers a deep-dive analysis of the user's spending against their budgets
    and returns a structured report with actionable insights.
    """
    report = await feedback_service.get_budget_optimization_feedback(user_id)
    return report

@router.post("/optimize-debt", response_model=OptimizationResponse)
async def get_debt_optimization(user_id: str = Depends(get_user_id_from_token)):
    """
    Triggers a deep-dive analysis of the user's debts and returns a
    structured report comparing payoff strategies like Avalanche and Snowball.
    """
    report = await feedback_service.get_debt_optimization_feedback(user_id)
    return report