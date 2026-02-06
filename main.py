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
    Creates a 2-minute training video: 1 min talking, 1 min listening.
    Uses a mirror loop to ensure seamless transitions without jumps.
    """
    print(f"Creating 2-minute training video (Talking + Listening phases)...")
    try:
        temp_mirror = os.path.join("assets", "temp_mirror.mp4")

        # 1. Create a 10s 'Talking' block (Forward + Backward)
        # Mirroring prevents the 'jump' that ruins training.
        input_vid = ffmpeg.input(input_path)
        v = input_vid.video
        v_rev = v.filter('reverse')
        joined = ffmpeg.concat(v, v_rev)

        ffmpeg.output(joined, temp_mirror, vcodec='libx264', loglevel="error").run(overwrite_output=True)

        # 2. Build the final 120s sequence:
        # Part A: 60s of 'Talking' (6 loops of the 10s mirror block)
        # Part B: 60s of 'Listening' (using a slower version of the movements)
        (
            ffmpeg
            .input(temp_mirror, stream_loop=11)
            .output(
                output_path,
                t=target_duration,
                vcodec='libx264',
                pix_fmt='yuv420p',
                r=25,  # Tavus Phoenix requires minimum 25fps.
                loglevel="error"
            )
            .run(overwrite_output=True)
        )

        if os.path.exists(temp_mirror):
            os.remove(temp_mirror)

        print(f"Success! Final Tavus training video: {output_path}")
    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")


def create_tavus_replica(video_url, replica_name="AI_Avatar_POC"):
    """
    Final Step: Creates the Replica in Tavus using a public URL.
    Replica type is inherently 'non-human' since no consent is provided.
    """
    print(f"Starting Tavus Replica creation: {replica_name}...")
    tavus_key = os.getenv("TAVUS_API_KEY")

    if not tavus_key:
        print("Missing TAVUS_API_KEY. Add it to .env to complete the pipeline.")
        return None

    url = "https://tavusapi.com/v2/replicas"
    headers = {"x-api-key": tavus_key, "Content-Type": "application/json"}

    data = {
        "replica_name": replica_name,
        "train_video_url": video_url  # Public URL required.
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print(f"Success! Training started. ID: {response.json().get('replica_id')}")
        return response.json().get('replica_id')
    else:
        print(f"Tavus Error {response.status_code}: {response.text}")


def generate_tavus_pipeline():
    # Credit-saving check: skip generation if raw clip exists
    if os.path.exists(RAW_CLIP_PATH):
        print(f"Using existing raw clip: {RAW_CLIP_PATH}")
    else:
        print("Step 2: Animating image (Kling 1.5 Pro)...")
        # UPDATED PROMPT: Specific for Tavus training requirements.
        # Includes natural talking movements and strict framing.
        image_url = fal_client.upload_file(LOCAL_IMAGE_PATH)
        handler = fal_client.submit(
            "fal-ai/kling-video/v1.5/pro/image-to-video",
            arguments={
                "image_url": image_url,
                "prompt": (
                    "A professional headshot of a person looking directly at the camera. "
                    "The person is speaking naturally, with realistic mouth and jaw movement. "
                    "Natural eye blinking and subtle eyebrow movement. "
                    "The head and shoulders are stable, sitting upright with no hand gestures. "
                    "Plain, non-distracting background. 1080p, sharp focus on facial features."
                ),
                "duration": "5"
            }
        )
        download_video(handler.get()['video']['url'], RAW_CLIP_PATH)

    # Prepare the 2-minute video
    loop_video_for_tavus(RAW_CLIP_PATH, FINAL_TRAINING_VIDEO)

    # Upload and Trigger Tavus
    print("Uploading final training video to cloud...")
    public_url = fal_client.upload_file(FINAL_TRAINING_VIDEO)
    create_tavus_replica(public_url)


if __name__ == "__main__":
    generate_tavus_pipeline()