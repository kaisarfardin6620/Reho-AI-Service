import asyncio
import json
from app.db import queries as db_queries
from app.ai import prompt_builder
from app.models.admin import AdminUserAIDashboard, DebtStatusItem, SpendingHeatmapItem
from app.models.feedback import OptimizationInsight
import openai
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics

openai.api_key = settings.OPENAI_API_KEY


@retry_openai(max_retries=3)
@track_openai_metrics()
async def _run_anomaly_detection_ai(financial_summary: dict):
    anomaly_prompt = prompt_builder.build_anomaly_detection_prompt(financial_summary)
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=anomaly_prompt,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


async def run_analysis_for_all_users():
    logger.info("Starting analysis job for all users...")
    all_users = await db_queries.get_all_active_users()
    
    for user in all_users:
        user_id = str(user["_id"])
        user_email = user.get("email", "N/A")
        logger.info(f"Analyzing data for user: {user_email} ({user_id})")

        try:
            financial_summary = await db_queries.get_user_financial_summary(user_id)
            
            if not financial_summary.get("incomes") and not financial_summary.get("expenses"):
                continue

            alert_data = await _run_anomaly_detection_ai(financial_summary)
            
            if alert_data and "alertMessage" in alert_data:
                await db_queries.save_admin_alert(
                    user_id=user_id,
                    user_email=user_email,
                    alert_message=alert_data["alertMessage"],
                    category=alert_data["category"]
                )
                logger.warning(f"!!! Alert generated for user {user_email}: {alert_data['alertMessage']}")
            
            await asyncio.sleep(1)

        except Exception as e:
            logger.exception(f"Error processing user {user_id}: {e}")
            continue 
    
    logger.info("Finished analysis job for all users.")


async def get_single_user_admin_dashboard(user_id: str) -> AdminUserAIDashboard:
    alerts_task = db_queries.get_latest_admin_alerts_for_user(user_id)
    expense_task = db_queries.get_latest_optimization_report(user_id, "expense")
    budget_task = db_queries.get_latest_optimization_report(user_id, "budget")
    debt_task = db_queries.get_latest_optimization_report(user_id, "debt")
    summary_task = db_queries.get_user_financial_summary(user_id)
    
    results = await asyncio.gather(alerts_task, expense_task, budget_task, debt_task, summary_task)
    
    latest_alerts, expense_report, budget_report, debt_report, financial_summary = results
    
    all_ai_tips: List[OptimizationInsight] = []
    
    for report in [expense_report, budget_report, debt_report]:
        if report and isinstance(report.get("insights"), list):
            for insight_data in report["insights"]:
                try:
                    all_ai_tips.append(OptimizationInsight(**insight_data))
                except Exception as e:
                    logger.error(f"Error validating insight data: {e}")

    debt_statuses = []
    if financial_summary.get("debts"):
        for debt in financial_summary["debts"]:
            status = "On Track"
            if debt.get("monthlyPayment", 0) == 0:
                status = "Missing Payment"
            elif debt.get("amount", 0) > 10000:
                status = "High Risk"
            
            debt_statuses.append(DebtStatusItem(name=debt["name"], status=status))


    spending_heatmap_data = [
        SpendingHeatmapItem(category="Food", spending_level="High"),
        SpendingHeatmapItem(category="Transport", spending_level="Low"),
        SpendingHeatmapItem(category="Shopping", spending_level="Moderate"),
    ]

    return AdminUserAIDashboard(
        total_monthly_spending=sum(e.get("amount", 0) for e in financial_summary.get("expenses", [])),
        top_overspending_categories=["Food", "Shopping", "Subscriptions"],
        spending_growth_from_last_month="12%",

        spending_heatmap=spending_heatmap_data,
        
        current_alerts=latest_alerts,
        ai_tips=all_ai_tips,

        debt_statuses=debt_statuses
    )