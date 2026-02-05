from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class SupportedLanguage(str, Enum):
    tamil = "Tamil"
    english = "English"
    hindi = "Hindi"
    malayalam = "Malayalam"
    telugu = "Telugu"


class DetectRequest(BaseModel):
    audio_base64: str = Field(..., min_length=100, description="Base64 encoded MP3 audio")
    language: SupportedLanguage
    request_id: Optional[str] = Field(default=None, max_length=128)


class DetectResponse(BaseModel):
    request_id: Optional[str]
    language: SupportedLanguage
    classification: str
    confidence: float
    model_name: str
    scores: Dict[str, float]
