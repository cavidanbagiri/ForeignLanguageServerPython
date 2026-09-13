from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"
    # Boş qalsa - birbaşa Google-a qoşulur.
    # Proxy (OFOX və s.) istifadə edəndə buraya proxy-nin gemini-native
    # base_url-ini yaz, məs: https://api.ofox.ai/gemini
    gemini_base_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
