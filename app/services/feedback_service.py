import json
import asyncio
from app.db import queries as db_queries
from app.ai import prompt_builder
from app.models.feedback import OptimizationResponse, OptimizationInsight
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics
from typing import Optional

aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class TipResponse(BaseModel):
    tip: str

def _dict_to_optimization_response(data: dict) -> OptimizationResponse:
    if isinstance(data, OptimizationResponse):
        return data
    return OptimizationResponse(
        summary=data.get("summary", ""),
        insights=[
            OptimizationInsight(**i) if isinstance(i, dict) else i
            for i in data.get("insights", [])
        ]
    )


def _fallback_response(message: str) -> OptimizationResponse:
    return OptimizationResponse(summary=message, insights=[])


@retry_openai(max_retries=3)
@track_openai_metrics()
async def _get_report_from_ai_and_save(
    user_id: str,
    report_type: str,
    prompt_builder_func,
    analysis_data: dict = None
) -> bool:
    try:
        if report_type == 'budget' and analysis_data:
            optimization_prompt = prompt_builder_func(analysis_data)
        else:
            financial_summary = await db_queries.get_user_financial_summary(user_id, skip_cache=True, time_frame='current_month')
            if report_type == 'expense' and not financial_summary.get("expenses"):
                return False
            if report_type == 'debt' and not financial_summary.get("debts"):
                return False
            optimization_prompt = prompt_builder_func(financial_summary)

        response = await aclient.beta.chat.completions.parse(
            model="gpt-4o",
            messages=optimization_prompt,
            response_format=OptimizationResponse
        )

        report = response.choices[0].message.parsed.model_dump()
        await db_queries.save_optimization_report(user_id, report_type, report)

        logger.info(f"Successfully generated and saved {report_type} report for user {user_id}.")
        return True

    except Exception as e:
        logger.exception(f"Error generating and saving {report_type} optimization report for user {user_id}: {e}")
        return False


def _calculate_weighted_savings_progress(saving_goals: list) -> float:
    if not saving_goals:
        return 0.0
    
    total_goal_amount = sum(float(sg.get("totalAmount") or 0) for sg in saving_goals)
    if total_goal_amount == 0:
        return 0.0
        
    weighted_sum = sum(
        float(sg.get("completionRatio") or 0) * float(sg.get("totalAmount") or 0)
        for sg in saving_goals
    )
    return weighted_sum / total_goal_amount

def _map_to_50_30_20(financial_summary: dict) -> dict:
    total_income = sum(float(i.get("amount") or 0) for i in financial_summary.get("incomes", []))
    total_expenses = sum(float(e.get("amount") or 0) for e in financial_summary.get("expenses", []))

    actual_essential = 0.0
    actual_discretionary = 0.0
    actual_savings = 0.0

    # Primary source: Use BUDGETS with category field for accurate classification
    for item in financial_summary.get("budgets", []):
        amount = float(item.get('amount') or 0)
        category = str(item.get('category', '')).strip().lower()

        if 'essential' in category or 'needs' in category:
            actual_essential += amount
        elif 'discretionary' in category or 'wants' in category:
            actual_discretionary += amount
        elif 'saving' in category:
            actual_savings += amount

    # Fallback: If no budgets, use expenses with budgetCategory field
    if not financial_summary.get("budgets"):
        for item in financial_summary.get("expenses", []):
            amount = float(item.get('amount') or 0)
            category_type = str(item.get('budgetCategory', '')).strip().lower()

            if 'essential' in category_type or category_type == 'needs':
                actual_essential += amount
            elif 'discretionary' in category_type or category_type == 'wants':
                actual_discretionary += amount
            elif 'saving' in category_type:
                actual_savings += amount
            else:
                name = item.get('name', '').lower()
                if any(keyword in name for keyword in ['rent', 'mortgage', 'utility', 'bill', 'grocery', 'insurance', 'loan', 'debt', 'payment']):
                    actual_essential += amount
                elif any(keyword in name for keyword in ['netflix', 'spotify', 'dining', 'entertainment', 'shopping', 'hobby', 'travel']):
                    actual_discretionary += amount
                else:
                    actual_discretionary += amount

    for item in financial_summary.get("debts", []):
        monthly = float(item.get('monthlyPayment') or 0)
        actual_essential += monthly

    actual_savings += sum(float(s.get('monthlyTarget') or 0) for s in financial_summary.get('saving_goals', []))

    disposable_income = total_income - total_expenses
    
    savings_progress = _calculate_weighted_savings_progress(financial_summary.get("saving_goals", []))

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "disposable_income": disposable_income,
        "actual_essential": actual_essential,
        "actual_discretionary": actual_discretionary,
        "actual_savings": actual_savings,
        "overall_savings_progress": savings_progress
    }

@retry_openai(max_retries=3)
@track_openai_metrics()
async def _get_single_calculator_tip(
    user_id: str,
    builder_func,
    mock_data_type: str,
    custom_data: Optional[dict] = None
) -> str:
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id, skip_cache=True, time_frame='current_month')

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

        response = await aclient.beta.chat.completions.parse(
            model="gpt-4o",
            messages=prompt,
            response_format=TipResponse
        )
        tip_data = response.choices[0].message.parsed.model_dump()
        return tip_data.get("tip", "Could not generate a specialised tip for this calculator.")

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

    logger.warning(f"generate_instant_tip_from_db called with unsupported tip_type='{tip_type}' for user {user_id}")
    return "Tip type not supported."

async def get_expense_optimization_feedback(user_id: str) -> OptimizationResponse:
    logger.info(f"Generating fresh expense optimization report for {user_id}.")
    success = await _get_report_from_ai_and_save(user_id, 'expense', prompt_builder.build_expense_optimization_prompt)

    if success:
        report = await db_queries.get_latest_optimization_report(user_id, "expense")
        if report:
            return _dict_to_optimization_response(report)

    return _fallback_response("Report could not be generated. Please ensure you have added expenses.")


async def get_budget_optimization_feedback(user_id: str) -> OptimizationResponse:
    logger.info(f"Generating fresh budget optimization report for {user_id}.")
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id, skip_cache=True, time_frame='current_month')
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

        success = await _get_report_from_ai_and_save(
            user_id, 'budget',
            prompt_builder.build_budget_optimization_prompt,
            analysis_data=budget_analysis_data
        )

        if success:
            report = await db_queries.get_latest_optimization_report(user_id, "budget")
            if report:
                return _dict_to_optimization_response(report)

    except Exception as e:
        logger.error(f"Failed to generate budget report on demand: {e}")

    return _fallback_response("Report not yet generated. Please ensure you have set up income and budgets.")


async def get_debt_optimization_feedback(user_id: str) -> OptimizationResponse:
    logger.info(f"Generating fresh debt optimization report for {user_id}.")
    success = await _get_report_from_ai_and_save(user_id, 'debt', prompt_builder.build_debt_optimization_prompt)

    if success:
        report = await db_queries.get_latest_optimization_report(user_id, "debt")
        if report:
            return _dict_to_optimization_response(report)

    return _fallback_response("Report could not be generated. Please ensure you have added debts.")