import logging

from google.cloud import texttospeech

logger = logging.getLogger(__name__)

_client = texttospeech.TextToSpeechClient()

# Frontend-dəki dil kodlarını Google Cloud TTS-in gözlədiyi BCP-47
# lokal koduna çeviririk. Voice adını əl ilə seçmirik - Google həmin dil
# üçün ən yaxşı mövcud səsi (Wavenet/Neural2) avtomatik seçsin deyə.
LANGUAGE_TO_LOCALE = {
    "tr": "tr-TR",
    "en": "en-US",
    "de": "de-DE",
    "fr": "fr-FR",
    "es": "es-ES",
    "it": "it-IT",
    "ru": "ru-RU",
    "ja": "ja-JP",
    "zh": "zh-CN",
    "ar": "ar-XA",
    "pt": "pt-PT",
    "nl": "nl-NL",
    "pl": "pl-PL",
    "sv": "sv-SE",
    "no": "nb-NO",
    "da": "da-DK",
    "fi": "fi-FI",
    "el": "el-GR",
    "he": "he-IL",
    "hi": "hi-IN",
    "ko": "ko-KR",
}


class SpeechSynthesisError(Exception):
    pass


def synthesize_speech(text: str, language_code: str) -> bytes:
    """
    Mətni Google Cloud Text-to-Speech ilə səsə çevirir, MP3 bytes qaytarır.
    """
    if not text or not text.strip():
        raise SpeechSynthesisError("Səsləndirmək üçün mətn boşdur")

    locale = LANGUAGE_TO_LOCALE.get(language_code, "en-US")

    try:
        response = _client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=locale,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Google Cloud TTS sorğusu uğursuz oldu")
        raise SpeechSynthesisError(str(exc)) from exc

    if not response.audio_content:
        raise SpeechSynthesisError("Google boş audio qaytardı")

    return response.audio_content
