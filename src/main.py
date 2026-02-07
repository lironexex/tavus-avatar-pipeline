# src/main.py

import os
import sys
from dotenv import load_dotenv

# Path logic to ensure imports work from the src directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(SCRIPT_DIR)

# Import our modular components
import fal_generator
import audio_generator
import video_processor
import tavus_trigger
from dropbox_utils import upload_and_get_link


def run_pipeline():
    """
    Orchestrates the full Avatar creation pipeline:
    1. Fal (Movement) -> 2. Neural TTS (Audio) -> 3. FFmpeg (Merge) -> 4. Dropbox (Cloud) -> 5. Tavus (Train)
    """
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    # Configuration paths
    image_input = os.path.join(PROJECT_ROOT, "assets", "generated_person_example_1.png")
    raw_clip = os.path.join(PROJECT_ROOT, "assets", "raw_movement.mp4")
    training_audio = os.path.join(PROJECT_ROOT, "assets", "training_audio.aac")
    final_video = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")

    print("--- Phase 1: Asset Generation (Fal.ai) ---")
    if not os.path.exists(raw_clip):
        fal_generator.generate_avatar_movement(image_input, raw_clip)
    else:
        print(f"Using existing raw clip: {raw_clip}")

    print("\n--- Phase 2: Audio Generation (Neural TTS) ---")
    # audio_generator now uses edge-tts for a natural male voice
    audio_success = audio_generator.generate_training_audio(training_audio)

    if not audio_success:
        print("Pipeline stopped: Audio generation failed.")
        return

    print("\n--- Phase 3: Final Merging (FFmpeg) ---")
    # Merge the looped visual with the natural speech-then-silence audio
    video_processor.merge_video_and_audio(raw_clip, training_audio, final_video)

    print("\n--- Phase 4: Cloud Upload & API Trigger ---")
    # Upload and get direct link for Tavus
    video_url = upload_and_get_link(final_video)

    if video_url:
        replica_id = tavus_trigger.trigger_tavus(video_url)

        if replica_id:
            # Automatic status check to catch initial validation errors
            tavus_trigger.check_status_automated(replica_id)
            print("\nPipeline complete! Please wait 4-6 hours for training.")
        else:
            print("Failed to start Tavus training.")
    else:
        print("Failed to get Dropbox link.")


if __name__ == "__main__":
    run_pipeline()