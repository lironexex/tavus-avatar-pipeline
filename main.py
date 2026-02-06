import os
import requests
import fal_client
import ffmpeg
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
    Uses FFmpeg to ensure the output is 1080p, 25fps, H.264/AAC.
    """
    print(f"Looping video to reach {target_duration} seconds...")
    try:
        # stream_loop=24 means it plays the 5s clip 25 times total (125 seconds)
        # then we trim it exactly to 120s with .output(t=120)
        (
            ffmpeg
            .input(input_path, stream_loop=24)
            .output(
                output_path,
                t=target_duration,
                vcodec='libx264',
                acodec='aac',
                pix_fmt='yuv420p',  # Ensure compatibility
                r=25  # Set frame rate to 25fps as per Tavus requirements
            )
            .run(overwrite_output=True)
        )
        print(f"Success! Final Tavus training video: {output_path}")
    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")


def generate_tavus_pipeline():
    # 1. Check for FAL_KEY
    if not os.getenv("FAL_KEY") or "your_actual_key" in os.getenv("FAL_KEY"):
        print("Error: Please set a valid FAL_KEY in your .env file.")
        return

    # 2. Upload local image to fal
    print(f"Step 1: Uploading {LOCAL_IMAGE_PATH}...")
    image_url = fal_client.upload_file(LOCAL_IMAGE_PATH)

    # 3. Generate 5 seconds of movement using Kling 1.5
    print("Step 2: Animating image (Kling 1.5)...")
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

    # 4. Download the 5s clip
    download_video(video_url, RAW_CLIP_PATH)

    # 5. Loop it to 120s for Tavus training
    loop_video_for_tavus(RAW_CLIP_PATH, FINAL_TRAINING_VIDEO)


if __name__ == "__main__":
    generate_tavus_pipeline()