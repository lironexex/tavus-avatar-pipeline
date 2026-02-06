# src/tavus_trigger.py

import os
import requests
import json
import dropbox
import time
from tqdm import tqdm
from dotenv import load_dotenv

# Path logic for .env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

LOCAL_VIDEO_PATH = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")
REPLICA_NAME = "Rizolv_AI_Avatar_POC_FINAL"


class ProgressFile:
    """A wrapper for a file object that updates a tqdm progress bar."""

    def __init__(self, file, pbar):
        self.file = file
        self.pbar = pbar

    def read(self, size=-1):
        chunk = self.file.read(size)
        if chunk:
            self.pbar.update(len(chunk))
        return chunk

    def __len__(self):
        return os.fstat(self.file.fileno()).st_size


def upload_and_get_link(file_path):
    """Uploads to Dropbox and returns a direct temporary download link."""
    access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
    if not access_token:
        print("Error: DROPBOX_ACCESS_TOKEN not found in .env")
        return None

    dbx = dropbox.Dropbox(access_token)
    file_name = f"/{os.path.basename(file_path)}"
    file_size = os.path.getsize(file_path)

    try:
        print(f"Uploading {os.path.basename(file_path)}...")
        with tqdm(total=file_size, unit='B', unit_scale=True, desc="Dropbox Upload") as pbar:
            with open(file_path, "rb") as f:
                wrapped_file = ProgressFile(f, pbar)
                dbx.files_upload(wrapped_file.read(), file_name, mode=dropbox.files.WriteMode("overwrite"))

        print("\nGenerating direct link for Tavus...")
        link_metadata = dbx.files_get_temporary_link(file_name)
        download_url = link_metadata.link
        print(f"✅ Download Link: {download_url}")
        return download_url

    except Exception as e:
        print(f"\nDropbox Error: {e}")
        return None


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
        # Step 1: Upload and get link
        url = upload_and_get_link(LOCAL_VIDEO_PATH)
        if url:
            # Step 2: Trigger Tavus
            new_id = trigger_tavus(url)
            # Step 3: Immediate follow-up status check
            if new_id:
                check_status_automated(new_id)
    else:
        print(f"Error: Video file missing at {LOCAL_VIDEO_PATH}")