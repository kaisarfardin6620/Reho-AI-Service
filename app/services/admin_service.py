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


def _calculate_category_spend(expenses: List[Dict]) -> Dict[str, float]:
    category_totals = {}
    for expense in expenses:
        name = expense.get('budgetCategory') or expense.get('name') or 'Others'
        amount = float(expense.get('amount') or 0)
        category_totals[name] = category_totals.get(name, 0.0) + amount
    return category_totals


async def get_single_user_admin_dashboard(user_id: str) -> AdminUserAIDashboard:
    alerts_task = asyncio.create_task(db_queries.get_latest_admin_alerts_for_user(user_id))
    expense_task = asyncio.create_task(db_queries.get_latest_optimization_report(user_id, "expense"))
    budget_task = asyncio.create_task(db_queries.get_latest_optimization_report(user_id, "budget"))
    debt_task = asyncio.create_task(db_queries.get_latest_optimization_report(user_id, "debt"))
    summary_task = asyncio.create_task(db_queries.get_user_financial_summary(user_id))

    financial_summary = await summary_task

    peer_task = asyncio.create_task(_run_peer_comparison_ai(financial_summary))

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

    total_income = sum(i.get("amount", 0) for i in financial_summary.get("incomes", []))
    total_payments = sum(d.get("monthlyPayment", 0) for d in financial_summary.get("debts", []))

    missed_count = 0  # TODO:
    if total_income > 0 and total_payments > 0 and (total_payments / total_income) > 0.40:
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

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    top_overspending_categories = [cat for cat, _ in sorted_categories[:3]] if sorted_categories else []

    return AdminUserAIDashboard(
        total_monthly_spending=total_expense,
        top_overspending_categories=top_overspending_categories,
        spending_growth_from_last_month="0%",
        spending_heatmap=spending_heatmap_data,
        current_alerts=latest_alerts,
        ai_tips=all_ai_tips,
        debt_statuses=installment_loan_info,
        peer_comparison=peer_comparison
    )