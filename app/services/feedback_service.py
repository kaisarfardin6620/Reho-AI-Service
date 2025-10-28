
import json
import asyncio
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY


async def _get_report_from_ai_and_save(user_id: str, report_type: str, prompt_builder_func) -> bool:
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)

        if report_type == 'expense' and not financial_summary.get("expenses"): return False
        if report_type == 'budget' and not financial_summary.get("budgets"): return False
        if report_type == 'debt' and not financial_summary.get("debts"): return False
        
        if financial_summary.get("error"):
            print(f"Skipping {report_type} for user {user_id} due to invalid ID/error.")
            return False

        optimization_prompt = prompt_builder_func(financial_summary)

        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=optimization_prompt,
            response_format={"type": "json_object"} 
        )
        
        report = json.loads(response.choices[0].message.content)
        await db_queries.save_optimization_report(user_id, report_type, report)
        
        print(f"Successfully generated and saved {report_type} report for user {user_id}.")
        return True
        
    except Exception as e:
        print(f"Error generating and saving {report_type} optimization report for user {user_id}: {e}")
        return False


async def generate_optimization_reports_for_all_users():
    print("\n--- DEBUG: Optimization reports background task TRIGGERED. ---")
    try:
        users = await db_queries.get_all_active_users()
        
        if not users:
            print("--- DEBUG: No active users found to process. ---")
            return
            
        for user in users:
            user_id = str(user["_id"])
            
            await asyncio.gather(
                _get_report_from_ai_and_save(user_id, 'expense', prompt_builder.build_expense_optimization_prompt),
                _get_report_from_ai_and_save(user_id, 'budget', prompt_builder.build_budget_optimization_prompt),
                _get_report_from_ai_and_save(user_id, 'debt', prompt_builder.build_debt_optimization_prompt)
            )
            await asyncio.sleep(1)

    except Exception as e:
        print(f"--- DEBUG: FATAL ERROR in optimization background task loop: {e} ---")

    print("--- DEBUG: Optimization task finished. ---")



async def get_expense_optimization_feedback(user_id: str) -> dict:
    report = await db_queries.get_latest_optimization_report(user_id, "expense")
    if report:
        return report
    
    return {
        "summary": "Report not yet generated for today. Please check back later.",
        "insights": []
    }


async def get_budget_optimization_feedback(user_id: str) -> dict:
    report = await db_queries.get_latest_optimization_report(user_id, "budget")
    if report:
        return report
    
    return {
        "summary": "Report not yet generated for today. Please check back later.",
        "insights": []
    }    
    

async def get_debt_optimization_feedback(user_id: str) -> dict:
    report = await db_queries.get_latest_optimization_report(user_id, "debt")
    if report:
        return report
    
    return {
        "summary": "Report not yet generated for today. Please check back later.",
        "insights": []
    }