# src/fal_generator.py

import os
import requests
import fal_client
from dotenv import load_dotenv

# Standard path logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def download_video(url, target_path):
    """Downloads the generated video from fal.ai cloud storage."""
    print(f"Downloading video from fal.ai...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully saved video to {target_path}")
    else:
        print(f"Failed to download video. Status: {response.status_code}")


def generate_avatar_movement(image_path, output_path):
    """Generates the initial 5-second movement clip via Kling 1.5 Pro."""
    print("Generating detailed movement via Kling 1.5 Pro...")

    # Upload local portrait to fal.ai storage
    image_url = fal_client.upload_file(image_path)

    # Prompt optimized for high-fidelity facial features
    handler = fal_client.submit(
        "fal-ai/kling-video/v1.5/pro/image-to-video",
        arguments={
            "image_url": image_url,
            "prompt": (
                "A professional headshot. Speaking naturally, realistic mouth and jaw movement. "
                "Natural eye blinking. Stable head and shoulders, sharp focus on facial features."
            ),
            "duration": "5"
        }
    )

    video_data = handler.get()
    download_video(video_data['video']['url'], output_path)