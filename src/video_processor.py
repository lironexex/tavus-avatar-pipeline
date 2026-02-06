# src/video_processor.py

import os
import ffmpeg
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def loop_video_for_tavus(input_path, output_path, target_duration=120):
    """
    Final Fix based on official Tavus Documentation:
    1. Force 1080p resolution.
    2. Use H.264 for video.
    3. Include AAC audio (even if silent).
    """
    print(f"Processing 120s video: 1080p, H.264 + AAC (Tavus Specs)...")

    try:
        # We generate a silent audio source to satisfy the AAC requirement
        silent_audio = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', f='lavfi')

        # Input video looped to 120s
        input_vid = ffmpeg.input(input_path, stream_loop=24)

        (
            ffmpeg
            .output(
                input_vid.video,
                silent_audio.audio,
                output_path,
                t=target_duration,
                vcodec='libx264',
                acodec='aac',  # MANDATORY: AAC audio codec
                pix_fmt='yuv420p',
                vf='scale=1920:1080',  # MANDATORY: Minimum 1080p
                r=25,  # MANDATORY: 25 fps
                movflags='+faststart',
                shortest=None,
                loglevel="error"
            )
            .run(overwrite_output=True)
        )
        print(f"Success! Video matches Tavus requirements at: {output_path}")

    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode() if e.stderr else str(e)}")