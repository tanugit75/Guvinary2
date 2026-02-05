from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.auth import ApiKeyMiddleware
from app.model import VoiceClassifier
from app.preprocessing import AudioPreprocessingError, decode_base64_audio, mp3_to_wav_16k_mono
from app.schemas import DetectRequest, DetectResponse

classifier: VoiceClassifier | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global classifier
    classifier = VoiceClassifier()
    yield


app = FastAPI(
    title="Voice Authenticity Detection API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(ApiKeyMiddleware)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/detect", response_model=DetectResponse)
async def detect_voice(request: DetectRequest) -> DetectResponse:
    if classifier is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        mp3_bytes = decode_base64_audio(request.audio_base64)
        waveform, sample_rate = mp3_to_wav_16k_mono(mp3_bytes)
    except AudioPreprocessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = classifier.predict(waveform=waveform, sampling_rate=sample_rate)

    return DetectResponse(
        request_id=request.request_id,
        language=request.language,
        classification=result.classification,
        confidence=result.confidence,
        model_name=classifier.model_name,
        scores=result.scores,
    )
