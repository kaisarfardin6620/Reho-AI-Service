import asyncio
import datetime
from bson import ObjectId
from .client import db

async def get_user_financial_summary(user_id: str) -> dict:
    """
    Fetches a comprehensive financial summary for a given user by concurrently
    querying all relevant collections in the database.
    """
    try:
        object_id = ObjectId(user_id)
    except Exception:
        print(f"Invalid user_id format provided: {user_id}")
        return {"name": "there", "error": "Invalid user ID"}

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
    
    return summary

async def set_conversation_title(user_id: str, conversation_id: str, title: str):
    """Saves or updates the title for a conversation in a new 'conversations' collection."""
    try:
        await db.conversations.update_one(
            {"conversation_id": conversation_id, "userId": ObjectId(user_id)},
            {"$set": {"title": title}, "$setOnInsert": {"createdAt": datetime.datetime.utcnow()}},
            upsert=True
        )
        print(f"Title set for conversation {conversation_id}: {title}")
    except Exception as e:
        print(f"DB Error setting conversation title: {e}")

async def save_chat_message(user_id: str, conversation_id: str, role: str, message: str):
    """Saves a single chat message to the history, including a timestamp."""
    try:
        await db.chat_history.insert_one({
            "userId": ObjectId(user_id),
            "conversation_id": conversation_id,
            "role": role,
            "message": message,
            "timestamp": datetime.datetime.utcnow()
        })
    except Exception as e:
        print(f"DB Error saving chat message: {e}")

async def get_conversation_history(conversation_id: str, max_messages: int = 20) -> list:
    """Fetches the last N messages for a given conversation and translates 'bot' role."""
    history = []
    cursor = db.chat_history.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).limit(max_messages)
    docs = await cursor.to_list(length=max_messages)
    for document in docs:
        role = document["role"]
        if role == "bot":
            role = "assistant"
        history.append({"role": role, "content": document["message"]})
    return history

async def get_user_conversations(user_id: str) -> list:
    """Fetches all conversation records for a specific user from the 'conversations' collection."""
    try:
        object_id = ObjectId(user_id)
        cursor = db.conversations.find({"userId": object_id}).sort("createdAt", -1)
        conversations = await cursor.to_list(length=None)
        return conversations
    except Exception as e:
        print(f"DB Error fetching user conversations: {e}")
        return []

async def rename_conversation(user_id: str, conversation_id: str, new_title: str) -> bool:
    """Updates the title of a specific conversation for a specific user."""
    try:
        result = await db.conversations.update_one(
            {"conversation_id": conversation_id, "userId": ObjectId(user_id)},
            {"$set": {"title": new_title}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"DB Error renaming conversation: {e}")
        return False

async def delete_conversation(user_id: str, conversation_id: str) -> bool:
    """Deletes a conversation record and all of its associated chat history messages."""
    try:
        delete_convo_task = db.conversations.delete_one(
            {"conversation_id": conversation_id, "userId": ObjectId(user_id)}
        )
        delete_history_task = db.chat_history.delete_many(
            {"conversation_id": conversation_id, "userId": ObjectId(user_id)}
        )
        results = await asyncio.gather(delete_convo_task, delete_history_task)
        return results[0].deleted_count > 0
    except Exception as e:
        print(f"DB Error deleting conversation: {e}")
        return False
    
async def save_suggestions(user_id: str, suggestions: list[dict]):
    """
    Saves a list of generated AI suggestions to the database.
    This will overwrite any previous suggestions for the user.  
    """
    try:
        object_id = ObjectId(user_id)
        await db.suggestions.delete_many({"userId": object_id})

        if suggestions:
            docs_to_insert = [
                {
                    **s,
                    "userId": object_id,
                    "createdAt": datetime.datetime.utcnow()
                } for s in suggestions
            ]
            await db.suggestions.insert_many(docs_to_insert)
            print(f"Successfully saved {len(docs_to_insert)} suggestions for user {user_id}")

    except Exception as e:
        print(f"DB Error saving suggestions: {e}")

async def get_latest_suggestions(user_id: str) -> list:
    """
    Fetches the most recent set of AI suggestions for a given user.
    """
    try:
        object_id = ObjectId(user_id)
        cursor = db.suggestions.find({"userId": object_id}).sort("createdAt", -1)
        return await cursor.to_list(length=None)
    except Exception as e:
        print(f"DB Error fetching suggestions: {e}")
        return []


async def get_all_active_users() -> list:
    """Fetches a list of all non-deleted users for analysis."""
    try:
        cursor = db.users.find({"isDeleted": False})
        return await cursor.to_list(length=None)
    except Exception as e:
        print(f"DB Error fetching all users: {e}")
        return []

async def save_admin_alert(user_id: str, user_email: str, alert_message: str, category: str):
    """Saves a single admin alert to the database."""
    try:
        await db.admin_alerts.insert_one({
            "userId": ObjectId(user_id),
            "userEmail": user_email,
            "alertMessage": alert_message,
            "category": category,
            "createdAt": datetime.datetime.utcnow()
        })
    except Exception as e:
        print(f"DB Error saving admin alert: {e}")

async def get_all_admin_alerts() -> list:
    """Fetches all generated admin alerts, sorted by most recent."""
    try:
        cursor = db.admin_alerts.find({}).sort("createdAt", -1)
        return await cursor.to_list(length=None)
    except Exception as e:
        print(f"DB Error fetching admin alerts: {e}")
        return []    