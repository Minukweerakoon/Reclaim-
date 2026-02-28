import sys
import os
import logging
import cv2
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.image.validator import ImageValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPrivacy")

def test_privacy_protection():
    logger.info("Initializing ImageValidator...")
    validator = ImageValidator()
    
    # Path to the generated test image
    # We assume the image is copied to tests/test_face.jpg
    image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_face.jpg'))
    
    if not os.path.exists(image_path):
        logger.error(f"Test image not found at {image_path}")
        return

    logger.info(f"Testing privacy protection on: {image_path}")
    result = validator.detect_privacy_content(image_path)
    
    logger.info(f"Result: {result}")
    
    if result['faces_detected'] > 0:
        logger.info(f"SUCCESS: Detected {result['faces_detected']} face(s).")
        if result['privacy_protected']:
            logger.info("SUCCESS: Privacy protection (blurring) applied.")
            logger.info(f"Processed image saved at: {result['processed_image']}")
        else:
            logger.error("FAILURE: Privacy protection NOT applied.")
    else:
        logger.warning("WARNING: No faces detected. The test image might not be clear enough or the cascade failed.")

if __name__ == "__main__":
    test_privacy_protection()
