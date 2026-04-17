import asyncio
from datetime import datetime, date, timezone
import json
from bson import ObjectId
from .client import db, redis_client
from loguru import logger

def _serialize_mongo_doc(obj):
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_serialize_mongo_doc(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize_mongo_doc(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj

def calculate_implied_interest_rate(debt_doc):
    amount = float(debt_doc.get("amount") or 0)
    int_rep = float(debt_doc.get("interestRepayment") or 0)

    if amount > 0 and int_rep > 0:
        return round(((int_rep * 12) / amount) * 100, 2)
    return 0.0

def _safe_result(result, single: bool = False):
    if isinstance(result, Exception):
        return None if single else []
    return result

async def get_user_financial_summary(user_id: str, skip_cache: bool = False, time_frame: str = 'all_time') -> dict:
    cache_key = f"user_summary:{user_id}:{time_frame}"

    if not skip_cache:
        cached_summary = await redis_client.get(cache_key)
        if cached_summary:
            return json.loads(cached_summary)

    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise ValueError(f"Invalid user_id format provided: {user_id}")

    # Get user first to check for partner link
    user = await db.users.find_one({"_id": object_id})
    partner_id = user.get("partnerId") if user else None
    
    general_query = {"userId": object_id, "isDeleted": False}
    income_query = dict(general_query)
    expense_query = dict(general_query)
    budget_query = dict(general_query)
    
    now = datetime.now(timezone.utc)
    
    if time_frame == 'current_month':
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        end_of_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc) if now.month < 12 else datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)

        # 1. Income: Filter by receiveDate (Target: £55,000)
        income_query["frequency"] = "monthly"
        income_query["receiveDate"] = {"$gte": start_of_month, "$lt": end_of_month}

        # 2. Expense: Restore budgetId requirement (Target: £16,100)
        expense_query["frequency"] = "monthly"
        expense_query["endDate"] = {"$gte": start_of_month, "$lt": end_of_month}
        expense_query["budgetId"] = {"$exists": True, "$ne": None}
        
        # 3. Budget: Filter by createdAt (Target: £26,100)
        budget_query["createdAt"] = {"$gte": start_of_month, "$lt": end_of_month}

    # 4. Partner Data Inclusion (Node.js rule: include partner's household budgets)
    budget_tasks = [db.budgets.find(budget_query).to_list(length=None)]
    if partner_id:
        partner_budget_query = {
            "userId": ObjectId(partner_id),
            "isDeleted": False,
            "type": "household",
            "createdAt": budget_query.get("createdAt", {"$exists": True})
        }
        budget_tasks.append(db.budgets.find(partner_budget_query).to_list(length=None))

    # 5. Saving Goal Filtering (Node.js rule: isCompleted: false and completeDate > now)
    saving_goal_query = dict(general_query)
    saving_goal_query["isCompleted"] = False
    saving_goal_query["completeDate"] = {"$gt": now}

    income_task = db.incomes.find(income_query).to_list(length=None)
    expense_task = db.expenses.find(expense_query).to_list(length=None)
    debt_task = db.debts.find(general_query).to_list(length=None)
    saving_goal_task = db.savinggoals.find(saving_goal_query).to_list(length=None)
    subscription_task = db.subscriptions.find_one({"userId": object_id, "status": "active"})

    results = await asyncio.gather(
        income_task, expense_task, asyncio.gather(*budget_tasks),
        debt_task, saving_goal_task, subscription_task,
        return_exceptions=True
    )

    incomes      = _safe_result(results[0])
    expenses     = _safe_result(results[1])
    budget_results = _safe_result(results[2]) # List of lists
    budgets      = [item for sublist in budget_results for item in sublist] if isinstance(budget_results, list) else []
    debts        = _safe_result(results[3])
    saving_goals = _safe_result(results[4])
    subscription = _safe_result(results[5], single=True)

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

    processed_debts = []
    if debts:
        for d in debts:
            cap = float(d.get("capitalRepayment") or 0)
            int_rep = float(d.get("interestRepayment") or 0)
            total_rep = cap + int_rep
            
            if total_rep > 0:
                rate = (int_rep / total_rep * 100)
            else:
                rate = float(d.get("interestRate") or d.get("userInterestRate") or 0)
            
            processed_debts.append({
                "name": d.get("name"),
                "amount": float(d.get("amount", 0)),
                "monthlyPayment": float(d.get("monthlyPayment", 0)),
                "interestRate": round(rate, 2),
                "completionRatio": float(d.get("completionRatio", 0))
            })

        processed_debts.sort(key=lambda x: x["interestRate"], reverse=True)
        processed_debts = processed_debts[:3]

    summary = {
        "name": user.get("name", "there") if user else "there",
        "incomes": [{"name": i.get("name"), "amount": i.get("amount"), "frequency": i.get("frequency")} for i in incomes],
        "expenses": formatted_expenses,
        "budgets": [{"name": b.get("name"), "amount": b.get("amount"), "category": b.get("category")} for b in budgets],
        "debts": processed_debts,
        "saving_goals": [{
            "name": sg.get("name"),
            "totalAmount": sg.get("totalAmount"),
            "monthlyTarget": sg.get("monthlyTarget"),
            "savedAmount": sg.get("savedMoney", 0),
            "completionRatio": sg.get("completionRation", 0)
        } for sg in saving_goals],
        "subscription_status": subscription.get("status", "none") if subscription else "none"
    }

    serialized_summary = _serialize_mongo_doc(summary)
    await redis_client.set(cache_key, json.dumps(serialized_summary), ex=300)

    return serialized_summary


async def save_chat_message(user_id: str, conversation_id: str, role: str, message: str):
    try:
        await db.chat_history.insert_one({
            "userId": ObjectId(user_id),
            "conversation_id": conversation_id,
            "role": role,
            "message": message,
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception as e:
        logger.error(f"Failed to save chat message for user {user_id}: {e}")


async def get_conversation_history(conversation_id: str, limit: int = 20) -> list:
    cursor = db.chat_history.find({"conversation_id": conversation_id}).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(length=limit)
    docs.reverse()
    history = []
    for document in docs:
        role = document["role"]
        if role == "bot":
            role = "assistant"
        elif role not in ("user", "assistant", "system"):
            logger.warning(f"Unknown role '{role}' in conversation history, skipping message.")
            continue
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
        "alertMessage": alert_message, "category": category,
        "createdAt": datetime.now(timezone.utc)
    })


async def get_latest_admin_alerts_for_user(user_id: str, limit: int = 5) -> list:
    try:
        cursor = db.admin_alerts.find({"userId": ObjectId(user_id)}).sort("createdAt", -1).limit(limit)
        alerts = await cursor.to_list(length=limit)
        return _serialize_mongo_doc(alerts)
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
    return _serialize_mongo_doc(doc)


async def get_latest_loan_input(user_id: str) -> dict | None:
    doc = await db.loanrepaymentcalculations.find_one(
        {"userId": ObjectId(user_id)},
        sort=[("_id", -1)]
    )
    return _serialize_mongo_doc(doc)


async def get_latest_future_value_input(user_id: str) -> dict | None:
    doc = await db.inflationcalculations.find_one(
        {"userId": ObjectId(user_id)},
        sort=[("_id", -1)]
    )
    clean = _serialize_mongo_doc(doc)
    if clean and "years" in clean:
        clean["yearsToProject"] = clean["years"]
    return clean


async def get_latest_historical_input(user_id: str) -> dict | None:
    doc = await db.inflationapicalculations.find_one(
        {"userId": ObjectId(user_id)},
        sort=[("_id", -1)]
    )
    return _serialize_mongo_doc(doc)