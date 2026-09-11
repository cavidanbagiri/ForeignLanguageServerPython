import json
import logging

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)


class TranscriptionResult(BaseModel):
    transcript: str
    translated_text: str


class GeminiTranscriptionError(Exception):
    pass


def transcribe_and_translate(
    audio_bytes: bytes,
    mime_type: str,
    source_lang_name: str,
    target_lang_name: str,
) -> dict:
    """
    Audio bytes-i birbaşa Gemini-yə göndərir, həm mətnə çevirir, həm tərcümə edir.
    Ayrıca STT servisinə ehtiyac yoxdur - Gemini multimodal olaraq audio-nu oxuyur.
    """
    prompt = (
        f"You will receive a short audio clip of a person speaking {source_lang_name}. "
        f"1) Transcribe exactly what is said in {source_lang_name}. "
        f"2) Translate that transcript into {target_lang_name}, naturally and fluently. "
        "Return only the JSON object matching the given schema. "
        "If the audio is silent, unclear, or contains no speech, "
        "return transcript and translated_text as empty strings."
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TranscriptionResult,
                temperature=0.2,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini sorğusu uğursuz oldu")
        raise GeminiTranscriptionError(str(exc)) from exc

    try:
        data = json.loads(response.text)
    except (ValueError, TypeError):
        logger.exception("Gemini cavabı JSON formatında deyil: %s", getattr(response, "text", None))
        raise GeminiTranscriptionError("Gemini cavabı emal edilə bilmədi")

    transcript = (data.get("transcript") or "").strip()
    translated_text = (data.get("translated_text") or "").strip()

    if not transcript:
        raise GeminiTranscriptionError("Səsdə heç bir nitq aşkarlanmadı")

    return {"transcript": transcript, "translated_text": translated_text}
