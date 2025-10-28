import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8080") 

SECRET_TOKEN = os.getenv(
    "SCHEDULER_API_KEY", 
    "f1c5d9a0e6b3g4h2i8j7k0l9m4n2o1p5q8r3s6t9u0v1w2x3y4z7"
) 

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