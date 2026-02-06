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
    Creates a seamless mirror loop to reach 120s for Tavus training.
    Fixed the stream_loop placement to avoid the 'Invalid argument' error.
    """
    print(f"Creating seamless mirror loop for {target_duration} seconds...")
    try:
        # 1. First, we create the 10-second 'ping-pong' (forward + backward) clip
        # We save this to a temporary file to keep the looping command simple
        temp_mirror = os.path.join("assets", "temp_mirror.mp4")

        input_vid = ffmpeg.input(input_path)
        v = input_vid.video
        v_reversed = v.filter('reverse')
        joined = ffmpeg.concat(v, v_reversed)

        # Save the 10s seamless block
        ffmpeg.output(joined, temp_mirror, vcodec='libx264', loglevel="error").run(overwrite_output=True)

        # 2. Now we loop that 10s block 12 times (10s * 12 = 120s)
        # We put stream_loop=11 BEFORE the input to satisfy FFmpeg
        (
            ffmpeg
            .input(temp_mirror, stream_loop=11)
            .output(
                output_path,
                t=target_duration,
                vcodec='copy',  # 'copy' is fast because it's already encoded
                pix_fmt='yuv420p',
                r=25,
                loglevel="error"
            )
            .run(overwrite_output=True)
        )

        # Cleanup temp file
        if os.path.exists(temp_mirror):
            os.remove(temp_mirror)

        print(f"Success! Seamless training video created at: {output_path}")
    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")

def create_tavus_replica(video_url, replica_name="AI_POC_Avatar"):
    """
    Final Step: Creates the Replica in Tavus using a public video URL.
    Tavus Phoenix requires a 2-minute high-quality video.
    """
    print(f"Starting Tavus Replica creation for: {replica_name}...")
    tavus_key = os.getenv("TAVUS_API_KEY")

    if not tavus_key:
        print("Missing TAVUS_API_KEY. Add it to .env to complete the pipeline.")
        return None

    url = "https://tavusapi.com/v2/replicas"
    headers = {
        "x-api-key": tavus_key,
        "Content-Type": "application/json"
    }

    # AI Replica (Non-human): Skips the verbal consent requirement.
    data = {
        "replica_name": replica_name,
        "train_video_url": video_url
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        replica_id = response.json().get("replica_id")
        print(f"Success! Replica is now training. ID: {replica_id}")
        print("Training typically takes 4-6 hours.")
        return replica_id
    else:
        print(f"Tavus Error {response.status_code}: {response.text}")
        return None


def generate_tavus_pipeline():
    # 1. Check for existing local raw clip to save fal.ai credits
    if os.path.exists(RAW_CLIP_PATH):
        print(f"Found existing raw clip at {RAW_CLIP_PATH}. Skipping fal.ai generation.")
    else:
        if not os.getenv("FAL_KEY"):
            print("Error: Please set a valid FAL_KEY in your .env file.")
            return

        print(f"Raw clip not found. Starting fal.ai generation process...")

        # 2. Upload local person image to fal.ai
        image_url = fal_client.upload_file(LOCAL_IMAGE_PATH)

        # 3. Generate movement based on Tavus guidelines
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
        download_video(result['video']['url'], RAW_CLIP_PATH)

    # 4. Create the 2-minute seamless training video
    loop_video_for_tavus(RAW_CLIP_PATH, FINAL_TRAINING_VIDEO)

    # 5. Get public URL for the final video (Required by Tavus)
    print("Uploading final video to cloud for Tavus access...")
    public_training_url = fal_client.upload_file(FINAL_TRAINING_VIDEO)
    print(f"Public URL ready: {public_training_url}")

    # 6. Execute Tavus API call
    create_tavus_replica(public_training_url)


if __name__ == "__main__":
    generate_tavus_pipeline()