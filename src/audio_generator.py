# src/audio_generator.py

import os
import asyncio
import edge_tts
import ffmpeg
from dotenv import load_dotenv

# 1. Determine the Project Root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Official Tavus Script - Required for Personal Replicas
CONSENT_TEXT = (
    "I, Liron Haber, am currently speaking and give consent to Tavus to create an AI clone of me "
    "by using the audio and video samples I provide. I understand that this AI clone can be used "
    "to create videos that look and sound like me. "
)

# Filler story to ensure we have enough speech for the first minute
STORY_TEXT = (
    "Now I will read a short story. The sun was shining brightly over the park in Nesher. "
    "I am working on a professional AI avatar pipeline using the Phoenix 3 model. "
    "It is important to maintain a steady tone and natural pauses during this recording. "
    "I am sitting upright and looking directly at the camera. "
    "This process involves many steps, including video generation and audio syncing. "
    "The goal is to achieve high-fidelity lip-sync and natural movement for the final replica."
    "Hopefully everything will go smoothly, I am excited to work around this problem."
    "I will be now silent for about 1 minute as it was a requirement from Tavus."
)


async def generate_neural_speech(text, output_path):
    """Generates natural male neural speech."""
    # 'en-US-ChristopherNeural' is a very clear, professional male voice
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_path)


def generate_training_audio(output_path):
    """
    Generates the required 2-minute training audio:
    - 00:00 - 01:00: Natural Neural Male Speech
    - 01:00 - 02:00: Digital Silence
    """
    print("Generating natural 2-minute training audio (Neural Male Voice)...")

    temp_speech_mp3 = os.path.join(PROJECT_ROOT, "assets", "temp_speech.mp3")

    try:
        # Step 1: Generate high-quality neural speech
        asyncio.run(generate_neural_speech(CONSENT_TEXT + STORY_TEXT, temp_speech_mp3))

        # Step 2: Concat 60s speech with 60s silence using clean FFmpeg filters
        # We ensure 44100Hz and mono to remove that background hum
        speech_input = ffmpeg.input(temp_speech_mp3).filter('atrim', duration=60)
        silence_input = ffmpeg.input('anullsrc=r=44100:cl=mono', f='lavfi', t=60)

        (
            ffmpeg
            .concat(speech_input, silence_input, v=0, a=1)
            .output(output_path, acodec='aac', ar=44100, ac=1, loglevel="error")
            .run(overwrite_output=True)
        )
        print(f"✅ Success! Natural training audio created at: {output_path}")
        return True

    except Exception as e:
        print(f"Audio Generation Error: {e}")
        return False
    finally:
        if os.path.exists(temp_speech_mp3):
            os.remove(temp_speech_mp3)


if __name__ == "__main__":
    test_path = os.path.join(PROJECT_ROOT, "assets", "training_audio.aac")
    generate_training_audio(test_path)