import os
import time
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Tuple, Union, Optional
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VoiceValidator')

class VoiceValidator:
    """A comprehensive audio validation system for speech recognition and quality assessment.
    
    This class provides methods to validate audio based on various criteria:
    - File format and size validation
    - Audio quality assessment (SNR, duration, clarity)
    - Speech-to-text transcription using OpenAI Whisper
    - Transcription confidence scoring
    
    The validation pipeline returns structured results in JSON format.
    """
    
    # Supported audio formats
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.ogg']
    
    # Maximum file size in bytes (5MB per specification)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Audio duration constraints (in seconds)
    MIN_DURATION = 5
    MAX_DURATION = 120  # 2 minutes
    
    # Signal-to-noise ratio threshold (in dB)
    MIN_SNR = 20.0
    
    def __init__(self, 
                 whisper_model_size: str = 'small',
                 snr_threshold: float = 20.0,
                 min_duration: float = 5.0,
                 max_duration: float = 120.0,
                 enable_logging: bool = True):
        """Initialize the AudioValidator with configurable parameters.
        
        Args:
            whisper_model_size: Size of the Whisper model to use ('tiny', 'base', 'small', 'medium', 'large')
            snr_threshold: Minimum signal-to-noise ratio in dB (default: 20.0)
            min_duration: Minimum audio duration in seconds (default: 5.0)
            max_duration: Maximum audio duration in seconds (default: 120.0)
            enable_logging: Whether to enable logging (default: True)
        """
        self.whisper_model_size = whisper_model_size
        self.snr_threshold = snr_threshold
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.enable_logging = enable_logging
        
        # Initialize Whisper model
        try:
            model_name = f"openai/whisper-{whisper_model_size}"
            self.processor = WhisperProcessor.from_pretrained(model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
            
            # Move model to GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(self.device)
            
            if self.enable_logging:
                logger.info(f"Whisper model '{model_name}' loaded successfully on {self.device}")
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Failed to load Whisper model: {str(e)}")
            raise
    
    def validate_voice(self, audio_path: str) -> Dict:
        """Main validation pipeline that processes an audio file and returns structured results.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing validation results with the following structure:
            {
                "audio_path": str,
                "timestamp": str,
                "quality": dict,
                "transcription": dict,
                "valid": bool,
                "overall_score": float
            }
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            "audio_path": audio_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "quality": {},
            "transcription": {},
            "valid": False,
            "overall_score": 0.0
        }
        
        try:
            # Step 1: Validate file format and size
            file_validation = self.validate_file(audio_path)
            if not file_validation["valid"]:
                result["quality"] = {"valid": False, "duration": 0.0, "snr": 0.0, "duration_valid": False, "quality_valid": False, "feedback": file_validation["message"]}
                result["transcription"] = {"valid": False, "transcription": "", "confidence": 0.0, "language": "", "feedback": file_validation["message"]}
                return result
            
            # Step 2: Perform audio quality assessment
            quality_result = self.assess_audio_quality(audio_path)
            result["quality"] = quality_result
            
            # Step 3: Perform speech-to-text transcription if audio quality is acceptable
            if quality_result["valid"]:
                transcription_result = self.transcribe_audio(audio_path)
                result["transcription"] = transcription_result
            else:
                # Skip transcription if audio quality is poor
                result["transcription"] = {
                    "valid": False,
                    "transcription": "",
                    "confidence": 0.0,
                    "language": "",
                    "feedback": "Transcription skipped due to poor audio quality: " + quality_result["feedback"]
                }
            
            # Calculate overall score
            quality_score = 1.0 if quality_result["valid"] else 0.0
            transcription_score = transcription_result["confidence"] if transcription_result["valid"] else 0.0
            
            overall_score = (0.6 * quality_score) + (0.4 * transcription_score) # Example weights
            result["overall_score"] = round(overall_score, 2)
            
            # Determine overall validity
            result["valid"] = overall_score >= 0.7 # Example threshold
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during voice validation: {str(e)}")
            # Ensure all sub-results are marked as invalid on error
            result["quality"] = {"valid": False, "duration": 0.0, "snr": 0.0, "duration_valid": False, "quality_valid": False, "feedback": f"Error: {str(e)}"}
            result["transcription"] = {"valid": False, "transcription": "", "confidence": 0.0, "language": "", "feedback": f"Error: {str(e)}"}
            result["valid"] = False
        
        # Calculate total processing time
        result["processing_time"] = time.time() - start_time
        
        return result
    
    def validate_file(self, audio_path: str) -> Dict:
        """Validate audio file existence, format, and file size."""
        result = {
            "valid": False,
            "format": "",
            "size": 0,
            "message": ""
        }

        try:
            if not os.path.exists(audio_path):
                result["message"] = "File does not exist"
                return result

            _, ext = os.path.splitext(audio_path.lower())
            result["format"] = ext
            if ext not in self.SUPPORTED_FORMATS:
                result["message"] = f"Unsupported audio format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                return result

            file_size = os.path.getsize(audio_path)
            result["size"] = file_size
            if file_size > self.MAX_FILE_SIZE:
                result["message"] = f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
                return result

            if file_size == 0:
                result["message"] = "File is empty"
                return result

            result["valid"] = True
            result["message"] = "File validation passed"
        except Exception as exc:
            if self.enable_logging:
                logger.error(f"Error during file validation: {str(exc)}")
            result["message"] = f"Error during file validation: {str(exc)}"

        return result
    
    
    def assess_audio_quality(self, audio_path: str) -> Dict:
        """Assess audio quality based on duration, SNR, and clarity.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing audio quality assessment results
        """
        result = {
            "valid": False,
            "duration": 0.0,
            "snr": 0.0,
            "duration_valid": False,
            "quality_valid": False,
            "feedback": ""
        }
        
        try:
            # Load audio
            try:
                audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            except Exception as e:
                result["feedback"] = f"Failed to load audio for quality assessment: {str(e)}"
                return result

            # Calculate duration
            duration = librosa.get_duration(y=audio, sr=sr)
            result["duration"] = duration
            
            # Check duration constraints
            if duration < self.min_duration:
                result["feedback"] = f"Audio duration ({duration:.2f}s) is below minimum required ({self.min_duration}s)"
                result["duration_valid"] = False
                return result
            
            if duration > self.max_duration:
                result["feedback"] = f"Audio duration ({duration:.2f}s) exceeds maximum allowed ({self.max_duration}s)"
                result["duration_valid"] = False
                return result
            
            result["duration_valid"] = True

            # Calculate signal-to-noise ratio
            # Method: Estimate noise from silent segments and calculate SNR
            # 1. Compute energy of signal
            signal_energy = np.mean(audio**2)
            
            # 2. Estimate noise from silent segments (using percentile of energy in short windows)
            frame_length = int(sr * 0.025)  # 25ms frames
            hop_length = int(sr * 0.010)    # 10ms hop
            
            # Compute energy in short frames
            frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
            frame_energy = np.mean(frames**2, axis=0)
            
            # Estimate noise energy as the 10th percentile of frame energies
            noise_energy = np.percentile(frame_energy, 10)
            
            # Calculate SNR in dB
            if noise_energy > 0:
                snr = 10 * np.log10(signal_energy / noise_energy)
            else:
                snr = 100.0  # Very high SNR if no noise detected
            
            result["snr"] = snr
            
            # Check SNR threshold
            if snr < self.snr_threshold:
                result["feedback"] = f"Signal-to-noise ratio ({snr:.2f}dB) is below minimum threshold ({self.snr_threshold}dB)"
                result["quality_valid"] = False
                return result
            
            # All checks passed
            result["valid"] = True
            result["quality_valid"] = True
            result["feedback"] = "Audio quality assessment passed"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during audio quality assessment: {str(e)}")
            result["feedback"] = f"Error during audio quality assessment: {str(e)}"
        
        return result
    
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Transcribe audio using Whisper model and calculate confidence score.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing transcription results
        """
        result = {
            "valid": False,
            "transcription": "",
            "confidence": 0.0,
            "language": "",
            "feedback": ""
        }
        
        try:
            # Load audio
            try:
                audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            except Exception as e:
                result["feedback"] = f"Failed to load audio for transcription: {str(e)}"
                return result

            # Prepare input features
            input_features = self.processor(audio, sampling_rate=sr, return_tensors="pt").input_features
            input_features = input_features.to(self.device)
            
            # Generate token ids and scores (if supported)
            with torch.no_grad():
                try:
                    gen_out = self.model.generate(
                        input_features,
                        return_dict_in_generate=True,
                        output_scores=True
                    )
                    predicted_ids = gen_out.sequences
                    # Aggregate scores across steps if available
                    if hasattr(gen_out, 'scores') and gen_out.scores:
                        step_probs = [torch.nn.functional.softmax(s, dim=-1) for s in gen_out.scores]
                    else:
                        step_probs = []
                except Exception:
                    predicted_ids = self.model.generate(input_features)
                    step_probs = []
            
            # Decode token ids to text
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            result["transcription"] = transcription
            
            # Confidence score estimation
            confidence = 0.0
            try:
                if step_probs:
                    # Use step-wise probabilities for selected tokens (greedy)
                    token_ids = predicted_ids[0]
                    probs = []
                    for i in range(min(len(step_probs), token_ids.shape[0])):
                        tok_id = token_ids[i]
                        probs.append(step_probs[i][0, tok_id].item())
                    if probs:
                        confidence = sum(probs) / len(probs)
                else:
                    # Fallback: run model forward pass to get logits
                    with torch.no_grad():
                        outputs = self.model(input_features, decoder_input_ids=predicted_ids)
                        logits = outputs.logits
                        p = torch.nn.functional.softmax(logits, dim=-1)
                        token_probs = []
                        for i, token_id in enumerate(predicted_ids[0]):
                            if i < logits.shape[1]:
                                token_probs.append(p[0, i, token_id].item())
                        if token_probs:
                            confidence = sum(token_probs) / len(token_probs)
            except Exception:
                confidence = 0.0
            
            result["confidence"] = confidence

            # Detect language (Whisper can do this)
            # This is a simplified approach, a more robust solution would involve the full pipeline
            # For now, we'll assume English if not explicitly detected or if the model is not multilingual
            detected_language = "en" # Default to English
            if hasattr(self.processor, "tokenizer") and hasattr(self.processor.tokenizer, "language"):
                detected_language = self.processor.tokenizer.language
            result["language"] = detected_language
            
            # Check if transcription is empty or too short
            if not transcription or len(transcription.split()) < 3:
                result["feedback"] = "Transcription is empty or too short"
                return result
            
            # Check confidence threshold (arbitrary threshold of 0.5)
            if confidence < 0.5:
                result["feedback"] = f"Transcription confidence ({confidence:.2f}) is too low for reliable results"
                return result
            
            # All checks passed
            result["valid"] = True
            result["feedback"] = "Speech recognition successful"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during speech recognition: {str(e)}")
            result["feedback"] = f"Error during speech recognition: {str(e)}"
        
        return result
