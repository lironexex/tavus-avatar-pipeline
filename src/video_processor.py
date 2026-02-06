# src/video_processor.py

import os
import requests
import fal_client
import ffmpeg
from dotenv import load_dotenv

# 1. Determine the Project Root (one level up from 'src')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Load API keys from .env file located in the root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# 2. Update Configuration Constants to use absolute paths
LOCAL_IMAGE_PATH = os.path.join(PROJECT_ROOT, "assets", "generated_person_example_1.png")
RAW_CLIP_PATH = os.path.join(PROJECT_ROOT, "assets", "raw_movement.mp4")
FINAL_TRAINING_VIDEO = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")


def download_video(url, target_path):
    """Downloads the generated video from a URL to a local path."""
    print(f"Downloading video from fal.ai...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        print(f"Failed to download video. Status: {response.status_code}")


def loop_video_for_tavus(input_path, output_path, target_duration=120):
    """Creates a 2-minute training video with a seamless mirror loop."""
    print(f"Processing {target_duration}s seamless training video...")

    # Ensure the assets directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        temp_mirror = os.path.join(PROJECT_ROOT, "assets", "temp_mirror.mp4")
        input_vid = ffmpeg.input(input_path)
        v = input_vid.video
        v_rev = v.filter('reverse')
        joined = ffmpeg.concat(v, v_rev)

        # Create 10s seamless mirror block
        ffmpeg.output(joined, temp_mirror, vcodec='libx264', loglevel="error").run(overwrite_output=True)

        # Loop to 120s total for Phoenix training requirements
        (
            ffmpeg
            .input(temp_mirror, stream_loop=11)
            .output(
                output_path,
                t=target_duration,
                vcodec='libx264',
                pix_fmt='yuv420p',
                r=25,
                loglevel="error"
            )
            .run(overwrite_output=True)
        )
        if os.path.exists(temp_mirror):
            os.remove(temp_mirror)
        print(f"Success! Final Tavus training video ready at: {output_path}")
    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")


def main():
    # Verify the source image exists before starting
    if not os.path.exists(LOCAL_IMAGE_PATH):
        print(f"Error: Could not find source image at {LOCAL_IMAGE_PATH}")
        return

    # Skip generation if raw clip already exists to save fal.ai credits
    if not os.path.exists(RAW_CLIP_PATH):
        print("Generating detailed movement via Kling 1.5 Pro...")

        # Upload portrait to fal.ai cloud storage
        image_url = fal_client.upload_file(LOCAL_IMAGE_PATH)

        # Detailed prompt optimized for Tavus Phoenix model
        handler = fal_client.submit(
            "fal-ai/kling-video/v1.5/pro/image-to-video",
            arguments={
                "image_url": image_url,
                "prompt": (
                    "A professional headshot of a person looking directly at the camera. "
                    "The person is speaking naturally, with realistic mouth and jaw movement. "
                    "Natural eye blinking and subtle eyebrow movement. "
                    "The head and shoulders are stable, sitting upright with no hand gestures. "
                    "Plain background, 1080p, sharp focus on facial features."
                ),
                "duration": "5"
            }
        )
        download_video(handler.get()['video']['url'], RAW_CLIP_PATH)
    else:
        print(f"Found existing raw clip at {RAW_CLIP_PATH}. Processing directly...")

    loop_video_for_tavus(RAW_CLIP_PATH, FINAL_TRAINING_VIDEO)


if __name__ == "__main__":
    main()