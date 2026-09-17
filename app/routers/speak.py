from fastapi import APIRouter, HTTPException, Response

from app.schemas import SpeakRequest
from app.services.gemini_service import SpeechSynthesisError, synthesize_speech

router = APIRouter(prefix="/speak", tags=["speak"])


@router.post("")
async def speak(payload: SpeakRequest):
    try:
        wav_bytes = synthesize_speech(payload.text)
    except SpeechSynthesisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(content=wav_bytes, media_type="audio/wav")
