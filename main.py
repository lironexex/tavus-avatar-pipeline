import os
import requests
import fal_client
import ffmpeg
import json
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# Configuration Constants
LOCAL_IMAGE_PATH = os.path.join("assets", "generated_person_example_1.png")
RAW_CLIP_PATH = os.path.join("assets", "raw_movement.mp4")
FINAL_TRAINING_VIDEO = os.path.join("assets", "tavus_training_video.mp4")


def download_video(url, target_path):
    """Downloads the generated video from a URL to a local path."""
    print(f"Downloading video from fal.ai...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved raw clip to: {target_path}")
    else:
        print(f"Failed to download video. Status: {response.status_code}")


def loop_video_for_tavus(input_path, output_path, target_duration=120):
    """
    Loops a short video to reach the required duration for Tavus training (120s).
    Ensures compatibility with Tavus Phoenix model requirements (1080p, 25fps).
    """
    print(f"Looping video to reach {target_duration} seconds...")
    try:
        # stream_loop=24 plays the 5s clip 25 times total.
        # Output is trimmed to exactly 120s using 't=target_duration'
        (
            ffmpeg
            .input(input_path, stream_loop=24)
            .output(
                output_path,
                t=target_duration,
                vcodec='libx264',  # Required H.264 codec
                acodec='aac',  # Required AAC audio codec
                pix_fmt='yuv420p',
                r=25,  # Required minimum 25 fps
                loglevel="error"  # This will hide all the "Late SEI" spam
            )
            .run(overwrite_output=True)
        )
        print(f"Success! Final Tavus training video created at: {output_path}")
    except ffmpeg.Error as e:
        # If this fails, ensure FFmpeg is in your System Path and PyCharm was restarted
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")


def create_tavus_replica(video_url, replica_name="AI_POC_Avatar"):
    """
    Final Step: Creates the Replica in Tavus using the provided video URL.
    Requires a publicly accessible URL for the training video.
    """
    print(f"Starting Tavus Replica creation for: {replica_name}...")
    tavus_key = os.getenv("TAVUS_API_KEY")

    if not tavus_key:
        print("Missing TAVUS_API_KEY. Ask Robi for the key to finish this step.")
        return None

    url = "https://tavusapi.com/v2/replicas"
    headers = {
        "x-api-key": tavus_key,
        "Content-Type": "application/json"
    }

    # Since this is an AI face, we skip consent by not using a 'personal' replica type
    data = {
        "replica_name": replica_name,
        "train_video_url": video_url
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        replica_id = response.json().get("replica_id")
        print(f"Success! Replica is now training. ID: {replica_id}")
        return replica_id
    else:
        print(f"Tavus Error {response.status_code}: {response.text}")
        return None


def generate_tavus_pipeline():
    # 1. Check for existing local raw clip to save fal.ai credits
    if os.path.exists(RAW_CLIP_PATH):
        print(f"Found existing raw clip at {RAW_CLIP_PATH}. Skipping fal.ai generation.")
    else:
        if not os.getenv("FAL_KEY") or "your_actual_key" in os.getenv("FAL_KEY"):
            print("Error: Please set a valid FAL_KEY in your .env file.")
            return

        print(f"Raw clip not found. Starting fal.ai generation process...")

        # 2. Upload local person image to fal.ai
        print(f"Step 1: Uploading {LOCAL_IMAGE_PATH}...")
        image_url = fal_client.upload_file(LOCAL_IMAGE_PATH)

        # 3. Generate 5 seconds of subtle movement based on Tavus guidelines
        print("Step 2: Animating image (Kling 1.5 Pro)...")
        handler = fal_client.submit(
            "fal-ai/kling-video/v1.5/pro/image-to-video",
            arguments={
                "image_url": image_url,
                "prompt": (
                    "A professional headshot, person looking directly into the camera at eye level. "
                    "Neutral, relaxed facial expression, natural eye blinking, lips closing fully. "
                    "Minimal head movement, sitting upright and stable. 1080p, sharp focus."
                ),
                "duration": "5"
            }
        )
        result = handler.get()
        video_url = result['video']['url']

        # 4. Download the generated 5s clip
        download_video(video_url, RAW_CLIP_PATH)

    # 5. Loop the 5s clip into a 2-minute video for Tavus training
    loop_video_for_tavus(RAW_CLIP_PATH, FINAL_TRAINING_VIDEO)

    # NEXT STEP: Upload FINAL_TRAINING_VIDEO to a public URL and call create_tavus_replica()


if __name__ == "__main__":
    generate_tavus_pipeline()