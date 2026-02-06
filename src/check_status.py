# src/check_status.py

import os
import requests
import json
from dotenv import load_dotenv

# 1. Determine the Project Root (one level up from 'src')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# 2. Load the .env file from the root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# 3. Use the NEW Replica ID you just generated
REPLICA_ID = "re352c876206"


def check_replica_status():
    tavus_key = os.getenv("TAVUS_API_KEY")
    if not tavus_key:
        print("Error: TAVUS_API_KEY not found in .env.")
        return

    url = f"https://tavusapi.com/v2/replicas/{REPLICA_ID}"
    headers = {"x-api-key": tavus_key}

    print(f"Checking status for Replica ID: {REPLICA_ID}...")

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")

            print("-" * 30)
            print(f"Current Status: {status}")

            if status == "error":
                print(f"❌ Error Message: {data.get('error_message')}")
            elif status == "training":
                print("⏳ Everything looks good! The video was accepted and training is in progress.")
                print("This phase usually takes 4-6 hours.")
            elif status == "ready":
                print("✅ Success! Your avatar is ready to use.")
            else:
                print(f"Status detail: {data}")
            print("-" * 30)
        else:
            print(f"API Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    check_replica_status()