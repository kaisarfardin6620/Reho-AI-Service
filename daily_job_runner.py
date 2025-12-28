import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") 

SECRET_TOKEN = os.getenv("SCHEDULER_API_KEY")

def run_daily_jobs():
    
    url = f"{API_BASE_URL}/schedule/run-daily-ai-jobs"
    
    headers = {
        "X-API-KEY": SECRET_TOKEN, 
        "Content-Type": "application/json"
    }
    
    print(f"[{requests.utils.default_headers().get('User-Agent')}] Attempting to trigger daily jobs at {url}")
    
    try:
        response = requests.post(url, headers=headers, json={}, timeout=10) 
        
        response.raise_for_status() 
        
        print(f"SUCCESS: Daily job triggered successfully.")
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
    except requests.exceptions.HTTPError as e:
        print(f"FAILURE: HTTP Error occurred. Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"FAILURE: Network/Request Error occurred. Reason: {e}")

if __name__ == "__main__":
    run_daily_jobs()