# mutimodel-validation

A comprehensive validation system for lost and found applications that performs multiple validation checks on images, text descriptions, and audio recordings to ensure they meet quality standards.

## Features

### Image Validation
- **File Validation**: Checks image format and size (supports JPEG, PNG, WebP up to 10MB)
- **Blur Detection**: Uses Laplacian variance to detect and filter blurry images
- **Object Detection**: Leverages YOLOv8 to identify objects in images with confidence filtering
- **Privacy Protection**: Automatically detects and blurs faces in images
### Image Validation Results

```json
{
  "image_path": "path/to/image.jpg",
  "timestamp": "2023-10-27 10:00:00",
  "sharpness": {
    "valid": true/false,
    "score": 235.45,
    "threshold": 100.0,
    "feedback": "Image is sharp"
  },
  "objects": {
    "valid": true/false,
    "detections": [
      {
        "class": "backpack",
        "confidence": 0.92,
        "bbox": [x1, y1, x2, y2]
      }
    ],
    "feedback": "Detected 3 objects"
  },
  "privacy": {
    "faces_detected": 2,
    "privacy_protected": true/false,
    "processed_image": "path/to/blurred_image.jpg",
    "feedback": "All faces blurred successfully"
  },
  "overall_score": 0.85,
  "valid": true/false
}
```

### Text Validation Results

```json
{
  "text": "I lost my blue phone in the library",
  "timestamp": "2023-10-27 10:00:00",
  "completeness": {
    "valid": true/false,
    "score": 0.8,
    "entities": {"item_type": ["phone"], "color": ["blue"], "location": ["library"]},
    "missing_info": [],
    "feedback": "Description contains all required elements"
  },
  "coherence": {
    "valid": true/false,
    "score": 0.75,
    "feedback": "Description is semantically coherent"
  },
  "entities": {
    "entities": [
      {
        "text": "library",
        "label": "LOC",
        "start": 24,
        "end": 31
      }
    ],
    "item_mentions": ["phone"],
    "color_mentions": ["blue"],
    "location_mentions": ["library"]
  },
  "overall_score": 0.78,
  "valid": true/false
}
```

### Audio Validation Results

```json
{
  "audio_path": "path/to/audio.mp3",
  "timestamp": "2023-10-27 10:00:00",
  "quality": {
    "valid": true/false,
    "duration": 15.2,
    "snr": 28.5,
    "duration_valid": true/false,
    "quality_valid": true/false,
    "feedback": "Audio quality assessment passed"
  },
  "transcription": {
    "valid": true/false,
    "transcription": "I lost my keys in the cafeteria",
    "confidence": 0.91,
    "language": "en",
    "feedback": "Speech recognition successful"
  },
  "overall_score": 0.88,
  "valid": true/false
}
```

### Audio Validation
- **File Validation**: Checks audio format and size (supports MP3, WAV, M4A, OGG up to 20MB)
- **Audio Quality Assessment**: Analyzes signal-to-noise ratio, duration, and clarity
- **Speech-to-Text Transcription**: Uses OpenAI Whisper for high-accuracy speech recognition
- **Transcription Confidence Scoring**: Evaluates reliability of transcription results
- **Recommendations**: Provides specific suggestions for improving audio quality

## Requirements

### For Image Validation
- Python 3.8+
- OpenCV (`opencv-python`)
- NumPy
- Ultralytics (YOLOv8)

### For Text Validation
- spaCy (with language models)
- transformers
- sentence-transformers
- torch
- langdetect (optional, for auto language)

### For Audio Validation
- librosa
- soundfile
- transformers (with Whisper models)
- torch
- numpy

## Installation

```bash
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_md
# Optional fallback multi-language model
# python -m spacy download xx_ent_wiki_sm
```

## Usage

### Image Validation

```python
from src.image.validator import ImageValidator

# Initialize with default parameters
validator = ImageValidator()

# Validate an image
result = validator.validate_image('path/to/image.jpg')

# Check overall validity
if result['valid']:
    print("Image passed all validation checks")
else:
    print(f"Image failed validation: {result['sharpness']['feedback']}. {result['objects']['feedback']}")
```

### Text Validation

```python
from src.text.validator import TextValidator

# Initialize with default parameters
validator = TextValidator()

# Validate a text description
result = validator.validate_text('I lost my blue phone in the library', 'en')

# Check overall validity
if result['valid']:
    print("Description passed all validation checks")
else:
    print(f"Description failed validation: {result['completeness']['feedback']}. {result['coherence']['feedback']}")
```

### Audio Validation

```python
from src.voice.validator import VoiceValidator

# Initialize with default parameters
validator = VoiceValidator()

# Validate an audio recording
result = validator.validate_voice('path/to/audio.mp3')

# Check overall validity
if result['valid']:
    print("Audio passed all validation checks")
    print(f"Transcription: {result['transcription']['transcription']}")
else:
    print(f"Audio failed validation: {result['quality']['feedback']}. {result['transcription']['feedback']}")
```

### Custom Configuration

#### Image Validator
```python
from src.image.validator import ImageValidator

# Initialize with custom parameters
image_validator = ImageValidator(
    blur_threshold=150.0,  # Higher threshold for blur detection
    object_confidence=0.75,  # Lower confidence threshold for object detection
    yolo_model_path='yolov8m.pt'  # Use medium-sized YOLOv8 model
)
```

