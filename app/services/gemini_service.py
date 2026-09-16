import json
import logging

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

client_kwargs = {"api_key": settings.gemini_api_key}
if settings.gemini_base_url:
    client_kwargs["http_options"] = {"base_url": settings.gemini_base_url}

client = genai.Client(**client_kwargs)


class TranscriptionResult(BaseModel):
    transcript: str
    translated_text: str


class GeminiTranscriptionError(Exception):
    pass


def _extract_json_text(raw_text: str) -> str:
    """
    Bəzi provider/proxy-lər (məs. OFOX) response_mime_type=application/json
    tələbini tam icra etmir və cavabı ```json ... ``` kimi markdown code
    fence içində qaytarır. Bunu təmizləyirik.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        # İlk sətri (```json və ya ```) və son ``` işarəsini at
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


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
        f"You will receive a short audio clip that may or may not contain a person "
        f"speaking {source_lang_name}.\n\n"
        "CRITICAL RULE: Only transcribe words that are ACTUALLY, CLEARLY spoken and "
        "audible in the recording. Do NOT guess, invent, or hallucinate speech. "
        "Background noise, silence, room tone, a fridge hum, breathing, static, "
        "or any non-speech sound is NOT speech - in these cases you MUST return "
        "empty strings for both fields. It is much better to return empty strings "
        "than to invent a sentence that was not actually said.\n\n"
        f"If (and only if) there is clear, audible, intelligible speech in "
        f"{source_lang_name}:\n"
        f"1) Transcribe exactly what is said in {source_lang_name}.\n"
        f"2) Translate that transcript into {target_lang_name}, naturally and fluently.\n\n"
        "Return ONLY a JSON object with EXACTLY these two keys, no other keys, "
        "no extra text, no markdown formatting:\n"
        '{"transcript": "...", "translated_text": "..."}\n'
        'Use the exact key name "translated_text" for the translation - '
        'do not call it "translation" or anything else.'
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
                temperature=0,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Something went wrong with the translation. Please try again.")
        raise GeminiTranscriptionError(str(exc)) from exc

    try:
        data = json.loads(_extract_json_text(response.text))
    except (ValueError, TypeError):
        logger.exception("Gemini cavabı JSON formatında deyil: %s", getattr(response, "text", None))
        raise GeminiTranscriptionError("We couldn't process the translation result. Please try again.")

    transcript = (data.get("transcript") or "").strip()
    # Bəzən model 'translated_text' əvəzinə 'translation' kimi fərqli açar
    # adı qaytarır (xüsusən proxy vasitəsilə) - ehtiyat olaraq bunları da yoxlayırıq
    translated_text = (
        data.get("translated_text")
        or data.get("translation")
        or ""
    ).strip()

    if not transcript:
        raise GeminiTranscriptionError("No speech was detected in the audio.")

    return {"transcript": transcript, "translated_text": translated_text}
