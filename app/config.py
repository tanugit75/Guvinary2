from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str = "change-me"
    model_id: str = "superb/wav2vec2-base-superb-sid"
    model_revision: str = "main"
    host: str = "0.0.0.0"
    port: int = 8000
    max_audio_bytes: int = 10 * 1024 * 1024
    target_sample_rate: int = 16000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
