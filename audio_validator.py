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
logger = logging.getLogger('AudioValidator')

class AudioValidator:
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
    
    # Maximum file size in bytes (20MB)
    MAX_FILE_SIZE = 20 * 1024 * 1024
    
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
    
    def validate_audio(self, audio_path: str) -> Dict:
        """Main validation pipeline that processes an audio file and returns structured results.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing validation results with the following structure:
            {
                "valid": bool,  # Overall validity of the audio
                "file_validation": {  # File validation results
                    "valid": bool,
                    "format": str,
                    "size": int,
                    "message": str
                },
                "audio_quality": {  # Audio quality assessment results
                    "valid": bool,
                    "duration": float,
                    "snr": float,
                    "clarity": float,
                    "threshold": float,
                    "message": str
                },
                "transcription": {  # Speech-to-text results
                    "valid": bool,
                    "text": str,
                    "confidence": float,
                    "message": str
                },
                "processing_time": float,  # Total processing time in seconds
                "message": str,  # Overall validation message
                "recommendations": List[str]  # Recommendations for improvement
            }
        """
        start_time = time.time()
        
        # Initialize result structure
        result = {
            "valid": False,
            "file_validation": {},
            "audio_quality": {},
            "transcription": {},
            "processing_time": 0,
            "message": "",
            "recommendations": []
        }
        
        try:
            # Step 1: Validate file format and size
            file_validation = self.validate_file(audio_path)
            result["file_validation"] = file_validation
            
            if not file_validation["valid"]:
                result["message"] = "File validation failed: " + file_validation["message"]
                result["processing_time"] = time.time() - start_time
                return result
            
            # Step 2: Load and preprocess audio
            try:
                audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            except Exception as e:
                if self.enable_logging:
                    logger.error(f"Error loading audio file: {str(e)}")
                result["message"] = f"Failed to load audio: The audio file may be corrupted. Error: {str(e)}"
                result["processing_time"] = time.time() - start_time
                return result
            
            # Step 3: Perform audio quality assessment
            audio_quality = self.assess_audio_quality(audio, sr)
            result["audio_quality"] = audio_quality
            
            # Step 4: Perform speech-to-text transcription if audio quality is acceptable
            if audio_quality["valid"]:
                transcription = self.transcribe_audio(audio_path, audio, sr)
                result["transcription"] = transcription
            else:
                # Skip transcription if audio quality is poor
                result["transcription"] = {
                    "valid": False,
                    "text": "",
                    "confidence": 0.0,
                    "message": "Transcription skipped due to poor audio quality"
                }
                
                # Add recommendations based on audio quality issues
                if audio_quality["duration"] < self.min_duration:
                    result["recommendations"].append(f"Audio is too short. Please record at least {self.min_duration} seconds.")
                elif audio_quality["duration"] > self.max_duration:
                    result["recommendations"].append(f"Audio is too long. Please limit recording to {self.max_duration} seconds.")
                
                if audio_quality["snr"] < self.snr_threshold:
                    result["recommendations"].append("Background noise is too high. Please record in a quieter environment.")
                
                if audio_quality["clarity"] < 0.5:  # Assuming clarity is normalized between 0 and 1
                    result["recommendations"].append("Audio clarity is poor. Please speak more clearly and closer to the microphone.")
            
            # Determine overall validity
            result["valid"] = (
                file_validation["valid"] and 
                audio_quality["valid"] and 
                result["transcription"]["valid"]
            )
            
            if result["valid"]:
                result["message"] = "Audio passed all validation checks"
            else:
                failed_checks = []
                if not file_validation["valid"]:
                    failed_checks.append("file validation")
                if not audio_quality["valid"]:
                    failed_checks.append("audio quality assessment")
                if not result["transcription"]["valid"]:
                    failed_checks.append("speech recognition")
                
                result["message"] = f"Audio failed validation: {', '.join(failed_checks)}"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during audio validation: {str(e)}")
            result["message"] = f"Error during validation: {str(e)}"
            result["recommendations"].append("An unexpected error occurred. Please try again with a different audio file.")
        
        # Calculate total processing time
        result["processing_time"] = time.time() - start_time
        
        return result
    
    def validate_file(self, audio_path: str) -> Dict:
        """Validate audio file format and size.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing file validation results
        """
        result = {
            "valid": False,
            "format": "",
            "size": 0,
            "message": ""
        }
        
        try:
            # Check if file exists
            if not os.path.exists(audio_path):
                result["message"] = "File does not exist"
                return result
            
            # Get file extension
            _, ext = os.path.splitext(audio_path.lower())
            result["format"] = ext
            
            # Check if format is supported
            if ext not in self.SUPPORTED_FORMATS:
                result["message"] = f"Unsupported audio format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                return result
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            result["size"] = file_size
            
            if file_size > self.MAX_FILE_SIZE:
                result["message"] = f"File size exceeds maximum allowed size of {self.MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
                return result
            
            # All checks passed
            result["valid"] = True
            result["message"] = "File validation passed"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during file validation: {str(e)}")
            result["message"] = f"Error during file validation: {str(e)}"
        
        return result
    
    def assess_audio_quality(self, audio: np.ndarray, sr: int) -> Dict:
        """Assess audio quality based on duration, SNR, and clarity.
        
        Args:
            audio: Audio signal as numpy array
            sr: Sample rate of the audio
            
        Returns:
            Dict containing audio quality assessment results
        """
        result = {
            "valid": False,
            "duration": 0.0,
            "snr": 0.0,
            "clarity": 0.0,
            "threshold": self.snr_threshold,
            "message": ""
        }
        
        try:
            # Calculate duration
            duration = librosa.get_duration(y=audio, sr=sr)
            result["duration"] = duration
            
            # Check duration constraints
            if duration < self.min_duration:
                result["message"] = f"Audio duration ({duration:.2f}s) is below minimum required ({self.min_duration}s)"
                return result
            
            if duration > self.max_duration:
                result["message"] = f"Audio duration ({duration:.2f}s) exceeds maximum allowed ({self.max_duration}s)"
                return result
            
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
                result["message"] = f"Signal-to-noise ratio ({snr:.2f}dB) is below minimum threshold ({self.snr_threshold}dB)"
                return result
            
            # Calculate clarity using spectral flatness
            # Spectral flatness is a measure of how tone-like a sound is (as opposed to noise-like)
            spectral_flatness = librosa.feature.spectral_flatness(y=audio)
            clarity = 1.0 - np.mean(spectral_flatness)  # Higher flatness = lower clarity
            result["clarity"] = clarity
            
            # Check clarity (arbitrary threshold of 0.5)
            if clarity < 0.5:
                result["message"] = f"Audio clarity ({clarity:.2f}) is too low for reliable transcription"
                return result
            
            # All checks passed
            result["valid"] = True
            result["message"] = "Audio quality assessment passed"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during audio quality assessment: {str(e)}")
            result["message"] = f"Error during audio quality assessment: {str(e)}"
        
        return result
    
    def transcribe_audio(self, audio_path: str, audio: np.ndarray, sr: int) -> Dict:
        """Transcribe audio using Whisper model and calculate confidence score.
        
        Args:
            audio_path: Path to the audio file
            audio: Audio signal as numpy array
            sr: Sample rate of the audio
            
        Returns:
            Dict containing transcription results
        """
        result = {
            "valid": False,
            "text": "",
            "confidence": 0.0,
            "message": ""
        }
        
        try:
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
            result["text"] = transcription
            
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
            
            # Check if transcription is empty or too short
            if not transcription or len(transcription.split()) < 3:
                result["message"] = "Transcription is empty or too short"
                return result
            
            # Check confidence threshold (arbitrary threshold of 0.5)
            if confidence < 0.5:
                result["message"] = f"Transcription confidence ({confidence:.2f}) is too low for reliable results"
                return result
            
            # All checks passed
            result["valid"] = True
            result["message"] = "Speech recognition successful"
            
        except Exception as e:
            if self.enable_logging:
                logger.error(f"Error during speech recognition: {str(e)}")
            result["message"] = f"Error during speech recognition: {str(e)}"
        
        return result
