# Voice Authenticity Detection API (FastAPI)

Production-ready FastAPI REST API that classifies whether a base64-encoded MP3 voice sample is **AI-generated** or **Human** with a confidence score.

## Features

- FastAPI async REST API
- Input: base64 MP3 in JSON
- Output: classification + confidence
- Language-aware request support:
  - Tamil
  - English
  - Hindi
  - Malayalam
  - Telugu
- Audio preprocessing pipeline:
  - Decode base64
  - Convert MP3 -> 16 kHz mono WAV (FFmpeg)
  - Normalize waveform for model inference
- Pre-trained model inference using Hugging Face `AutoModelForAudioClassification`
- API Key authentication middleware (`X-API-Key` header)
- Health checks and robust error handling
- Dockerized deployment option and Render/Railway-ready setup

---

## Project Structure

```bash
.
├── app
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── main.py
│   ├── model.py
│   ├── preprocessing.py
│   └── schemas.py
├── requirements.txt
└── README.md
```

---

## Quick Start (Local)

### 1) Clone and install

```bash
git clone <your-repo-url>
cd Guvinary2
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Install FFmpeg

FFmpeg is required to decode MP3 files.

- Ubuntu/Debian:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg
  ```
- macOS:
  ```bash
  brew install ffmpeg
  ```

### 3) Configure environment variables

#### Generate your own API key (recommended)

Use one of these commands to generate a strong random key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

or

```bash
openssl rand -hex 32
```

#### Where to put the API key

You can set it in either place:

1. **Shell environment** (quick local run)
2. **`.env` file** in the project root (recommended for development)

Create `.env` from template:

```bash
cp .env.example .env
```

Then edit `.env` and set:

```env
API_KEY=<your-generated-key>
MODEL_ID=superb/wav2vec2-base-superb-sid
MODEL_REVISION=main
HOST=0.0.0.0
PORT=8000
```

> In requests, send the same value in header: `X-API-Key: <your-generated-key>`.

```bash
export API_KEY="super-secret-key"
export MODEL_ID="wav2vec2-large-robust-ft-libri-960h"  # optional override
export MODEL_REVISION="main"                            # optional
export HOST="0.0.0.0"
export PORT="8000"
```

> **Important:** Use a Hugging Face audio-classification model that provides labels for human/AI or bonafide/spoof for best results. `MODEL_ID` can be replaced at runtime with your preferred anti-spoof model.

### 4) Run server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs: `http://localhost:8000/docs`

---

## API Reference

### `POST /v1/detect`

Classifies a voice sample as AI-generated or Human.

**Headers:**
- `X-API-Key: <your_api_key>`

**Request JSON:**

```json
{
  "audio_base64": "SUQzBAAAAAA...<base64_mp3>",
  "language": "English",
  "request_id": "demo-001"
}
```

**Response JSON (200):**

```json
{
  "request_id": "demo-001",
  "language": "English",
  "classification": "Human",
  "confidence": 0.9134,
  "model_name": "your-model-id",
  "scores": {
    "AI-generated": 0.0866,
    "Human": 0.9134
  }
}
```

### `GET /health`

Health probe endpoint.

---

## cURL Example

```bash
curl -X POST "http://localhost:8000/v1/detect" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: super-secret-key" \
  -d '{
    "audio_base64": "<BASE64_MP3_HERE>",
    "language": "Tamil",
    "request_id": "hackathon-42"
  }'
```

---

## Deployment

### Option A: Render

1. Push code to GitHub.
2. Create a **Web Service** on Render.
3. Set Build Command:
   ```bash
   pip install -r requirements.txt
   ```
4. Set Start Command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Add environment variables:
   - `API_KEY`
   - `MODEL_ID`
   - `MODEL_REVISION` (optional)
6. Add FFmpeg in Render native environment using apt buildpack or use Docker deployment.

### Option B: Railway

1. Create a new Railway project linked to the repo.
2. Add env vars (`API_KEY`, `MODEL_ID`, etc.).
3. Ensure FFmpeg availability:
   - Preferred: Docker deploy.
4. Start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Option C: Docker (Recommended)

Create a `Dockerfile` like:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t voice-auth-api .
docker run -p 8000:8000 -e API_KEY=super-secret-key -e MODEL_ID=<your-model-id> voice-auth-api
```

---

## Hackathon Production Readiness Notes

- Uses startup-time model loading to avoid per-request cold starts.
- Applies strict request schema validation with Pydantic.
- Enforces API key auth middleware for all non-health routes.
- Adds deterministic response format for leaderboard evaluations.
- Includes confidence + score breakdown for explainability.
- Can be horizontally scaled behind a load balancer.
- For best accuracy, plug in a dedicated anti-spoof Hugging Face model via `MODEL_ID`.
