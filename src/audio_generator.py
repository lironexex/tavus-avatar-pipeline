# src/audio_generator.py

import os
from gtts import gTTS
import ffmpeg
from dotenv import load_dotenv

# 1. Determine the Project Root (one level up from 'src')
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
    "This process involves many steps, including video generation and audio syncing."
)


def generate_training_audio(output_path):
    """
    Generates the required 2-minute training audio:
    - 00:00 - 01:00: Speech (Consent + Story)
    - 01:00 - 02:00: Silence
    """
    print("Generating 2-minute training audio (1m speech + 1m silence)...")

    temp_speech_mp3 = os.path.join(PROJECT_ROOT, "assets", "temp_speech.mp3")

    try:
        # Step 1: Generate the speech using Google Text-to-Speech
        tts = gTTS(text=CONSENT_TEXT + STORY_TEXT, lang='en')
        tts.save(temp_speech_mp3)

        # Step 2: Use FFmpeg to concat 60s of speech with 60s of silence
        # We move loglevel inside .output() to avoid the 'unexpected keyword' error
        (
            ffmpeg
            .filter([
                ffmpeg.input(temp_speech_mp3).filter('atrim', duration=60).filter('apad', whole_len=44100 * 60),
                ffmpeg.input('anullsrc=r=44100:cl=mono', f='lavfi', t=60)
            ], 'concat', n=2, v=0, a=1)
            .output(output_path, acodec='aac', ar=44100, loglevel="error")
            .run(overwrite_output=True)
        )
        print(f"✅ Success! Training audio created at: {output_path}")
        return True

    except Exception as e:
        print(f"Audio Generation Error: {e}")
        return False
    finally:
        # Clean up the temporary MP3 file
        if os.path.exists(temp_speech_mp3):
            os.remove(temp_speech_mp3)


if __name__ == "__main__":
    # Allows for standalone testing of the audio script
    test_path = os.path.join(PROJECT_ROOT, "assets", "training_audio.aac")
    generate_training_audio(test_path)