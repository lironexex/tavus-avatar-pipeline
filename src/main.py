# src/main.py

import os
import sys
from dotenv import load_dotenv

# Path logic to ensure imports work from the src directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)

# Import our custom modules
import video_processor
import tavus_trigger


def run_pipeline():
    """
    Orchestrates the full Avatar creation pipeline:
    1. Process Video -> 2. Upload to Dropbox -> 3. Trigger Tavus
    """
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    # Define paths
    input_video = os.path.join(PROJECT_ROOT, "assets", "raw_movement.mp4")
    output_video = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")

    print("--- Phase 1: Video Processing ---")
    if not os.path.exists(input_video):
        print(f"Error: Input video not found at {input_video}")
        return

    # Process video with strict H.264 settings for Tavus Phoenix-3
    video_processor.loop_video_for_tavus(input_video, output_video)

    print("\n--- Phase 2: Upload and Trigger ---")
    # Step 2 & 3: Upload to Dropbox and start Tavus training
    video_url = tavus_trigger.upload_and_get_link(output_video)

    if video_url:
        replica_id = tavus_trigger.trigger_tavus(video_url)

        if replica_id:
            # Step 4: Final verification check
            tavus_trigger.check_status_automated(replica_id)
            print("\nPipeline complete! Monitor status with check_status.py")
        else:
            print("Failed to trigger Tavus API.")
    else:
        print("Failed to upload video to Dropbox.")


if __name__ == "__main__":
    run_pipeline()