from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import speak, translate

app = FastAPI(title="Foreign Talker Backend", version="0.1.0")

# Development üçün açıq CORS. Production-da öz domenini/IP-ni yaz.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translate.router)
app.include_router(speak.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
