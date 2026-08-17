from fastapi import APIRouter, Response
from pydantic import BaseModel

from services.tts_service import synthesize_speech
from utils.exception_handler import ExceptionBase

router = APIRouter()

# Default delivery style for the scan/chat voice — matches the product's
# "warm, direct, friend-toned" voice principle (see prompts/wabi_sabi_scan.prompt).
DEFAULT_STYLE = "warmly, like a knowledgeable friend, at a calm and reassuring pace"


class TtsRequest(BaseModel):
    text: str
    style: str | None = None


@router.post("/tts")
async def text_to_speech(payload: TtsRequest):
    if not payload.text.strip():
        raise ExceptionBase(status_code=400, message="No text to speak.")

    try:
        audio_bytes = await synthesize_speech(payload.text, payload.style or DEFAULT_STYLE)
    except Exception as e:
        print(f"[tts] synthesis failed: {e}")
        raise ExceptionBase(status_code=502, message="Voice synthesis is unavailable right now.") from e

    return Response(content=audio_bytes, media_type="audio/wav")
