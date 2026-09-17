import io
import json
import logging
import wave

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
        logger.exception("Gemini sorğusu uğursuz oldu")
        raise GeminiTranscriptionError(str(exc)) from exc

    try:
        data = json.loads(_extract_json_text(response.text))
    except (ValueError, TypeError):
        logger.exception("Gemini cavabı JSON formatında deyil: %s", getattr(response, "text", None))
        raise GeminiTranscriptionError("Gemini cavabı emal edilə bilmədi")

    transcript = (data.get("transcript") or "").strip()
    # Bəzən model 'translated_text' əvəzinə 'translation' kimi fərqli açar
    # adı qaytarır (xüsusən proxy vasitəsilə) - ehtiyat olaraq bunları da yoxlayırıq
    translated_text = (
        data.get("translated_text")
        or data.get("translation")
        or ""
    ).strip()

    if not transcript:
        raise GeminiTranscriptionError("Səsdə heç bir nitq aşkarlanmadı")

    return {"transcript": transcript, "translated_text": translated_text}


class SpeechSynthesisError(Exception):
    pass


# Gemini-nin hazır səsləri arasından seçilib - neytral, aydın bir səs.
# Tam siyahı: https://ai.google.dev/gemini-api/docs/speech-generation
_TTS_VOICE_NAME = "Kore"

# Gemini native audio çıxışının formatı: 16-bit PCM, mono, 24kHz
_PCM_SAMPLE_RATE = 24000
_PCM_CHANNELS = 1
_PCM_SAMPLE_WIDTH = 2  # bytes (16-bit)


def synthesize_speech(text: str) -> bytes:
    """
    Verilmiş mətni Gemini-nin native TTS modeli ilə səsə çevirir və
    birbaşa oxuna bilən WAV bytes qaytarır (frontend heç bir əlavə
    decode/convert etmədən birbaşa oynada bilsin deyə).
    """
    if not text or not text.strip():
        raise SpeechSynthesisError("Səsləndirmək üçün mətn boşdur")

    try:
        response = client.models.generate_content(
            model=settings.gemini_tts_model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=_TTS_VOICE_NAME
                        )
                    )
                ),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini TTS sorğusu uğursuz oldu")
        raise SpeechSynthesisError(str(exc)) from exc

    try:
        pcm_bytes = response.candidates[0].content.parts[0].inline_data.data
    except (AttributeError, IndexError, TypeError):
        logger.exception("Gemini TTS cavabında audio tapılmadı")
        raise SpeechSynthesisError("Gemini audio qaytarmadı")

    if not pcm_bytes:
        raise SpeechSynthesisError("Gemini boş audio qaytardı")

    # Xam PCM-i WAV konteynerinə bükürük ki, frontend-də birbaşa
    # standart audio player ilə oynadıla bilsin (PCM tək başına
    # sample rate/kanal məlumatı daşımır).
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(_PCM_CHANNELS)
        wav_file.setsampwidth(_PCM_SAMPLE_WIDTH)
        wav_file.setframerate(_PCM_SAMPLE_RATE)
        wav_file.writeframes(pcm_bytes)

    return wav_buffer.getvalue()
