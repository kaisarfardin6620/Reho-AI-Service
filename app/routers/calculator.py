from fastapi import APIRouter, Depends
from app.utils.security import get_user_id_from_token
from app.db import queries as db_queries
from app.ai import prompt_builder
from app.models.calculator import FinancialTipResponse
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics
import openai
from app.core.config import settings
import json

router = APIRouter(prefix="/calculator", tags=["Financial Calculator"])
openai.api_key = settings.OPENAI_API_KEY


async def get_precalculated_savings_tip(user_id: str) -> str:
    
    return "Your daily scheduled savings tip will be available after 00:00 UTC."


@router.get("/savings-tip", response_model=FinancialTipResponse)
async def get_scheduled_savings_tip(
    user_id: str = Depends(get_user_id_from_token) 
):
    tip_text = await get_precalculated_savings_tip(user_id)
    
    return FinancialTipResponse(tip=tip_text)