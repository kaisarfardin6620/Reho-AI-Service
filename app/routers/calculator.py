from fastapi import APIRouter, Depends
from app.utils.security import get_user_id_from_token
from app.db import queries as db_queries
from app.models.calculator import CalculatorTipsResponse # NOTE: Using the new multi-tip response model
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
    tips_data = await get_precalculated_calculator_tips(user_id)
    
    return CalculatorTipsResponse(**tips_data)