# Foreign Talker — Backend

FastAPI + Gemini API (`google-genai` rəsmi SDK, model: `gemini-3.6-flash`).
Audio faylını qəbul edir, Gemini birbaşa multimodal olaraq mətnə çevirir
və tərcümə edir (ayrıca STT addımı yoxdur).

> Qeyd: köhnə `google-generativeai` kitabxanası 2025-ci ilin noyabrından
> deprecated-dir və artıq işləmir. Bu layihə yeni `google-genai` SDK-nı
> istifadə edir (`from google import genai`).

## Qurulum

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylını aç və `GEMINI_API_KEY` dəyərini
https://aistudio.google.com/apikey ünvanından aldığın açarla doldur.

## İşə salmaq

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Telefon ilə eyni Wi-Fi şəbəkəsində olmalısan. Frontend-də backend URL-i
kompüterinin lokal IP-si olmalıdır (məs. `http://192.168.1.20:8000`),
`localhost` yox — çünki telefon ayrı cihazdır.

## Test

```bash
curl -X POST http://localhost:8000/translate/audio \
  -F "audio=@test.m4a" \
  -F "source_lang=tr" \
  -F "target_lang=en"
```

Cavab:
```json
{
  "transcript": "Merhaba",
  "translated_text": "Hello",
  "source_lang": "tr",
  "target_lang": "en"
}
```

## Struktur

```
backend/
├── main.py                    # FastAPI app + CORS
├── app/
│   ├── config.py              # .env oxuyur (GEMINI_API_KEY)
│   ├── languages.py           # dil kodu -> tam ad (frontend ilə sinxron)
│   ├── schemas.py             # response modelləri
│   ├── routers/
│   │   └── translate.py       # POST /translate/audio
│   └── services/
│       └── gemini_service.py  # Gemini çağırışı + JSON parse
├── requirements.txt
└── .env.example
```

## Sonrakı addımlar

- Frontend-də `expo-av` ilə audio qeydi + bu endpoint-ə göndərmə
- Rate limiting / audio ölçü limiti (Gemini-nin inline data limiti ~20MB-dır)
- Uzun audio üçün `genai.upload_file` ilə fayl yükləmə üsuluna keçid
