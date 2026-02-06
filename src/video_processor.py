# src/video_processor.py

import os
import ffmpeg
from dotenv import load_dotenv

# 1. Determine the Project Root (one level up from 'src')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Load environment variables for absolute path consistency
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def loop_video_for_tavus(input_path, output_path, target_duration=120):
    """
    Creates a training video using ultra-compatible 'Nuclear' settings.
    Forces 8-bit depth, Baseline profile, and strips all metadata.
    """
    print(f"Applying Nuclear Codec Fix: Stripping metadata and forcing 8-bit Baseline H.264...")

    try:
        # Use a single-pass approach to avoid stream sync issues
        # We loop the input first, then apply the strict encoding
        (
            ffmpeg
            .input(input_path, stream_loop=24)  # Ensure enough loops for 120s
            .output(
                output_path,
                t=target_duration,  # Limit final output to exactly 120s
                vcodec='libx264',  # Standard H.264 codec
                pix_fmt='yuv420p',  # Strict 8-bit pixel format
                profile='baseline',  # Simplest profile for max compatibility
                level='3.0',  # Broadly accepted level
                r=25,  # Mandatory 25fps for Phoenix-3
                crf=23,  # Balanced quality/file size
                map_metadata=-1,  # STRIP ALL HIDDEN METADATA
                an=None,  # STRIP ALL AUDIO (Required)
                movflags='+faststart',  # Allow API to read metadata instantly
                loglevel="error"
            )
            .run(overwrite_output=True)
        )
        print(f"Success! Compatible training video ready at: {output_path}")

    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")


if __name__ == "__main__":
    # Fallback for direct testing if not run through main.py
    RAW_CLIP = os.path.join(PROJECT_ROOT, "assets", "raw_movement.mp4")
    FINAL_VIDEO = os.path.join(PROJECT_ROOT, "assets", "tavus_training_video.mp4")

    if os.path.exists(RAW_CLIP):
        loop_video_for_tavus(RAW_CLIP, FINAL_VIDEO)
    else:
        print(f"Error: Could not find raw clip at {RAW_CLIP}")