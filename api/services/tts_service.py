"""
Text-to-speech via the Gemini API — same GEMINI_API_KEY already used for
chat/scan generation, no new credential. Confirmed live (2026-08-17):
gemini-2.5-flash-preview-tts returns raw 16-bit PCM audio at 24kHz mono
(mime_type "audio/L16;codec=pcm;rate=24000"), which browsers can't play
directly — it's wrapped in a WAV container here before being returned.

Optional by nature: if this fails for any reason, callers (routers/tts.py)
should let the frontend fall back to the browser's own SpeechSynthesis —
voice narration must never be a hard dependency on this endpoint.
"""

import io
import os
import wave

from google import genai
from google.genai import types

TTS_MODEL = os.getenv("TTS_MODEL", "gemini-2.5-flash-preview-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "Kore")
SAMPLE_RATE = 24000

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


async def synthesize_speech(text: str, style: str | None = None) -> bytes:
    """Returns WAV-encoded audio bytes. `style` is an optional natural-
    language delivery instruction (e.g. "warmly and reassuringly") — Gemini
    TTS follows style prompts prepended to the text itself."""
    prompt = f"Say {style}: {text}" if style else text

    response = _client.models.generate_content(
        model=TTS_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE)
                )
            ),
        ),
    )
    part = response.candidates[0].content.parts[0]
    return _pcm_to_wav(part.inline_data.data)
