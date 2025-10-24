import asyncio
from app.db import queries as db_queries
from app.services import suggestion_service, admin_service

async def generate_suggestions_for_all_users():
    print("SCHEDULER: Starting nightly job to generate AI suggestions for all users...")
    
    try:
        all_users = await db_queries.get_all_active_users()
        if not all_users:
            print("SCHEDULER: No active users found. Skipping suggestion generation.")
            return

        print(f"SCHEDULER: Found {len(all_users)} users to process.")
        
        for user in all_users:
            user_id = str(user["_id"])
            user_email = user.get("email", "N/A")
            
            try:
                print(f"SCHEDULER: Generating suggestions for user: {user_email} ({user_id})")
                await suggestion_service.generate_and_save_suggestions(user_id)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"SCHEDULER: ERROR - Failed to generate suggestions for user {user_id}. Reason: {e}")
                continue
                
    except Exception as e:
        print(f"SCHEDULER: FATAL ERROR - The suggestion generation job failed entirely. Reason: {e}")
    
    print("SCHEDULER: Finished nightly suggestion generation job.")


async def run_admin_alert_analysis():
    print("SCHEDULER: Starting nightly job to run admin alert analysis...")
    try:
        await admin_service.run_analysis_for_all_users()
    except Exception as e:
        print(f"SCHEDULER: FATAL ERROR - The admin alert analysis job failed. Reason: {e}")
    
    print("SCHEDULER: Finished nightly admin alert analysis job.")