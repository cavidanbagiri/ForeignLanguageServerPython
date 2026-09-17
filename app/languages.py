# Bu fayl frontend-dəki data/languages.js ilə sinxron saxlanmalıdır.
# Gemini-yə prompt yazarkən dil kodunu deyil, tam adını göndəririk (daha dəqiq nəticə üçün).

LANGUAGE_NAMES = {
    "tr": "Turkish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "el": "Greek",
    "he": "Hebrew",
    "hi": "Hindi",
    "ko": "Korean",
}


def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)
