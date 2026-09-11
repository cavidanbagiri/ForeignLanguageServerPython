from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.languages import get_language_name
from app.schemas import TranslateResponse
from app.services.gemini_service import GeminiTranscriptionError, transcribe_and_translate

router = APIRouter(prefix="/translate", tags=["translate"])

# expo-av ilə qeyd edilən audio adətən bunlardan biri olur
ALLOWED_MIME_TYPES = {
    "audio/m4a",
    "audio/mp4",
    "audio/x-m4a",
    "audio/wav",
    "audio/webm",
    "audio/3gpp",
    "audio/aac",
}


@router.post("/audio", response_model=TranslateResponse)
async def translate_audio(
    audio: UploadFile = File(..., description="Qeyd olunmuş səs faylı"),
    source_lang: str = Form(..., description="Danışanın dil kodu, məs: 'tr'"),
    target_lang: str = Form(..., description="Hədəf dil kodu, məs: 'en'"),
):
    if audio.content_type not in ALLOWED_MIME_TYPES:
        # Bəzi cihazlarda content_type boş/fərqli gələ bilər - bloklamırıq, sadəcə xəbərdarlıq
        pass

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Boş audio faylı")

    source_lang_name = get_language_name(source_lang)
    target_lang_name = get_language_name(target_lang)

    try:
        result = transcribe_and_translate(
            audio_bytes=audio_bytes,
            mime_type=audio.content_type or "audio/m4a",
            source_lang_name=source_lang_name,
            target_lang_name=target_lang_name,
        )
    except GeminiTranscriptionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return TranslateResponse(
        transcript=result["transcript"],
        translated_text=result["translated_text"],
        source_lang=source_lang,
        target_lang=target_lang,
    )
