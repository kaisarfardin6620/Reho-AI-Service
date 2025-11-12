import asyncio
import datetime
from bson import ObjectId
from .client import db, redis_client
from app.utils.mongo_metrics import track_mongo_operation
from loguru import logger
import json

async def get_user_financial_summary(user_id: str) -> dict:
    cache_key = f"user_summary:{user_id}"
    
    cached_summary = await redis_client.get(cache_key)
    if cached_summary:
        logger.info(f"Redis Cache HIT for {user_id}")
        return json.loads(cached_summary)
    
    logger.info(f"Redis Cache MISS for {user_id}. Fetching from MongoDB.")
    
    try:
        object_id = ObjectId(user_id)
    except Exception:
        logger.error(f"Invalid user_id format provided: {user_id}") 
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
    summary = {
        "name": user.get("name", "there") if user else "there",
        "incomes": [{"name": i.get("name"), "amount": i.get("amount"), "frequency": i.get("frequency")} for i in incomes],
        "expenses": [{"name": e.get("name"), "amount": e.get("amount"), "frequency": e.get("frequency")} for e in expenses],
        "budgets": [{"name": b.get("name"), "amount": b.get("amount"), "category": b.get("category")} for b in budgets],
        "debts": [{"name": d.get("name"), "amount": d.get("amount"), "monthlyPayment": d.get("monthlyPayment")} for d in debts],
        "saving_goals": [{"name": sg.get("name"), "totalAmount": sg.get("totalAmount"), "monthlyTarget": sg.get("monthlyTarget")} for sg in saving_goals],
        "subscription_status": subscription.get("status", "none") if subscription else "none"
    }
    
    await redis_client.set(cache_key, json.dumps(summary), ex=300)
    
    return summary
@track_mongo_operation(collection='chat_history', operation='insert')
async def save_chat_message(user_id: str, conversation_id: str, role: str, message: str):
    try:
        await db.chat_history.insert_one({
            "userId": ObjectId(user_id),
            "conversation_id": conversation_id,
            "role": role,
            "message": message,
            "timestamp": datetime.datetime.utcnow()
        })
    except Exception as e:
        logger.exception(f"DB Error saving chat message: {e}")
async def get_conversation_history(conversation_id: str, max_messages: int = 20) -> list:
    history = []
    cursor = db.chat_history.find({"conversation_id": conversation_id}).sort("timestamp", 1).limit(max_messages)
    docs = await cursor.to_list(length=max_messages)
    for document in docs:
        role = document["role"]
        if role == "bot":
            role = "assistant"
        history.append({"role": role, "content": document["message"]})
    return history