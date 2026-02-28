import pytest
import os
from unittest.mock import MagicMock, patch
from src.voice.validator import VoiceValidator
import numpy as np
import torch
import soundfile as sf

# Mock external dependencies
@pytest.fixture
def mock_librosa():
    with patch('src.voice.validator.librosa') as mock:
        mock.load.return_value = (np.zeros(16000 * 10), 16000) # 10 seconds of silence
        mock.get_duration.return_value = 10.0
        mock.util.frame.return_value = np.zeros((10, 100)) # Dummy frames
        mock.feature.spectral_flatness.return_value = np.array([0.5])
        yield mock

@pytest.fixture
def mock_soundfile():
    with patch('src.voice.validator.sf') as mock:
        yield mock

@pytest.fixture
def mock_whisper_processor():
    with patch('src.voice.validator.WhisperProcessor.from_pretrained') as mock:
        mock_processor = MagicMock()
        mock_processor.batch_decode.return_value = ["This is a test transcription."]
        mock_processor.tokenizer.language = "en"
        mock.return_value = mock_processor
        yield mock

@pytest.fixture
def mock_whisper_model():
    with patch('src.voice.validator.WhisperForConditionalGeneration.from_pretrained') as mock:
        mock_model = MagicMock()
        mock_model.to.return_value = mock_model # Mock .to("cpu"/"cuda")
        mock_model.generate.return_value.sequences = MagicMock()
        mock_model.generate.return_value.scores = [torch.tensor([[0.1, 0.9]])] # Dummy scores
        yield mock

@pytest.fixture
def voice_validator(mock_librosa, mock_soundfile, mock_whisper_processor, mock_whisper_model):
    validator = VoiceValidator(enable_logging=False)
    return validator

# Helper to create a dummy audio file
@pytest.fixture
def dummy_audio_file(tmp_path):
    audio_path = tmp_path / "test_audio.wav"
    # Create a simple dummy WAV file
    samplerate = 16000
    duration = 10  # seconds
    frequency = 440  # Hz
    t = np.linspace(0., duration, int(samplerate * duration), endpoint=False)
    amplitude = np.iinfo(np.int16).max * 0.5
    data = amplitude * np.sin(2. * np.pi * frequency * t)
    sf.write(str(audio_path), data.astype(np.int16), samplerate)
    return str(audio_path)

@pytest.fixture
def dummy_unsupported_audio_file(tmp_path):
    file_path = tmp_path / "test_audio.mp4"
    file_path.write_text("This is a test video.")
    return str(file_path)

