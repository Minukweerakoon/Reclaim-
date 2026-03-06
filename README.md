# Multimodal Validation System

Research-grade multimodal validation for lost-and-found reports using image, text, and voice inputs.

## Overview

This system validates reports across three modalities and enforces cross-modal consistency:

- Computer vision: YOLOv11 (primary), YOLOv8 fallback, custom ViT classifier, CLIP alignment
- NLP: spaCy NER, semantic coherence, intent/urgency classification, optional LLM extraction
- Speech: Whisper transcription, audio quality analysis, voice-text alignment
- Cross-modal: CLIP similarity, adaptive confidence weighting, context consistency checks
- Intelligence: knowledge graph, spatial-temporal plausibility, active learning loop

## Architecture (high level)

```
React UI
  -> FastAPI API
     -> Image / Text / Voice validators
     -> Cross-modal consistency engine
     -> Intelligence layer (LLM, knowledge graph, plausibility)
     -> Storage + monitoring
```

## Quick Start

Prerequisites:
- Python 3.10+
- Node.js 18+ (frontend)
- Docker (optional)

Backend setup:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_models.py
python -m spacy download en_core_web_md
```

Environment configuration:
```bash
cp .env.example .env
# Set API_KEY and any optional provider keys (GEMINI_API_KEY, etc)
```

Run the API:
```bash
python app.py
```

Run the UI:
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints (core)

- POST `/validate/text`
- POST `/validate/image`
- POST `/validate/voice`
- POST `/validate/complete`
- POST `/api/validate/context` (spatial-temporal plausibility)
- POST `/api/xai/attention` (attention heatmap)
- POST `/api/xai/explain-enhanced` (enhanced discrepancy explanation)
- POST `/api/chat/message` (conversational guidance)
- POST `/api/feedback/submit` (active learning feedback)
- GET `/api/feedback/stats` (active learning stats)

Authentication:
- Use `X-API-Key` with the value from `API_KEY` in your environment.

Confidence scale:
- `overall_confidence` is normalized to 0.0-1.0 across modalities.

## Usage Example (Python)

```python
from src.image.validator import ImageValidator
from src.text.validator import TextValidator
from src.voice.validator import VoiceValidator
from src.cross_modal.consistency_engine import ConsistencyEngine

image_val = ImageValidator()
text_val = TextValidator()
voice_val = VoiceValidator()

image_result = image_val.validate_image("photo.jpg")
text_result = text_val.validate_text("Lost my blue laptop in the library", language="en")
voice_result = voice_val.validate_voice("recording.mp3")

engine = ConsistencyEngine()
confidence = engine.calculate_overall_confidence(
    image_result=image_result,
    text_result=text_result,
    voice_result=voice_result,
    cross_modal_results={}
)
print(confidence["overall_confidence"])
```

## Testing

```bash
pytest tests/ -v
```

Optional CLIP integration tests:
```bash
RUN_CLIP_INTEGRATION_TESTS=1 pytest tests/test_xai.py -v
```

## Reproducibility

See `docs/REPRODUCIBILITY.md` for dataset expectations, deterministic training, and evaluation steps.

## Notes on Explainability

The project provides attention heatmaps and discrepancy explanations out of the box. SHAP/LIME/Captum
dependencies are included for extending explanations, but the default runtime focuses on the CLIP
occlusion heatmap and rule-based mismatch diagnostics.

## License

MIT License. See `LICENSE`.
