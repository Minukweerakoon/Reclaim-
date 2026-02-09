# Multimodal Validation API

A production-ready FastAPI application for validating multimodal inputs including text, images, and audio recordings. This API provides comprehensive validation services with real-time feedback and detailed quality assessment.

## Features

- **RESTful API Endpoints** for different validation types (complete, image, text, voice)
- **API Key Authentication** with rate limiting
- **Asynchronous Processing** for time-intensive operations
- **WebSocket Support** for real-time validation feedback
- **Comprehensive Error Handling** with detailed messages
- **Performance Monitoring** with metrics endpoint
- **Health Checks** for load balancer integration

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

1. Clone the repository or download the source code

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create an uploads directory (if not already present):

```bash
mkdir uploads
```

4. Run the application:

```bash
python app.py
```

Or with uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication

All API endpoints (except health and metrics) require API key authentication. Include the API key in the request header:

```
X-API-Key: test-api-key
```

Note: The API key is configured via `API_KEY` in the environment. In a production
environment, you should implement a proper API key management system.

## API Endpoints

### Health Check

```
GET /health
```

Returns the health status of the API and its components.

### Metrics

```
GET /metrics
```

Returns performance metrics including request counts, success rates, and response times.

### Text Validation

```
POST /validate/text
```

Validates text input for completeness, coherence, and quality.

**Request Body:**
```json
{
  "text": "A silver watch with leather strap found near the park entrance",
  "language": "en"
}
```

### Voice/Audio Validation

```
POST /validate/voice
```

Validates audio recordings for quality, clarity, and transcribes speech content.

**Form Data:**
- `audio_file`: Audio file (MP3, WAV, M4A, OGG)

### Image Validation

```
POST /validate/image
```

Validates images for quality and optionally checks alignment with provided text.

**Form Data:**
- `image_file`: Image file (JPEG, PNG, GIF)
- `text` (optional): Text description to check against the image

### Complete Multimodal Validation

```
POST /validate/complete
```

Performs comprehensive validation across multiple modalities with cross-modal consistency checks.

**Form Data:**
- `text` (optional): Text description
- `image_file` (optional): Image file
- `audio_file` (optional): Audio file
- `language` (optional, default: "en"): Language code

### WebSocket Endpoint

```
WS /ws/validation/{client_id}
```

Provides real-time progress updates during validation processing.

## Response Format

All validation endpoints return a standardized response format:

All confidence scores are normalized to a 0.0-1.0 scale.

```json
{
  "valid": true,
  "confidence": 0.92,
  "confidence_interval": [0.89, 0.95],
  "routing": "high",
  "modal_scores": {
    "text": { ... },
    "image": { ... },
    "audio": { ... },
    "cross_modal": { ... }
  },
  "consistency": { ... },
  "feedback": {
    "suggestions": ["Consider adding more details about the location"],
    "missing_elements": [],
    "message": "Description is clear and concise"
  },
  "processing_time": 1.25,
  "message": "Multimodal validation passed with confidence level: high",
  "request_id": "20230615123045123456"
}
```

## Error Handling

The API provides detailed error responses with suggestions for resolution:

```json
{
  "detail": "Unsupported file type: audio/aac. Supported types: ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a']",
  "status_code": 400,
  "timestamp": "2023-06-15T12:30:45.123456",
  "path": "/validate/voice",
  "suggestion": "Check the file format and try again with a supported format"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. By default, clients are limited to 100 requests per minute. When the rate limit is exceeded, the API returns a 429 Too Many Requests response.

## Performance Considerations

- The API is designed to handle 100+ concurrent requests
- Response times are typically under 3 seconds for complete validation
- File uploads are limited to 20MB
- Temporary files are automatically cleaned up after processing

## WebSocket Usage Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/validation/client123');

// Handle connection open
ws.onopen = () => {
  console.log('Connected to validation service');
  
  // Send validation request
  ws.send(JSON.stringify({
    type: 'validate',
    text: 'A silver watch with leather strap found near the park entrance',
    language: 'en'
  }));
};

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.task_id) {
    console.log(`Task ID: ${data.task_id}`);
    
    // Request status updates
    setInterval(() => {
      ws.send(JSON.stringify({
        type: 'status',
        task_id: data.task_id
        
      }));
    }, 1000);
  }
  
  if (data.progress) {
    console.log(`Progress: ${data.progress}% - ${data.message}`);
    
    // Handle completion
    if (data.progress === 100 && data.result) {
      console.log('Validation complete:', data.result);
    }
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle disconnection
ws.onclose = () => {
  console.log('Disconnected from validation service');
};
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
