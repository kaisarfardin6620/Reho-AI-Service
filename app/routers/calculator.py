import asyncio
from fastapi import APIRouter, Depends
from app.utils.security import get_user_id_from_token
from app.db import queries as db_queries
from app.models.calculator import CalculatorTipsResponse
from app.services import feedback_service
from loguru import logger

router = APIRouter(prefix="/calculator", tags=["Financial Calculator"])


async def get_precalculated_calculator_tips(user_id: str) -> dict:
    tips_data = await db_queries.get_latest_calculator_tips(user_id)
    if not tips_data:
        tips_data = {
            "savingsTip": "Tip will be available after the midnight analysis.",
            "loanTip": "Tip will be available after the midnight analysis.",
            "futureValueTip": "Tip will be available after the midnight analysis.",
            "historicalTip": "Tip will be available after the midnight analysis."
        }
    return tips_data


@router.get("/tips", response_model=CalculatorTipsResponse)
async def get_scheduled_calculator_tips(
    user_id: str = Depends(get_user_id_from_token) 
):
    cached_tips = await get_precalculated_calculator_tips(user_id)
    
    savings_input_task = db_queries.get_latest_savings_input(user_id)
    loan_input_task = db_queries.get_latest_loan_input(user_id)
    future_input_task = db_queries.get_latest_future_value_input(user_id)
    hist_input_task = db_queries.get_latest_historical_input(user_id)
    
    results = await asyncio.gather(
        savings_input_task, 
        loan_input_task, 
        future_input_task, 
        hist_input_task
    )
    
    latest_savings, latest_loan, latest_future, latest_hist = results
    
    ai_tasks = []
    task_map = {}

    if latest_savings:
        t = feedback_service.generate_instant_tip_from_db(user_id, 'savings', latest_savings)
        ai_tasks.append(t)
        task_map[len(ai_tasks)-1] = "savingsTip"
        
    if latest_loan:
        t = feedback_service.generate_instant_tip_from_db(user_id, 'loan', latest_loan)
        ai_tasks.append(t)
        task_map[len(ai_tasks)-1] = "loanTip"

    if latest_future:
        t = feedback_service.generate_instant_tip_from_db(user_id, 'inflation_future', latest_future)
        ai_tasks.append(t)
        task_map[len(ai_tasks)-1] = "futureValueTip"
        
    if latest_hist:
        t = feedback_service.generate_instant_tip_from_db(user_id, 'historical', latest_hist)
        ai_tasks.append(t)
        task_map[len(ai_tasks)-1] = "historicalTip"

    if ai_tasks:
        ai_results = await asyncio.gather(*ai_tasks)
        
        for i, tip_text in enumerate(ai_results):
            key = task_map[i]
            cached_tips[key] = tip_text

    return CalculatorTipsResponse(**cached_tips)