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

# 3. Enter the Replica ID you want to investigate
REPLICA_ID = "r3b5b046e926"


def check_replica_error():
    tavus_key = os.getenv("TAVUS_API_KEY")
    if not tavus_key:
        print("Error: TAVUS_API_KEY not found in .env.")
        return

    url = f"https://tavusapi.com/v2/replicas/{REPLICA_ID}"
    headers = {"x-api-key": tavus_key}

    print(f"Fetching details for Replica ID: {REPLICA_ID}...")

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            error_msg = data.get("error_message")

            print("-" * 30)
            print(f"Status: {status}")

            if status == "error":
                print(f"Detailed Error: {error_msg}")
                # Common errors include 'face_not_detected' or 'download_failed'
            elif status == "training":
                print("Replica is still training. Check back later.")
            else:
                print(f"Current Status: {status}")
            print("-" * 30)
        else:
            print(f"API Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Connection failed: {e}")


if __name__ == "__main__":
    check_replica_error()