class TestVoiceValidator:

    def test_init(self, mock_whisper_processor, mock_whisper_model):
        validator = VoiceValidator(enable_logging=False)
        mock_whisper_processor.assert_called_once()
        mock_whisper_model.assert_called_once()

    def test_validate_file_supported_format_and_size(self, voice_validator, dummy_audio_file):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100): # Smaller than MAX_FILE_SIZE
            result = voice_validator.validate_file(dummy_audio_file)
            assert result['valid'] is True
            assert result['format'] == '.wav'
            assert result['size'] == 100
            assert "File validation passed" in result['message']

    def test_validate_file_unsupported_format(self, voice_validator, dummy_unsupported_audio_file):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100):
            result = voice_validator.validate_file(dummy_unsupported_audio_file)
            assert result['valid'] is False
            assert result['format'] == '.mp4'
            assert "Unsupported audio format" in result['message']

    def test_validate_file_exceeds_size(self, voice_validator, dummy_audio_file):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=voice_validator.MAX_FILE_SIZE + 1):
            result = voice_validator.validate_file(dummy_audio_file)
            assert result['valid'] is False
            assert "File size exceeds maximum allowed size" in result['message']

    def test_assess_audio_quality_valid(self, voice_validator, mock_librosa, dummy_audio_file):
        result = voice_validator.assess_audio_quality(dummy_audio_file)
        assert result['valid'] is True
        assert result['duration_valid'] is True
        assert result['quality_valid'] is True
        assert result['duration'] == 10.0
        assert result['snr'] > voice_validator.snr_threshold
        assert "Audio quality assessment passed" in result['feedback']

    def test_assess_audio_quality_too_short(self, voice_validator, mock_librosa, dummy_audio_file):
        mock_librosa.get_duration.return_value = 2.0 # Too short
        result = voice_validator.assess_audio_quality(dummy_audio_file)
        assert result['valid'] is False
        assert result['duration_valid'] is False
        assert "below minimum required" in result['feedback']

    def test_assess_audio_quality_low_snr(self, voice_validator, mock_librosa, dummy_audio_file):
        mock_librosa.get_duration.return_value = 10.0
        with patch('numpy.percentile', return_value=1.0): # Simulate high noise energy
            result = voice_validator.assess_audio_quality(dummy_audio_file)
            assert result['valid'] is False
            assert result['quality_valid'] is False
            assert "below minimum threshold" in result['feedback']

    def test_transcribe_audio_successful(self, voice_validator, mock_librosa, mock_whisper_processor, mock_whisper_model, dummy_audio_file):
        # Mock confidence to be high enough
        with patch('torch.nn.functional.softmax', return_value=torch.tensor([[0.1, 0.9]])) as mock_softmax:
            result = voice_validator.transcribe_audio(dummy_audio_file)
            assert result['valid'] is True
            assert result['transcription'] == "This is a test transcription."
            assert result['confidence'] > 0.5
            assert result['language'] == "en"
            assert "Speech recognition successful" in result['feedback']

    def test_transcribe_audio_low_confidence(self, voice_validator, mock_librosa, mock_whisper_processor, mock_whisper_model, dummy_audio_file):
        # Mock confidence to be low
        with patch('torch.nn.functional.softmax', return_value=torch.tensor([[0.9, 0.1]])) as mock_softmax:
            result = voice_validator.transcribe_audio(dummy_audio_file)
            assert result['valid'] is False
            assert result['confidence'] < 0.5
            assert "confidence is too low" in result['feedback']

    def test_validate_voice_overall_valid(self, voice_validator, mock_librosa, mock_whisper_processor, mock_whisper_model, dummy_audio_file):
        # Mock sub-methods to return valid results
        voice_validator.validate_file = MagicMock(return_value={'valid': True, 'format': '.wav', 'size': 100, 'message': 'File validation passed'})
        voice_validator.assess_audio_quality = MagicMock(return_value={'valid': True, 'duration': 10.0, 'snr': 25.0, 'duration_valid': True, 'quality_valid': True, 'feedback': 'Good quality'})
        voice_validator.transcribe_audio = MagicMock(return_value={'valid': True, 'transcription': 'Hello world', 'confidence': 0.9, 'language': 'en', 'feedback': 'Transcribed'})

        result = voice_validator.validate_voice(dummy_audio_file)
        assert result['valid'] is True
        assert result['overall_score'] >= 0.7
        assert result['audio_path'] == dummy_audio_file
        assert 'timestamp' in result
        assert result['quality']['valid'] is True
        assert result['transcription']['valid'] is True

    def test_validate_voice_overall_invalid_low_quality(self, voice_validator, mock_librosa, mock_whisper_processor, mock_whisper_model, dummy_audio_file):
        # Mock sub-methods to return invalid results
        voice_validator.validate_file = MagicMock(return_value={'valid': True, 'format': '.wav', 'size': 100, 'message': 'File validation passed'})
        voice_validator.assess_audio_quality = MagicMock(return_value={'valid': False, 'duration': 2.0, 'snr': 10.0, 'duration_valid': False, 'quality_valid': False, 'feedback': 'Too short'})
        voice_validator.transcribe_audio = MagicMock(return_value={'valid': False, 'transcription': '', 'confidence': 0.0, 'language': '', 'feedback': 'Skipped'})

        result = voice_validator.validate_voice(dummy_audio_file)
        assert result['valid'] is False
        assert result['overall_score'] < 0.7
        assert result['audio_path'] == dummy_audio_file
        assert 'timestamp' in result
        assert result['quality']['valid'] is False
        assert result['transcription']['valid'] is False
