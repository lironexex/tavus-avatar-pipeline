# src/tavus_trigger.py

import os
import requests
import time
from dotenv import load_dotenv
from dropbox_utils import upload_and_get_link  # Import our new utility

# Path logic for .env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

LOCAL_VIDEO_PATH = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")
REPLICA_NAME = "Rizolv_AI_Avatar_POC_FINAL"


def trigger_tavus(video_url):
    """Triggers the Tavus API training and returns the new replica_id."""
    print(f"Triggering Tavus training...")
    tavus_key = os.getenv("TAVUS_API_KEY")
    endpoint = "https://tavusapi.com/v2/replicas"
    headers = {"x-api-key": tavus_key, "Content-Type": "application/json"}
    data = {"replica_name": REPLICA_NAME, "train_video_url": video_url}

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code in [200, 201]:
        replica_id = response.json().get('replica_id')
        print(f"🚀 Success! Training started. Replica ID: {replica_id}")
        return replica_id
    else:
        print(f"Tavus API Error {response.status_code}: {response.text}")
        return None


def check_status_automated(replica_id):
    """Automatically performs an initial status check after a delay."""
    print(f"\nWaiting 10 seconds for initial validation...")
    time.sleep(10)

    tavus_key = os.getenv("TAVUS_API_KEY")
    url = f"https://tavusapi.com/v2/replicas/{replica_id}"
    headers = {"x-api-key": tavus_key}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"--- Initial Status Check ---")
            print(f"Replica ID: {replica_id}")
            print(f"Current Status: {status}")
            if status == "error":
                print(f"❌ Error Detail: {data.get('error_message')}")
            else:
                print(f"Progress: Video accepted. Phase is '{status}'.")
            print(f"-----------------------------")
    except Exception as e:
        print(f"Status check connection failed: {e}")


if __name__ == "__main__":
    if os.path.exists(LOCAL_VIDEO_PATH):
        url = upload_and_get_link(LOCAL_VIDEO_PATH)
        if url:
            new_id = trigger_tavus(url)
            if new_id:
                check_status_automated(new_id)
    else:
        print(f"Error: Video file missing at {LOCAL_VIDEO_PATH}")