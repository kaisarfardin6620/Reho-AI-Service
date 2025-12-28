import json
import asyncio
from app.db import queries as db_queries
from app.ai import prompt_builder
from openai import AsyncOpenAI
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics
from typing import List, Dict, Optional

aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


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
        
        response = await aclient.chat.completions.create(
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

async def process_user_reports(user, semaphore):
    async with semaphore:
        user_id = str(user["_id"])
        try:
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
        except Exception as e:
            logger.error(f"Error processing reports for user {user_id}: {e}")

async def generate_optimization_reports_for_all_users():
    logger.info("Optimization reports background task TRIGGERED.")
    try:
        users = await db_queries.get_all_active_users()
        
        if not users:
            logger.info("No active users found to process.")
            return

        semaphore = asyncio.Semaphore(5)
        tasks = [process_user_reports(user, semaphore) for user in users]
        
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.exception(f"FATAL ERROR in optimization background task loop: {e}")

    logger.info("Optimization task finished.")


@retry_openai(max_retries=3)
@track_openai_metrics()
async def _get_single_calculator_tip(user_id: str, builder_func, mock_data_type: str, custom_data: Optional[dict] = None) -> str:
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id)
        
        if custom_data:
            prompt = builder_func(user_id, custom_data, financial_summary)
        else:
            if mock_data_type == 'savings':
                mock_data = {"amount": 500.0, "frequency": "Monthly", "returnRate": 5.0, "years": 10.0, "taxRate": 20.0}
            elif mock_data_type == 'loan':
                mock_data = {"principal": 10000.0, "annualInterestRate": 5.0, "loanTermYears": 5.0}
            elif mock_data_type == 'inflation_future':
                mock_data = {"initialAmount": 1000.0, "annualInflationRate": 3.0, "yearsToProject": 5.0}
            else:
                mock_data = {"fromYear": 2021, "toYear": 2025, "amount": 100.0}
            
            prompt = builder_func(user_id, mock_data, financial_summary)
            
        response = await aclient.chat.completions.create(
            model="gpt-4o", messages=prompt, response_format={"type": "json_object"}
        )
        tip_data = json.loads(response.choices[0].message.content)
        return tip_data.get("tip", "Could not generate a specialized tip for this calculator.")
    
    except Exception as e:
        logger.exception(f"AI Failed to generate {mock_data_type} tip for user {user_id}: {e}")
        return "An error occurred while generating your tip. Please try again later."


async def generate_instant_tip_from_db(user_id: str, tip_type: str, db_data: dict) -> str:
    if tip_type == 'historical':
         return await _get_single_calculator_tip(user_id, prompt_builder.build_historical_tip_prompt, 'historical', custom_data=db_data)
    elif tip_type == 'inflation_future':
        return await _get_single_calculator_tip(user_id, prompt_builder.build_inflation_tip_prompt, 'inflation_future', custom_data=db_data)
    elif tip_type == 'savings':
        return await _get_single_calculator_tip(user_id, prompt_builder.build_savings_tip_prompt, 'savings', custom_data=db_data)
    elif tip_type == 'loan':
        return await _get_single_calculator_tip(user_id, prompt_builder.build_loan_tip_prompt, 'loan', custom_data=db_data)
    
    return "Tip type not supported."


async def process_user_tips(user, semaphore):
    async with semaphore:
        user_id = str(user["_id"])
        try:
            savings_task = _get_single_calculator_tip(user_id, prompt_builder.build_savings_tip_prompt, 'savings')
            loan_task = _get_single_calculator_tip(user_id, prompt_builder.build_loan_tip_prompt, 'loan') 
            future_task = _get_single_calculator_tip(user_id, prompt_builder.build_inflation_tip_prompt, 'inflation_future') 
            historical_task = _get_single_calculator_tip(user_id, prompt_builder.build_historical_tip_prompt, 'historical') 

            results = await asyncio.gather(savings_task, loan_task, future_task, historical_task)
            
            tips_data = {
                "savingsTip": results[0],
                "loanTip": results[1],
                "futureValueTip": results[2],
                "historicalTip": results[3]
            }
            await db_queries.save_calculator_tips(user_id, tips_data)
            logger.info(f"Successfully generated and saved all 4 calculator tips for user {user_id}.")
        except Exception as e:
             logger.error(f"Error processing tips for user {user_id}: {e}")

async def generate_savings_tip_for_all_users():
    logger.info("Calculator tips background task TRIGGERED.")
    try:
        users = await db_queries.get_all_active_users()
        
        if not users:
            logger.info("No active users found to process.")
            return
            
        semaphore = asyncio.Semaphore(5)
        tasks = [process_user_tips(user, semaphore) for user in users]
        
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.exception(f"FATAL ERROR in calculator tip background task loop: {e}")

    logger.info("Calculator tips task finished.")


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