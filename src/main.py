# src/main.py

import os
import sys
from dotenv import load_dotenv

# Path logic to ensure imports work from the src directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)

# Import our new modular components
import fal_generator
import video_processor
import tavus_trigger
from dropbox_utils import upload_and_get_link


def run_pipeline():
    """
    Orchestrates the full Avatar creation pipeline:
    1. Fal (Generation) -> 2. FFmpeg (Processing) -> 3. Dropbox (Upload) -> 4. Tavus (Trigger)
    """
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    # Configuration paths
    image_input = os.path.join(PROJECT_ROOT, "assets", "generated_person_example_1.png")
    raw_clip = os.path.join(PROJECT_ROOT, "assets", "raw_movement.mp4")
    final_video = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")

    print("--- Phase 1: Asset Generation (Fal.ai) ---")
    # Only generate the expensive raw clip if it doesn't exist
    if not os.path.exists(raw_clip):
        fal_generator.generate_avatar_movement(image_input, raw_clip)
    else:
        print(f"Using existing raw clip: {raw_clip}")

    print("\n--- Phase 2: Video Processing (FFmpeg) ---")
    # Always process to ensure the latest codec fixes are applied
    video_processor.loop_video_for_tavus(raw_clip, final_video)

    print("\n--- Phase 3: Cloud Upload & API Trigger ---")
    # Upload and get the direct link
    video_url = upload_and_get_link(final_video)

    if video_url:
        # Trigger the training
        replica_id = tavus_trigger.trigger_tavus(video_url)

        if replica_id:
            # Immediate status verification
            tavus_trigger.check_status_automated(replica_id)
            print("\nPipeline complete! Monitor the Replica ID above.")
        else:
            print("Failed to start Tavus training.")
    else:
        print("Failed to get Dropbox link.")


if __name__ == "__main__":
    run_pipeline()