from fastapi import APIRouter, Depends
from app.utils.security import get_user_id_from_token
from app.db import queries as db_queries
from app.models.calculator import FinancialTipResponse
from loguru import logger

router = APIRouter(prefix="/calculator", tags=["Financial Calculator"])


async def get_precalculated_savings_tip(user_id: str) -> str:
    
    tip_text = await db_queries.get_latest_savings_tip(user_id)
    
    if not tip_text:
        tip_text = "Your daily scheduled savings tip will be available after 00:00 UTC."

    return tip_text


@router.get("/savings-tip", response_model=FinancialTipResponse)
async def get_scheduled_savings_tip(
    user_id: str = Depends(get_user_id_from_token) 
):
    tip_text = await get_precalculated_savings_tip(user_id)
    
    return FinancialTipResponse(tip=tip_text)