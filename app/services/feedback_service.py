import json
import asyncio
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics
from typing import List, Dict

openai.api_key = settings.OPENAI_API_KEY


@retry_openai(max_retries=3)
@track_openai_metrics()
async def _get_report_from_ai_and_save(user_id: str, report_type: str, prompt_builder_func, analysis_data: dict = None) -> bool:
    try:
        if report_type == 'budget' and analysis_data:
            optimization_prompt = prompt_builder_func(analysis_data)
        else:
            financial_summary = await db_queries.get_user_financial_summary(user_id)
            if report_type == 'expense' and not financial_summary.get("expenses"): return False
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


def _map_to_50_30_20(financial_summary: dict) -> dict:
    
    total_income = sum(i.get("amount", 0) for i in financial_summary.get("incomes", []))
    
    actual_essential = 0.0
    actual_discretionary = 0.0
    actual_savings = 0.0
    
    all_commitments = financial_summary.get("expenses", []) + financial_summary.get("debts", [])
    
    for item in all_commitments:
        name = item.get('name', '').lower()
        amount = item.get('amount') or item.get('monthlyPayment', 0)
        
        if any(keyword in name for keyword in ['rent', 'mortgage', 'utility', 'bill', 'grocery', 'insurance', 'loan', 'debt', 'payment']):
            actual_essential += amount
        elif any(keyword in name for keyword in ['netflix', 'spotify', 'dining', 'entertainment', 'shopping', 'hobby', 'travel']):
            actual_discretionary += amount
        
    actual_savings = sum(s.get('monthlyTarget', 0) for s in financial_summary.get('saving_goals', []))
    
    total_commitments = actual_essential + actual_discretionary + actual_savings

    return {
        "total_income": total_income,
        "total_commitments": total_commitments,
        "actual_essential": actual_essential,
        "actual_discretionary": actual_discretionary,
        "actual_savings": actual_savings
    }


async def generate_optimization_reports_for_all_users():
    logger.info("Optimization reports background task TRIGGERED.")
    try:
        users = await db_queries.get_all_active_users()
        
        if not users:
            logger.info("No active users found to process.")
            return
            
        for user in users:
            user_id = str(user["_id"])
            
            financial_summary = await db_queries.get_user_financial_summary(user_id)
            
            analysis_map = _map_to_50_30_20(financial_summary)
            total_income = analysis_map["total_income"]
            
            if total_income > 0:
                analysis_map["percent_essential"] = (analysis_map["actual_essential"] / total_income) * 100
                analysis_map["percent_discretionary"] = (analysis_map["actual_discretionary"] / total_income) * 100
                analysis_map["percent_savings"] = (analysis_map["actual_savings"] / total_income) * 100
            else:
                analysis_map["percent_essential"] = 0
                analysis_map["percent_discretionary"] = 0
                analysis_map["percent_savings"] = 0
                
            budget_analysis_data = {
                "name": financial_summary.get('name', 'there'),
                "financial_summary": financial_summary,
                **analysis_map 
            }
            
            await asyncio.gather(
                _get_report_from_ai_and_save(user_id, 'expense', prompt_builder.build_expense_optimization_prompt),
                _get_report_from_ai_and_save(user_id, 'budget', prompt_builder.build_budget_optimization_prompt, analysis_data=budget_analysis_data),
                _get_report_from_ai_and_save(user_id, 'debt', prompt_builder.build_debt_optimization_prompt)
            )
            await asyncio.sleep(1)

    except Exception as e:
        logger.exception(f"FATAL ERROR in optimization background task loop: {e}")

    logger.info("Optimization task finished.")


@retry_openai(max_retries=3)
@track_openai_metrics()
async def _get_and_save_savings_tip_for_one_user(user_id: str) -> bool:
    
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)
        
        mock_calc_data = {"amount": 500.0, "frequency": "Monthly", "returnRate": 5.0, "inflationYears": 10.0, "taxationRate": "20% BRT"}
        prompt = prompt_builder.build_savings_tip_prompt(user_id, mock_calc_data, financial_summary)
        
        response = openai.chat.completions.create(
            model="gpt-4o", messages=prompt, response_format={"type": "json_object"}
        )
        tip_data = json.loads(response.choices[0].message.content)
        tip_text = tip_data.get("tip", "A generic savings tip is: Review high-interest debts before starting new savings goals.")
        
        await db_queries.save_savings_tip(user_id, tip_text)
        logger.info(f"Successfully generated and saved savings tip for user {user_id}.")
        return True
    
    except Exception as e:
        logger.exception(f"Error generating and saving savings tip for user {user_id}: {e}")
        return False


async def generate_savings_tip_for_all_users():
    
    logger.info("Savings tip background task TRIGGERED.")
    try:
        users = await db_queries.get_all_active_users()
        
        if not users:
            logger.info("No active users found to process.")
            return
            
        for user in users:
            user_id = str(user["_id"])
            await _get_and_save_savings_tip_for_one_user(user_id)
            await asyncio.sleep(1)

    except Exception as e:
        logger.exception(f"FATAL ERROR in savings tip background task loop: {e}")

    logger.info("Savings tip task finished.")


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