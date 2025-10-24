from fastapi import APIRouter, Depends, BackgroundTasks
from app.utils.security import get_user_id_from_token
from app.db import queries as db_queries
from app.services import suggestion_service
from app.models.suggestion import SuggestionResponse

router = APIRouter(prefix="/suggestions", tags=["AI Suggestions"])

@router.get("", response_model=SuggestionResponse)
async def get_user_suggestions(user_id: str = Depends(get_user_id_from_token)):
    """
    Fetches the latest set of AI-generated suggestions for the authenticated user.
    """
    suggestions = await db_queries.get_latest_suggestions(user_id)
    return {"suggestions": suggestions}

@router.post("/generate")
async def trigger_suggestion_generation(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id_from_token)
):
    """
    Manually triggers the AI suggestion generation process for the user.
    This runs in the background so the user gets an immediate response.
    In production, this logic would be run by a scheduled job (e.g., nightly).
    """
    background_tasks.add_task(suggestion_service.generate_and_save_suggestions, user_id)
    return {"message": "Suggestion generation process has been started in the background."}