#### Text Validator
```python
from src.text.validator import TextValidator

# Initialize with custom parameters
text_validator = TextValidator(
    completeness_threshold=0.6,  # Lower threshold for completeness
    coherence_threshold=0.5,  # Lower threshold for coherence
    bert_model_name='bert-base-multilingual-cased',  # Specify BERT model
    sentence_transformer_model='paraphrase-multilingual-mpnet-base-v2'  # Specify sentence transformer model
)
```

#### Audio Validator
```python
from src.voice.validator import VoiceValidator

# Initialize with custom parameters
voice_validator = VoiceValidator(
    whisper_model_size='small',  # Model size: 'tiny', 'base', 'small', 'medium', 'large'
    snr_threshold=15.0,  # Lower threshold for signal-to-noise ratio
    min_duration=3.0,  # Shorter minimum duration in seconds
    max_duration=180.0  # Longer maximum duration in seconds
)
```

### Demo Scripts

#### Image Validation Demo

```bash
python image_demo.py --image path/to/image.jpg --output processed_image.jpg
```

Options:
- `--image`: Path to the input image (required)
- `--output`: Path to save the processed image with blurred faces (optional)
- `--blur_threshold`: Custom threshold for blur detection (default: 100.0)
- `--confidence`: Custom confidence threshold for object detection (default: 0.85)

#### Text Validation Demo

```bash
python text_demo.py --text "I lost my blue phone in the library" --language en --output results.json
```

Options:
- `--text`: Text description to validate
- `--file`: Path to text file containing description (alternative to --text)
- `--language`: Language code (en, si, ta) (default: en)
- `--output`: Path to save validation results (optional)
- `--completeness`: Completeness threshold (default: 0.7)
- `--coherence`: Coherence threshold (default: 0.6)

#### Audio Validation Demo

```bash
python audio_demo.py --audio path/to/audio.mp3 --output results.json
```

## Deployment

To deploy the entire multimodal validation system using Docker Compose, follow these steps:

1.  **Prerequisites**:
    *   Docker Desktop (or Docker Engine and Docker Compose) installed on your system.
    *   Ensure ports 80, 443, 3000, 8000, 8001, 9090, 5432, 6379 are free or adjust `docker-compose.yml`.

2.  **Environment Configuration**:
    *   Create a `.env` file in the root directory of the project based on `.env.example`.
    *   Set your `API_KEY` in the `.env` file. This key will be used for authenticating API requests.

    ```bash
    cp .env.example .env
    # Edit .env and set API_KEY
    ```

3.  **Build and Run with Docker Compose**:
    *   Navigate to the root directory of the project in your terminal.
    *   Build and start all services defined in `docker-compose.yml`:

    ```bash
    docker compose build
    docker compose up -d
    ```

4.  **Verify Services**:
    *   **FastAPI Application**: Access the API documentation at `http://localhost:8000/docs`.
    *   **Frontend Chatbot**: Access the UI at `http://localhost:3001`.
    *   **Grafana Dashboard**: Access Grafana at `http://localhost:3000` (default login: admin/admin).
    *   **Prometheus**: Access Prometheus at `http://localhost:9090`.

5.  **Stop Services**:
    *   To stop all running services, use:

    ```bash
    docker compose down
    ```

## Response Format

### Image Validation Results

```json
{
  "image_path": "path/to/image.jpg",
  "timestamp": "2023-10-27 10:00:00",
  "sharpness": {
    "valid": true/false,
    "score": 235.45,
    "threshold": 100.0,
    "feedback": "Image is sharp"
  },
  "objects": {
    "valid": true/false,
    "detections": [
      {
        "class": "backpack",
        "confidence": 0.92,
        "bbox": [x1, y1, x2, y2]
      }
    ],
    "feedback": "Detected 3 objects"
  },
  "privacy": {
    "faces_detected": 2,
    "privacy_protected": true/false,
    "processed_image": "path/to/blurred_image.jpg",
    "feedback": "All faces blurred successfully"
  },
  "overall_score": 0.85,
  "valid": true/false
}
```

### Text Validation Results

```json
{
  "text": "I lost my blue phone in the library",
  "timestamp": "2023-10-27 10:00:00",
  "completeness": {
    "valid": true/false,
    "score": 0.8,
    "entities": {"item_type": ["phone"], "color": ["blue"], "location": ["library"]},
    "missing_info": [],
    "feedback": "Description contains all required elements"
  },
  "coherence": {
    "valid": true/false,
    "score": 0.75,
    "feedback": "Description is semantically coherent"
  },
  "entities": {
    "entities": [
      {
        "text": "library",
        "label": "LOC",
        "start": 24,
        "end": 31
      }
    ],
    "item_mentions": ["phone"],
    "color_mentions": ["blue"],
    "location_mentions": ["library"]
  },
  "overall_score": 0.78,
  "valid": true/false
}
```

### Audio Validation Results

```json
{
  "audio_path": "path/to/audio.mp3",
  "timestamp": "2023-10-27 10:00:00",
  "quality": {
    "valid": true/false,
    "duration": 15.2,
    "snr": 28.5,
    "duration_valid": true/false,
    "quality_valid": true/false,
    "feedback": "Audio quality assessment passed"
  },
  "transcription": {
    "valid": true/false,
    "transcription": "I lost my keys in the cafeteria",
    "confidence": 0.91,
    "language": "en",
    "feedback": "Speech recognition successful"
  },
  "overall_score": 0.88,
  "valid": true/false
}
```

## Performance

- Processes single images in under 1 second (depending on hardware)
- Memory-efficient processing suitable for concurrent requests
- Handles edge cases like very dark/bright images and unusual aspect ratios

## License

MIT
