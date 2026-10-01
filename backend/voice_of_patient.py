import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def transcribe_patient_voice(audio_filepath):
    """Transcribes patient audio file using Groq's Whisper API.

    Accepts any of Groq's supported formats directly (flac, mp3, mp4, mpeg,
    mpga, m4a, ogg, wav, webm) - including the webm output of a browser's
    MediaRecorder, so no client-side audio conversion is needed.
    """
    if not audio_filepath:
        raise ValueError("No audio filepath provided for transcription.")

    file_path_str = str(audio_filepath)
    groq_api_key = os.environ.get("GROQ_API_KEY")

    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")

    client = Groq(api_key=groq_api_key)

    with open(file_path_str, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(Path(file_path_str).name, audio_file.read()),
            model=os.environ.get("WHISPER_MODEL", "whisper-large-v3"),
        )

    return transcription.text
