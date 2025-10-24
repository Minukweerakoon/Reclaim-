# Multimode Input Validation & Quality Filtering Module

A comprehensive validation system for lost and found applications that performs multiple validation checks on images, text descriptions, and audio recordings to ensure they meet quality standards.

## Features

### Image Validation
- **File Validation**: Checks image format and size (supports JPEG, PNG, WebP up to 10MB)
- **Blur Detection**: Uses Laplacian variance to detect and filter blurry images
- **Object Detection**: Leverages YOLOv8 to identify objects in images with confidence filtering
- **Privacy Protection**: Automatically detects and blurs faces in images
- **Structured Results**: Returns detailed JSON results with validity flags, scores, and feedback

### Text Validation
- **Completeness Analysis**: Checks for essential elements (item type, color, location)
- **Semantic Coherence**: Validates text coherence using BERT embeddings
- **Entity Extraction**: Uses spaCy NER to identify named entities in descriptions
- **Feedback Generation**: Provides constructive feedback for incomplete descriptions
- **Multilingual Support**: Works with English, Sinhala, and Tamil languages

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
from image_validator import ImageValidator

# Initialize with default parameters
validator = ImageValidator()

# Validate an image
result = validator.validate_image('path/to/image.jpg')

# Check overall validity
if result['valid']:
    print("Image passed all validation checks")
else:
    print(f"Image failed validation: {result['message']}")
```

### Text Validation

```python
from text_validator import TextValidator

# Initialize with default parameters
validator = TextValidator()

# Validate a text description
result = validator.validate_text('I lost my blue phone in the library', 'en')

# Check overall validity
if result['valid']:
    print("Description passed all validation checks")
else:
    print(f"Description failed validation: {result['message']}")
```

### Audio Validation

```python
from audio_validator import AudioValidator

# Initialize with default parameters
validator = AudioValidator()

# Validate an audio recording
result = validator.validate_audio('path/to/audio.mp3')

# Check overall validity
if result['valid']:
    print("Audio passed all validation checks")
    print(f"Transcription: {result['transcription']['text']}")
else:
    print(f"Audio failed validation: {result['message']}")
    if result['recommendations']:
        print("Recommendations:")
        for rec in result['recommendations']:
            print(f"- {rec}")
```

### Custom Configuration

#### Image Validator
```python
# Initialize with custom parameters
image_validator = ImageValidator(
    blur_threshold=150.0,  # Higher threshold for blur detection
    object_confidence=0.75,  # Lower confidence threshold for object detection
    yolo_model_path='yolov8m.pt'  # Use medium-sized YOLOv8 model
)
```

#### Text Validator
```python
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
# Initialize with custom parameters
audio_validator = AudioValidator(
    whisper_model_size='small',  # Model size: 'tiny', 'base', 'small', 'medium', 'large'
    snr_threshold=15.0,  # Lower threshold for signal-to-noise ratio
    min_duration=3.0,  # Shorter minimum duration in seconds
    max_duration=180.0  # Longer maximum duration in seconds
)
```

### Demo Scripts

#### Image Validation Demo

```bash
python demo.py --image path/to/image.jpg --output processed_image.jpg
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

#### CLIP-based Image-Text Alignment Validation

```bash
python clip_demo.py --image path/to/image.jpg --text "a description of the image" --output results.json
```
```

Options:
- `--audio`: Path to the audio file (required)
- `--output`: Path to save validation results (optional)

### API Server

```bash
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Access docs at http://localhost:8000/docs (use header `X-API-Key: test-api-key`).

### Frontend Chatbot UI

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_API_KEY=test-api-key" >> .env.local
npm run dev
```

Open http://localhost:5173 to interact with the chatbot.
- `--model`: Whisper model size (tiny, base, small, medium, large) (default: small)
- `--snr_threshold`: Signal-to-noise ratio threshold (default: 20.0)
- `--min_duration`: Minimum audio duration in seconds (default: 5.0)
- `--max_duration`: Maximum audio duration in seconds (default: 120.0)

## Response Format

### Image Validation Results

```json
{
  "valid": true/false,  // Overall validity of the image
  "file_validation": {
    "valid": true/false,
    "format": ".jpg",
    "size": 1234567,
    "message": "File validation passed"
  },
  "blur_detection": {
    "valid": true/false,
    "variance": 235.45,
    "threshold": 100.0,
    "message": "Image is sharp"
  },
  "object_detection": {
    "valid": true/false,
    "objects": [
      {
        "class": "backpack",
        "confidence": 0.92,
        "bbox": [x1, y1, x2, y2]
      }
    ],
    "message": "Detected 3 objects"
  },
  "privacy_protection": {
    "faces_detected": 2,
    "faces_blurred": 2,
    "message": "All faces blurred successfully"
  },
  "processing_time": 1.23,  // Processing time in seconds
  "message": "Image passed all validation checks"
}
```

### Text Validation Results

```json
{
  "valid": true/false,  // Overall validity of the description
  "completeness": {
    "valid": true/false,
    "score": 0.8,
    "threshold": 0.7,
    "item_type": {"found": true, "value": "phone"},
    "color": {"found": true, "value": "blue"},
    "location": {"found": true, "value": "library"},
    "message": "Description contains all required elements"
  },
  "coherence": {
    "valid": true/false,
    "score": 0.75,
    "threshold": 0.6,
    "message": "Description is semantically coherent"
  },
  "entities": {
    "valid": true/false,
    "extracted": [
      {
        "text": "library",
        "label": "LOC",
        "start": 24,
        "end": 31
      }
    ],
    "message": "Extracted 1 entities from description"
  },
  "feedback": {
    "suggestions": [],
    "missing_elements": [],
    "message": "Your description is complete and coherent"
  },
  "processing_time": 0.45,  // Processing time in seconds
  "message": "Description passed all validation checks"
}
```

## Performance

- Processes single images in under 1 second (depending on hardware)
- Memory-efficient processing suitable for concurrent requests
- Handles edge cases like very dark/bright images and unusual aspect ratios

## License

MIT
