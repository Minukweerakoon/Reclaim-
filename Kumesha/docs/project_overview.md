# Project Overview: Multimodal Validation System

## 1. Executive Summary
The **Multimodal Validation System** is a research-grade application designed to validate and cross-reference lost-and-found reports using three distinct modalities: **Image**, **Text**, and **Voice**. The system ensures high data integrity by enforcing cross-modal consistency (e.g., does the image match the text description?) and leverages advanced AI for object detection, semantic analysis, and speech recognition.

## 2. System Architecture

The application follows a modern decoupled architecture:

### High-Level Data Flow
1.  **User Interface (React)**: User submits a report with an image, text description, and optional voice recording.
2.  **API Layer (FastAPI)**: Routes requests to specific validators.
3.  **Validation Layer (AI Models)**:
    *   **Image Validator**: Detects objects and quality.
    *   **Text Validator**: Extracts entities and checks coherence.
    *   **Voice Validator**: Transcribes speech and assesses audio quality.
4.  **Intelligence Layer**:
    *   **Consistency Engine**: Cross-references outputs from all three validators (e.g., CLIP image-text alignment).
    *   **Knowledge Graph**: Context-aware relationships (e.g., spatial-temporal plausibility).
    *   **Active Learning**: Feedback loop for model improvement.
5.  **Storage & Monitoring**: Results are returned to the user and logged for system monitoring.

## 3. AI Capabilities & Technologies

### A. Computer Vision (Image)
*   **Primary Detector**: **YOLOv11** (Nano) for real-time, high-accuracy object detection (COCO classes).
*   **Fallback Detector**: **YOLOv8** / **ViT** (Vision Transformer) if primary fails.
*   **Zero-Shot Validation**: **CLIP** (Contrastive Language-Image Pre-training) used to validate if the image matches the user's text description when standard detectors are uncertain.
*   **Quality Checks**: Laplacian variance for blur detection; privacy preservation (face blurring) using Haar Cascades.

### B. Natural Language Processing (Text)
*   **Entity Extraction (NER)**: **spaCy** (en_core_web_md) to extract Item Type, Color, Location, and Time.
*   **Semantic Coherence**: **BERT** embeddings and **Sentence Transformers** (`paraphrase-multilingual-mpnet-base-v2`) to ensure description logic.
*   **Zero-Shot Classification**: **BART-MNLI** for categorizing items without explicit labels.
*   **Multilingual Support**: Supports English, Sinhala, and Tamil.

### C. Speech Processing (Voice)
*   **Transcription**: **OpenAI Whisper** (Small) for robust speech-to-text, even with accents.
*   **Quality Analysis**: **Librosa** for Signal-to-Noise Ratio (SNR) and duration checks.
*   **Language Detection**: Automatic language identification via Whisper.

### D. Advanced Intelligence
*   **Explainable AI (XAI)**: Provides attention heatmaps and human-readable reasoning for validation decisions.
*   **Knowledge Graph**: Validates the plausibility of lost items in specific locations (e.g., "Is it likely to find a passport in a swimming pool?").

## 4. Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, Framer Motion |
| **Backend API** | Python, FastAPI, Pydantic |
| **AI/ML Frameworks** | PyTorch, Transformers (Hugging Face), Ultralytics (YOLO) |
| **Specific Models** | YOLOv11, CLIP, BERT, Whisper, ViT |
| **Data Processing** | NumPy, Pandas, OpenCV, Pillow, Librosa |
| **Database/Graph** | Neo4j (Knowledge Graph), SQLAlchemy (Structured Data) |

## 5. Directory Structure
*   `src/api`: FastAPI route handlers.
*   `src/image`, `src/text`, `src/voice`: Domain-specific validators.
*   `src/cross_modal`: Logic for combining validator outputs (CLIP, Fusion).
*   `src/intelligence`: Knowledge graph, LLM client, and active learning logic.
*   `frontend/src/pages`: React pages (Landing, Auth, Validation, Results, Monitor).

## 6. Setup & Usage
Refer to `README.md` for detailed installation instructions.
**Key Commands:**
*   Backend: `python app.py`
*   Frontend: `npm run dev` (in `frontend/` directory)
*   Testing: `pytest tests/`
