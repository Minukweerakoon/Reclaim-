import pytest
import os
import cv2
from unittest.mock import MagicMock, patch
from src.image.validator import ImageValidator

# Mock external dependencies
@pytest.fixture
def mock_yolo():
    with patch('src.image.validator.YOLO') as mock:
        yield mock

@pytest.fixture
def mock_cv2():
    with patch('src.image.validator.cv2') as mock:
        mock.CascadeClassifier.return_value = MagicMock()
        mock.CascadeClassifier.return_value.empty.return_value = False
        yield mock

@pytest.fixture
def image_validator(mock_yolo, mock_cv2):
    # Ensure the yolo_model_path exists for the mock to not raise an error during init
    with patch('os.path.exists', return_value=True):
        validator = ImageValidator(yolo_model_path='dummy_yolov8n.pt', enable_logging=False)
    return validator

# Helper to create a dummy image file
@pytest.fixture
def dummy_image_file(tmp_path):
    img_path = tmp_path / "test_image.jpg"
    # Create a simple dummy image (e.g., a black image)
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), dummy_img)
    return str(img_path)

@pytest.fixture
def dummy_unsupported_file(tmp_path):
    file_path = tmp_path / "test_doc.txt"
    file_path.write_text("This is a test document.")
    return str(file_path)

