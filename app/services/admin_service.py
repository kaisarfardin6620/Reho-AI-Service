import asyncio
import json
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY

async def run_analysis_for_all_users():
    """
    The core logic for the admin alert system. This function iterates through
    all users, analyzes their data, and saves any generated alerts.
    This is intended to be run as a scheduled background job.
    """
    print("Starting analysis job for all users...")
    all_users = await db_queries.get_all_active_users()
    
    for user in all_users:
        user_id = str(user["_id"])
        user_email = user.get("email", "N/A")
        print(f"Analyzing data for user: {user_email} ({user_id})")

        try:
            financial_summary = await db_queries.get_user_financial_summary(user_id)
            
            if not financial_summary.get("incomes") and not financial_summary.get("expenses"):
                continue

            anomaly_prompt = prompt_builder.build_anomaly_detection_prompt(financial_summary)
            
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=anomaly_prompt,
                response_format={"type": "json_object"}
            )
            
            alert_data = json.loads(response.choices[0].message.content)

            if alert_data and "alertMessage" in alert_data:
                await db_queries.save_admin_alert(
                    user_id=user_id,
                    user_email=user_email,
                    alert_message=alert_data["alertMessage"],
                    category=alert_data["category"]
                )
                print(f"!!! Alert generated for user {user_email}: {alert_data['alertMessage']}")
            
            await asyncio.sleep(1)

        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            continue 
    
    print("Finished analysis job for all users.")