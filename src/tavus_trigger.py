# src/tavus_trigger.py

import os
import requests
import json
from dotenv import load_dotenv

# 1. Determine the Project Root (one level up from 'src')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Load API keys from the .env file located in the root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Configuration
# Ensure this link is a direct download. Google Drive can sometimes block APIs.
VIDEO_URL = "https://drive.google.com/uc?export=download&id=1aRL2KEI92BazNSUlN3PLVJr88Eyh77TD"
REPLICA_NAME = "Rizolv_AI_Avatar_POC_v3"


def trigger_tavus(video_url):
    """
    Triggers the Tavus API to start training the Replica.
    Phoenix-3 is the default model used.
    """
    print(f"Triggering Tavus Replica creation for: {REPLICA_NAME}...")
    tavus_key = os.getenv("TAVUS_API_KEY")

    if not tavus_key:
        print("Error: TAVUS_API_KEY not found in .env. Please check your project root.")
        return

    endpoint = "https://tavusapi.com/v2/replicas"
    headers = {
        "x-api-key": tavus_key,
        "Content-Type": "application/json"
    }

    # Request body for a Non-human/AI Replica (no consent_video_url needed)
    data = {
        "replica_name": REPLICA_NAME,
        "train_video_url": video_url
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data)

        # 201 is the official 'Created' status, 200 may return existing status
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"🚀 Success! Status: {result.get('status')}")
            print(f"Replica ID: {result.get('replica_id')}")
            print("Training typically takes 4-6 hours. Monitor progress in the dashboard.")  #
        else:
            print(f"Error {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")


if __name__ == "__main__":
    trigger_tavus(VIDEO_URL)