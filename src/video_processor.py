# src/video_processor.py

import os
import ffmpeg
from dotenv import load_dotenv

# 1. Determine the Project Root (one level up from 'src')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Load environment variables for absolute path consistency
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def merge_video_and_audio(video_input, audio_input, output_path):
    """
    Merges the generated video movement with the training audio.
    Ensures 1080p resolution and AAC audio codec as per Tavus requirements.
    """
    print("Merging video and audio into final 1080p training file...")

    try:
        # Step 1: Input the raw video clip and loop it to match the 120s audio
        # stream_loop=24 ensures we have enough frames for 2 minutes
        v = ffmpeg.input(video_input, stream_loop=24)

        # Step 2: Input the pre-generated training audio (1m speech + 1m silence)
        a = ffmpeg.input(audio_input)

        # Step 3: Combine them using strict Tavus Phoenix-3 specifications
        (
            ffmpeg
            .output(
                v.video,
                a.audio,
                output_path,
                t=120,  # Force exactly 120 seconds duration
                vcodec='libx264',  # Standard H.264 video codec
                acodec='aac',  # MANDATORY: AAC audio codec for mp4 containers
                pix_fmt='yuv420p',  # Standard 8-bit color depth
                vf='scale=1920:1080',  # MANDATORY: Minimum 1080p resolution
                r=25,  # MANDATORY: 25 frames per second
                movflags='+faststart',  # Optimizes file for faster web/API processing
                loglevel="error"
            )
            .run(overwrite_output=True)
        )
        print(f"✅ Success! Final training video created at: {output_path}")

    except ffmpeg.Error as e:
        # Decode and print FFmpeg errors for easier debugging
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")

if __name__ == "__main__":
    # Standard paths for standalone testing
    RAW_CLIP = os.path.join(PROJECT_ROOT, "assets", "raw_movement.mp4")
    TRAINING_AUDIO = os.path.join(PROJECT_ROOT, "assets", "training_audio.aac")
    FINAL_VIDEO = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")

    if os.path.exists(RAW_CLIP) and os.path.exists(TRAINING_AUDIO):
        merge_video_and_audio(RAW_CLIP, TRAINING_AUDIO, FINAL_VIDEO)
    else:
        print("Error: Missing input assets for merging.")