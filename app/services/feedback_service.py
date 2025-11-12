import json
import asyncio
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics

openai.api_key = settings.OPENAI_API_KEY


@retry_openai(max_retries=3)
@track_openai_metrics()
async def _get_report_from_ai_and_save(user_id: str, report_type: str, prompt_builder_func) -> bool:
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)

        if report_type == 'expense' and not financial_summary.get("expenses"): return False
        if report_type == 'budget' and not financial_summary.get("budgets"): return False
        if report_type == 'debt' and not financial_summary.get("debts"): return False
        

        optimization_prompt = prompt_builder_func(financial_summary)

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=optimization_prompt,
            response_format={"type": "json_object"} 
        )
        
        report = json.loads(response.choices[0].message.content)
        await db_queries.save_optimization_report(user_id, report_type, report)
        
        logger.info(f"Successfully generated and saved {report_type} report for user {user_id}.")
        return True
        
    except Exception as e:
        logger.exception(f"Error generating and saving {report_type} optimization report for user {user_id}: {e}")
        return False


async def generate_optimization_reports_for_all_users():
    logger.info("Optimization reports background task TRIGGERED.")
    try:
        users = await db_queries.get_all_active_users()
        
        if not users:
            logger.info("No active users found to process.")
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
        logger.exception(f"FATAL ERROR in optimization background task loop: {e}")

    logger.info("Optimization task finished.")


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