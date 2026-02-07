# src/face_swapper.py

import os
import fal_client
import requests
from dotenv import load_dotenv

# Path logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def swap_face_video(base_video_path, face_image_path, output_path):
    """
    Swaps the face from the PNG onto the MP4.
    Preserves the 'driving' movements for Tavus.
    """
    print(f"🔄 Swapping face from {os.path.basename(face_image_path)} onto {os.path.basename(base_video_path)}...")

    try:
        # Upload assets to Fal storage
        video_url = fal_client.upload_file(base_video_path)
        image_url = fal_client.upload_file(face_image_path)

        handler = fal_client.submit(
            "fal-ai/face-swap/video",
            arguments={
                "base_video_url": video_url,
                "swap_image_url": image_url
            }
        )

        result = handler.get()
        video_url = result['video']['url']

        # Download results
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"✅ Success: Swapped video saved to {output_path}")
            return True
    except Exception as e:
        print(f"❌ Face Swap Failed: {e}")
        return False