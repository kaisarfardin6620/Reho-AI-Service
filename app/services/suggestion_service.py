import json
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY

async def generate_and_save_suggestions(user_id: str):
    """
    The core logic for the suggestion feature. Fetches data, gets suggestions
    from the AI, and saves them to the database.
    """
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)

        suggestion_prompt = prompt_builder.build_suggestion_generation_prompt(financial_summary)

        response = openai.chat.completions.create(
            model="gpt-4-turbo", 
            messages=suggestion_prompt,
            response_format={"type": "json_object"}
        )
        
        suggestions_str = response.choices[0].message.content
        suggestions = json.loads(suggestions_str)

        await db_queries.save_suggestions(user_id, suggestions)
        
        return {"status": "success", "message": f"{len(suggestions)} suggestions generated and saved."}
        
    except Exception as e:
        print(f"Error in suggestion generation service: {e}")
        return {"status": "error", "message": str(e)}