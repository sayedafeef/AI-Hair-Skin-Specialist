import os
import uuid
from pathlib import Path

from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
AUDIO_OUTPUT_DIR = BASE_DIR / "generated_audio"

DEEPGRAM_TTS_CHAR_LIMIT = 2000


def _split_text(text, limit=DEEPGRAM_TTS_CHAR_LIMIT):
    """Splits text into chunks under `limit` chars, breaking on sentence
    boundaries where possible so audio doesn't cut mid-sentence."""
    text = text.strip()
    if len(text) <= limit:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        split_at = max(
            window.rfind(". "),
            window.rfind("! "),
            window.rfind("? "),
            window.rfind("\n"),
        )
        if split_at == -1 or split_at < limit * 0.5:
            split_at = window.rfind(" ")
        if split_at == -1:
            split_at = limit

        chunks.append(remaining[:split_at + 1].strip())
        remaining = remaining[split_at + 1:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def convert_text_to_speech(text):
    """Converts specialist text guidance to speech using Deepgram TTS.

    Splits text longer than Deepgram's 2000-character-per-request limit
    into multiple chunks, synthesizes each separately, and writes the
    resulting MP3 byte streams back-to-back into one uniquely-named file
    (uuid-based, since this API may serve many concurrent requests).
    No ffmpeg/pydub dependency - consecutive MP3 frame streams concatenate
    cleanly on their own.
    """
    deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not deepgram_api_key:
        raise ValueError("DEEPGRAM_API_KEY is missing from environment variables.")

    client = DeepgramClient(api_key=deepgram_api_key)
    model = os.environ.get("DEEPGRAM_TTS_MODEL", "aura-2-thalia-en")

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = AUDIO_OUTPUT_DIR / f"{uuid.uuid4().hex}.mp3"

    chunks = _split_text(text)

    with open(output_path, "wb") as out_file:
        for chunk in chunks:
            response = client.speak.v1.audio.generate(text=chunk, model=model)
            for data in response:
                out_file.write(data)

    return str(output_path)
