from fastapi import APIRouter, HTTPException, Response

from app.schemas import SpeakRequest
from app.services.tts_service import SpeechSynthesisError, synthesize_speech

router = APIRouter(prefix="/speak", tags=["speak"])


@router.post("")
async def speak(payload: SpeakRequest):
    try:
        audio_bytes = synthesize_speech(payload.text, payload.language)
    except SpeechSynthesisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(content=audio_bytes, media_type="audio/mpeg")