class TestImageValidator:

    def test_init(self, mock_yolo, mock_cv2):
        with patch('os.path.exists', return_value=True):
            validator = ImageValidator(yolo_model_path='dummy_yolov8n.pt', enable_logging=False)
        mock_yolo.assert_called_once_with('dummy_yolov8n.pt')
        mock_cv2.CascadeClassifier.assert_called_once()
        assert not validator.face_cascade.empty()

    def test_validate_file_supported_format_and_size(self, image_validator, dummy_image_file):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100): # Smaller than MAX_FILE_SIZE
            result = image_validator.validate_file(dummy_image_file)
            assert result['valid'] is True
            assert result['format'] == '.jpg'
            assert result['size'] == 100
            assert "File validation passed" in result['message']

    def test_validate_file_unsupported_format(self, image_validator, dummy_unsupported_file):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100):
            result = image_validator.validate_file(dummy_unsupported_file)
            assert result['valid'] is False
            assert result['format'] == '.txt'
            assert "Unsupported image format" in result['message']

    def test_validate_file_exceeds_size(self, image_validator, dummy_image_file):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=image_validator.MAX_FILE_SIZE + 1):
            result = image_validator.validate_file(dummy_image_file)
            assert result['valid'] is False
            assert "File size exceeds maximum allowed size" in result['message']

    def test_check_sharpness_sharp_image(self, image_validator, mock_cv2, dummy_image_file):
        mock_cv2.imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.Laplacian.return_value.var.return_value = image_validator.blur_threshold + 10
        
        result = image_validator.check_sharpness(dummy_image_file)
        assert result['valid'] is True
        assert result['score'] > image_validator.blur_threshold
        assert "Image is sharp" in result['feedback']

    def test_check_sharpness_blurry_image(self, image_validator, mock_cv2, dummy_image_file):
        mock_cv2.imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.Laplacian.return_value.var.return_value = image_validator.blur_threshold - 10
        
        result = image_validator.check_sharpness(dummy_image_file)
        assert result['valid'] is False
        assert result['score'] < image_validator.blur_threshold
        assert "Image is too blurry" in result['feedback']

    def test_detect_objects_found(self, image_validator, mock_yolo, dummy_image_file):
        mock_yolo_result = MagicMock()
        mock_yolo_result.boxes = [MagicMock()]
        mock_yolo_result.boxes[0].xyxy = torch.tensor([[10, 10, 20, 20]])
        mock_yolo_result.boxes[0].conf = torch.tensor([0.9])
        mock_yolo_result.boxes[0].cls = torch.tensor([0])
        mock_yolo_result.names = {0: 'person'}
        mock_yolo.return_value.return_value = [mock_yolo_result]

        result = image_validator.detect_objects(dummy_image_file)
        assert result['valid'] is True
        assert len(result['detections']) == 1
        assert result['detections'][0]['class'] == 'person'
        assert result['detections'][0]['confidence'] == 0.9
        assert "Detected 1 objects" in result['feedback']

    def test_detect_objects_not_found(self, image_validator, mock_yolo, dummy_image_file):
        mock_yolo_result = MagicMock()
        mock_yolo_result.boxes = []
        mock_yolo.return_value.return_value = [mock_yolo_result]

        result = image_validator.detect_objects(dummy_image_file)
        assert result['valid'] is False
        assert len(result['detections']) == 0
        assert "No objects detected" in result['feedback']

    def test_detect_privacy_content_faces_detected(self, image_validator, mock_cv2, dummy_image_file, tmp_path):
        mock_cv2.imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.CascadeClassifier.return_value.detectMultiScale.return_value = [[10, 10, 20, 20]] # One face
        mock_cv2.GaussianBlur.return_value = np.zeros((20, 20, 3), dtype=np.uint8) # Mock blurred face
        
        with patch('os.makedirs'), patch('src.image.validator.ImageValidator.save_processed_image', return_value=True):
            result = image_validator.detect_privacy_content(dummy_image_file)
            assert result['faces_detected'] == 1
            assert result['privacy_protected'] is True
            assert result['processed_image'] is not None
            assert "Detected and blurred 1 faces" in result['feedback']

    def test_detect_privacy_content_no_faces(self, image_validator, mock_cv2, dummy_image_file):
        mock_cv2.imread.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_cv2.CascadeClassifier.return_value.detectMultiScale.return_value = [] # No faces
        
        result = image_validator.detect_privacy_content(dummy_image_file)
        assert result['faces_detected'] == 0
        assert result['privacy_protected'] is False
        assert result['processed_image'] is None
        assert "No faces detected" in result['feedback']

    def test_validate_image_overall_valid(self, image_validator, mock_cv2, mock_yolo, dummy_image_file):
        # Mock for validate_file
        image_validator.validate_file = MagicMock(return_value={'valid': True, 'format': '.jpg', 'size': 100, 'message': 'File validation passed'})
        # Mock for check_sharpness
        image_validator.check_sharpness = MagicMock(return_value={'valid': True, 'score': 150.0, 'threshold': 100.0, 'feedback': 'Sharp'})
        # Mock for detect_objects
        image_validator.detect_objects = MagicMock(return_value={'valid': True, 'detections': [{'class': 'person', 'confidence': 0.9, 'bbox': [10,10,20,20]}], 'feedback': 'Objects detected'})
        # Mock for detect_privacy_content
        image_validator.detect_privacy_content = MagicMock(return_value={'faces_detected': 0, 'privacy_protected': False, 'processed_image': None, 'feedback': 'No faces'})

        result = image_validator.validate_image(dummy_image_file)
        assert result['valid'] is True
        assert result['overall_score'] >= 0.7
        assert "Sharp" in result['sharpness']['feedback']
        assert "Objects detected" in result['objects']['feedback']
        assert "No faces" in result['privacy']['feedback']
        assert result['image_path'] == dummy_image_file
        assert 'timestamp' in result

    def test_validate_image_overall_invalid_blurry(self, image_validator, mock_cv2, mock_yolo, dummy_image_file):
        # Mock for validate_file
        image_validator.validate_file = MagicMock(return_value={'valid': True, 'format': '.jpg', 'size': 100, 'message': 'File validation passed'})
        # Mock for check_sharpness
        image_validator.check_sharpness = MagicMock(return_value={'valid': False, 'score': 50.0, 'threshold': 100.0, 'feedback': 'Blurry'})
        # Mock for detect_objects
        image_validator.detect_objects = MagicMock(return_value={'valid': True, 'detections': [{'class': 'person', 'confidence': 0.9, 'bbox': [10,10,20,20]}], 'feedback': 'Objects detected'})
        # Mock for detect_privacy_content
        image_validator.detect_privacy_content = MagicMock(return_value={'faces_detected': 0, 'privacy_protected': False, 'processed_image': None, 'feedback': 'No faces'})

        result = image_validator.validate_image(dummy_image_file)
        assert result['valid'] is False
        assert result['overall_score'] < 0.7
        assert "Blurry" in result['sharpness']['feedback']
        assert "Objects detected" in result['objects']['feedback']
        assert "No faces" in result['privacy']['feedback']
        assert result['image_path'] == dummy_image_file
        assert 'timestamp' in result
