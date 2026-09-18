from pydantic import BaseModel


class TranslateResponse(BaseModel):
    transcript: str          # danışılan orijinal mətn
    translated_text: str     # tərcümə olunmuş mətn
    source_lang: str         # məs: "tr"
    target_lang: str         # məs: "en"


class ErrorResponse(BaseModel):
    detail: str


class SpeakRequest(BaseModel):
    text: str
    language: str = "en"
