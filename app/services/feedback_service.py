import json
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY

async def get_expense_optimization_feedback(user_id: str) -> dict:
    """
    The core logic for the on-demand expense optimization feature.
    Fetches data, gets a detailed report from the AI, and returns it.
    """
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)
        
        if not financial_summary.get("expenses"):
            return {
                "summary": "Not enough expense data to provide an analysis.",
                "insights": []
            }

        optimization_prompt = prompt_builder.build_expense_optimization_prompt(financial_summary)

        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=optimization_prompt,
            response_format={"type": "json_object"} 
        )
        
        report = json.loads(response.choices[0].message.content)
        return report
        
    except Exception as e:
        print(f"Error in expense optimization service: {e}")
        return {
            "summary": "An error occurred while generating your optimization report.",
            "insights": [{"insight": "Error", "suggestion": str(e), "category": "System"}]
        }
    


async def get_budget_optimization_feedback(user_id: str) -> dict:
    """
    The core logic for the on-demand budget optimization feature.
    """
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)
        
        if not financial_summary.get("budgets"):
            return {
                "summary": "You haven't set up any budgets yet. Add a budget to get an analysis.",
                "insights": []
            }

        optimization_prompt = prompt_builder.build_budget_optimization_prompt(financial_summary)

        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=optimization_prompt,
            response_format={"type": "json_object"}
        )
        
        report = json.loads(response.choices[0].message.content)
        return report
        
    except Exception as e:
        print(f"Error in budget optimization service: {e}")
        return {
            "summary": "An error occurred while generating your budget report.",
            "insights": [{"insight": "Error", "suggestion": str(e), "category": "System"}]
        }    
    

async def get_debt_optimization_feedback(user_id: str) -> dict:
    """
    The core logic for the on-demand debt optimization feature.
    """
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)
        
        if not financial_summary.get("debts"):
            return {
                "summary": "You haven't added any debts yet. Add your debts to get a payoff plan.",
                "insights": []
            }

        optimization_prompt = prompt_builder.build_debt_optimization_prompt(financial_summary)

        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=optimization_prompt,
            response_format={"type": "json_object"}
        )
        
        report = json.loads(response.choices[0].message.content)
        return report
        
    except Exception as e:
        print(f"Error in debt optimization service: {e}")
        return {
            "summary": "An error occurred while generating your debt payoff plan.",
            "insights": [{"insight": "Error", "suggestion": str(e), "category": "System"}]
        }    