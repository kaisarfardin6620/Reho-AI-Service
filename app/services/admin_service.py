import asyncio
import json
from app.db import queries as db_queries
from app.ai import prompt_builder
from app.models.admin import AdminUserAIDashboard, SpendingHeatmapItem, InstallmentLoanInfo, PeerComparison 
from app.models.feedback import OptimizationInsight
from openai import AsyncOpenAI
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics
from typing import List, Dict

aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

@retry_openai(max_retries=3)
@track_openai_metrics()
async def _run_anomaly_detection_ai(financial_summary: dict):
    anomaly_prompt = prompt_builder.build_anomaly_detection_prompt(financial_summary)
    response = await aclient.chat.completions.create(
        model="gpt-4o",
        messages=anomaly_prompt,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

@retry_openai(max_retries=3)
@track_openai_metrics()
async def _run_peer_comparison_ai(financial_summary: dict) -> PeerComparison:
    try:
        comparison_prompt = prompt_builder.build_peer_comparison_prompt(financial_summary)
        response = await aclient.chat.completions.create(
            model="gpt-4o",
            messages=comparison_prompt,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return PeerComparison(**data)
    except Exception as e:
        logger.warning(f"Failed to generate Peer Comparison: {e}")
        return PeerComparison(comparison="Peer comparison data is temporarily unavailable.")

async def process_single_user_admin_job(user, semaphore):
    async with semaphore:
        user_id = str(user["_id"])
        user_email = user.get("email", "N/A")
        try:
            financial_summary = await db_queries.get_user_financial_summary(user_id)
            
            if not financial_summary.get("incomes") and not financial_summary.get("expenses"):
                return

            alert_data = await _run_anomaly_detection_ai(financial_summary)
            
            if alert_data and "alertMessage" in alert_data:
                await db_queries.save_admin_alert(
                    user_id=user_id,
                    user_email=user_email,
                    alert_message=alert_data["alertMessage"],
                    category=alert_data["category"]
                )
                logger.warning(f"!!! Alert generated for user {user_email}: {alert_data['alertMessage']}")
        except Exception as e:
            logger.exception(f"Error processing user {user_id} in admin job: {e}")

async def run_analysis_for_all_users():
    logger.info("Starting analysis job for all users...")
    
    active_tasks = set()
    MAX_CONCURRENT_USERS = 10
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_USERS)

    async for user in db_queries.get_all_active_users_cursor():
        if len(active_tasks) >= MAX_CONCURRENT_USERS:
            done, pending = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
            active_tasks = pending
        
        task = asyncio.create_task(process_single_user_admin_job(user, semaphore))
        active_tasks.add(task)
    
    if active_tasks:
        await asyncio.wait(active_tasks)
    
    logger.info("Finished analysis job for all users.")

def _calculate_category_spend(expenses: List[Dict]) -> Dict[str, float]:
    category_totals = {}
    for expense in expenses:
        name = expense.get('name', 'Others')
        amount = expense.get('amount', 0)
        category_totals[name] = category_totals.get(name, 0.0) + amount
    return category_totals

async def get_single_user_admin_dashboard(user_id: str) -> AdminUserAIDashboard:
    alerts_task = db_queries.get_latest_admin_alerts_for_user(user_id)
    expense_task = db_queries.get_latest_optimization_report(user_id, "expense")
    budget_task = db_queries.get_latest_optimization_report(user_id, "budget")
    debt_task = db_queries.get_latest_optimization_report(user_id, "debt")
    summary_task = db_queries.get_user_financial_summary(user_id)
    
    financial_summary = await summary_task
    peer_task = _run_peer_comparison_ai(financial_summary) 

    results = await asyncio.gather(alerts_task, expense_task, budget_task, debt_task, peer_task)
    
    latest_alerts, expense_report, budget_report, debt_report, peer_comparison = results
    
    all_ai_tips: List[OptimizationInsight] = []
    for report in [expense_report, budget_report, debt_report]:
        if report and isinstance(report.get("insights"), list):
            for insight_data in report["insights"]:
                try:
                    all_ai_tips.append(OptimizationInsight(**insight_data))
                except Exception as e:
                    logger.error(f"Error validating insight data: {e}")

    total_debts = sum(d.get("amount", 0) for d in financial_summary.get("debts", []))
    total_income = sum(i.get("amount", 0) for i in financial_summary.get("incomes", []))
    total_payments = sum(d.get("monthlyPayment", 0) for d in financial_summary.get("debts", []))

    missed_count = 0
    if total_income > 0 and (total_payments / total_income) > 0.40:
        overall_status = "High Risk"
    elif total_payments > 0:
        overall_status = "Medium Risk"
    else:
        overall_status = "Low Risk"
    
    installment_loan_info = InstallmentLoanInfo(
        missed_installments=missed_count, 
        next_due_date="N/A",
        status=overall_status
    )
    category_totals = _calculate_category_spend(financial_summary.get("expenses", []))
    total_expense = sum(category_totals.values())
    
    spending_heatmap_data = []
    
    if total_expense > 0:
        high_threshold = total_expense * 0.25
        low_threshold = total_expense * 0.05

        for category, amount in category_totals.items():
            level = "Moderate"
            if amount >= high_threshold:
                level = "High"
            elif amount <= low_threshold:
                level = "Low"
            
            spending_heatmap_data.append(SpendingHeatmapItem(category=category, spendingLevel=level))
    
    required_categories = ["Food", "Transport", "Shopping", "Utility Bills", "Others"]
    existing_categories = [item.category for item in spending_heatmap_data]
    for category in required_categories:
        if category not in existing_categories:
            spending_heatmap_data.append(SpendingHeatmapItem(category=category, spendingLevel="Low"))

    return AdminUserAIDashboard(
        total_monthly_spending=total_expense,
        top_overspending_categories=["Food", "Shopping", "Subscriptions"],
        spending_growth_from_last_month="12%",
        spending_heatmap=spending_heatmap_data,
        current_alerts=latest_alerts,
        ai_tips=all_ai_tips,
        debt_statuses=installment_loan_info, 
        peer_comparison=peer_comparison      
    )