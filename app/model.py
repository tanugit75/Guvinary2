from dataclasses import dataclass

import numpy as np
import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

from app.config import get_settings


@dataclass
class PredictionResult:
    classification: str
    confidence: float
    scores: dict[str, float]


class VoiceClassifier:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.model_id
        self.feature_extractor = AutoFeatureExtractor.from_pretrained(
            settings.model_id,
            revision=settings.model_revision,
        )
        self.model = AutoModelForAudioClassification.from_pretrained(
            settings.model_id,
            revision=settings.model_revision,
        )
        self.model.eval()

    @torch.inference_mode()
    def predict(self, waveform: np.ndarray, sampling_rate: int) -> PredictionResult:
        inputs = self.feature_extractor(
            waveform,
            sampling_rate=sampling_rate,
            return_tensors="pt",
            padding=True,
        )

        logits = self.model(**inputs).logits
        probabilities = torch.nn.functional.softmax(logits, dim=-1).squeeze(0)

        labels = self.model.config.id2label
        normalized = self._normalize_scores(labels, probabilities)

        if normalized["Human"] >= normalized["AI-generated"]:
            classification = "Human"
            confidence = normalized["Human"]
        else:
            classification = "AI-generated"
            confidence = normalized["AI-generated"]

        return PredictionResult(
            classification=classification,
            confidence=float(round(confidence, 4)),
            scores={k: float(round(v, 4)) for k, v in normalized.items()},
        )

    @staticmethod
    def _normalize_scores(id2label: dict[int, str], probs: torch.Tensor) -> dict[str, float]:
        ai_keys = {"ai", "fake", "synthetic", "spoof", "generated", "tts"}
        human_keys = {"human", "real", "bonafide", "bona fide", "genuine"}

        ai_prob = 0.0
        human_prob = 0.0

        for idx, prob in enumerate(probs.tolist()):
            label = str(id2label.get(idx, f"class_{idx}")).lower()
            if any(k in label for k in ai_keys):
                ai_prob += prob
            elif any(k in label for k in human_keys):
                human_prob += prob

        if ai_prob == 0.0 and human_prob == 0.0:
            top_idx = int(torch.argmax(probs).item())
            top_label = str(id2label.get(top_idx, "")).lower()
            if top_label and any(k in top_label for k in human_keys):
                human_prob = float(probs[top_idx].item())
                ai_prob = 1.0 - human_prob
            else:
                ai_prob = float(probs[top_idx].item())
                human_prob = 1.0 - ai_prob

        total = ai_prob + human_prob
        if total <= 0:
            return {"AI-generated": 0.5, "Human": 0.5}

        return {"AI-generated": ai_prob / total, "Human": human_prob / total}
