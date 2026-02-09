import asyncio
from datetime import datetime, date, timezone
import json
from bson import ObjectId
from .client import db, redis_client
from app.utils.mongo_metrics import track_mongo_operation
from loguru import logger

def safe_serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    return str(obj)

def _clean_mongo_doc(doc: dict, mapping: dict = None) -> dict:
    if not doc:
        return None
    clean_doc = json.loads(json.dumps(doc, default=safe_serialize))
    if mapping:
        for db_key, prompt_key in mapping.items():
            if db_key in clean_doc:
                clean_doc[prompt_key] = clean_doc[db_key]
    return clean_doc

def calculate_implied_interest_rate(debt_doc):
    cap_rep = float(debt_doc.get("capitalRepayment") or 0)
    int_rep = float(debt_doc.get("interestRepayment") or 0)
    total_payment = cap_rep + int_rep
    
    if total_payment > 0:
        return round((int_rep / total_payment) * 100, 2)
    return 0.0

async def get_user_financial_summary(user_id: str) -> dict:
    cache_key = f"user_summary:{user_id}"
    cached_summary = await redis_client.get(cache_key)
    if cached_summary:
        return json.loads(cached_summary)
    
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise ValueError(f"Invalid user_id format provided: {user_id}")
    
    user_task = db.users.find_one({"_id": object_id})
    income_task = db.incomes.find({"userId": object_id, "isDeleted": False}).to_list(length=None)
    expense_task = db.expenses.find({"userId": object_id, "isDeleted": False}).to_list(length=None)
    budget_task = db.budgets.find({"userId": object_id, "isDeleted": False}).to_list(length=None)
    debt_task = db.debts.find({"userId": object_id, "isDeleted": False}).to_list(length=None)
    saving_goal_task = db.savinggoals.find({"userId": object_id, "isDeleted": False}).to_list(length=None)
    subscription_task = db.subscriptions.find_one({"userId": object_id, "status": "active"})
    
    results = await asyncio.gather(
        user_task, income_task, expense_task, budget_task,
        debt_task, saving_goal_task, subscription_task,
        return_exceptions=True
    )
    user, incomes, expenses, budgets, debts, saving_goals, subscription = (
        r for r in results if not isinstance(r, Exception)
    )
    budget_map = {}
    if budgets:
        for b in budgets:
            b_id = str(b.get("_id"))
            budget_map[b_id] = b.get("category") or b.get("name") or "Uncategorized"

    formatted_expenses = []
    if expenses:
        for e in expenses:
            b_id = str(e.get("budgetId")) if e.get("budgetId") else None
            category_name = budget_map.get(b_id, "Others")
            
            formatted_expenses.append({
                "name": e.get("name"),
                "amount": e.get("amount"),
                "frequency": e.get("frequency"),
                "budgetCategory": category_name 
            })

    formatted_debts = []
    if debts:
        for d in debts:
            stored_rate = d.get("userInterestRate")
            if stored_rate is not None:
                rate = float(stored_rate)
            else:
                rate = calculate_implied_interest_rate(d)

            formatted_debts.append({
                "name": d.get("name"),
                "amount": d.get("amount"),
                "monthlyPayment": d.get("monthlyPayment"),
                "interestRate": rate
            })

    summary = {
        "name": user.get("name", "there") if user else "there",
        "incomes": [{"name": i.get("name"), "amount": i.get("amount"), "frequency": i.get("frequency")} for i in incomes],
        "expenses": formatted_expenses,
        "budgets": [{"name": b.get("name"), "amount": b.get("amount"), "category": b.get("category")} for b in budgets],
        "debts": formatted_debts,
        "saving_goals": [{
            "name": sg.get("name"), 
            "totalAmount": sg.get("totalAmount"), 
            "monthlyTarget": sg.get("monthlyTarget"),
            "savedAmount": sg.get("savedMoney", 0)
        } for sg in saving_goals],
        "subscription_status": subscription.get("status", "none") if subscription else "none"
    }
    
    await redis_client.set(cache_key, json.dumps(summary, default=safe_serialize), ex=300)
    return summary

async def save_chat_message(user_id: str, conversation_id: str, role: str, message: str):
    try:
        await db.chat_history.insert_one({
            "userId": ObjectId(user_id),
            "conversation_id": conversation_id,
            "role": role,
            "message": message,
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception:
        pass 

async def get_conversation_history(conversation_id: str, limit: int = 20) -> list:
    cursor = db.chat_history.find({"conversation_id": conversation_id}).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(length=limit) 
    docs.reverse()
    history = []
    for document in docs:
        role = document["role"]
        if role == "bot": role = "assistant"
        history.append({"role": role, "content": document["message"]})
    return history

async def get_all_active_users_cursor():
    cursor = db.users.find({"isDeleted": False})
    async for user in cursor:
        yield user

async def save_optimization_report(user_id: str, report_type: str, report_data: dict):
    await db.optimization_reports.update_one(
        {"userId": ObjectId(user_id), "reportType": report_type},
        {"$set": {"reportData": report_data, "createdAt": datetime.now(timezone.utc)}},
        upsert=True
    )

async def get_latest_optimization_report(user_id: str, report_type: str) -> dict | None:
    report = await db.optimization_reports.find_one(
        {"userId": ObjectId(user_id), "reportType": report_type}, 
        sort=[("createdAt", -1)]
    )
    return report.get("reportData") if report else None

async def save_admin_alert(user_id: str, user_email: str, alert_message: str, category: str):
    await db.admin_alerts.insert_one({
        "userId": ObjectId(user_id), "userEmail": user_email,
        "alertMessage": alert_message, "category": category, "createdAt": datetime.now(timezone.utc)
    })

async def get_latest_admin_alerts_for_user(user_id: str, limit: int = 5) -> list:
    try:
        cursor = db.admin_alerts.find({"userId": ObjectId(user_id)}).sort("createdAt", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)
        return json.loads(json.dumps(alerts, default=safe_serialize))
    except Exception:
        return []

async def save_calculator_tips(user_id: str, tips_data: dict):
    await db.calculator_tips.update_one(
        {"userId": ObjectId(user_id)},
        {"$set": {"tipsData": tips_data, "createdAt": datetime.now(timezone.utc)}},
        upsert=True
    )

async def get_latest_calculator_tips(user_id: str) -> dict | None:
    tips = await db.calculator_tips.find_one({"userId": ObjectId(user_id)})
    return tips.get("tipsData") if tips else None

async def get_latest_savings_input(user_id: str) -> dict | None:
    doc = await db.savingcalculations.find_one(
        {"userId": ObjectId(user_id)}, 
        sort=[("_id", -1)]
    )
    return _clean_mongo_doc(doc)

async def get_latest_loan_input(user_id: str) -> dict | None:
    doc = await db.loanrepaymentcalculations.find_one(
        {"userId": ObjectId(user_id)}, 
        sort=[("_id", -1)]
    )
    return _clean_mongo_doc(doc)

async def get_latest_future_value_input(user_id: str) -> dict | None:
    doc = await db.inflationcalculations.find_one(
        {"userId": ObjectId(user_id)}, 
        sort=[("_id", -1)]
    )
    return _clean_mongo_doc(doc, mapping={"years": "yearsToProject"})

async def get_latest_historical_input(user_id: str) -> dict | None:
    doc = await db.inflationapicalculations.find_one(
        {"userId": ObjectId(user_id)}, 
        sort=[("_id", -1)]
    )
    return _clean_mongo_doc(doc)