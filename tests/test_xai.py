import sys
import os
import logging
import torch
from PIL import Image

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cross_modal.clip_validator import CLIPValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestXAI")

def test_explainable_discrepancy():
    validator = CLIPValidator(enable_logging=True)
    
    # Use the user's uploaded image (Red iPhone)
    # Path: C:/Users/16473/.gemini/antigravity/brain/776ef917-6b30-402f-8cfe-b8bf2c8db5b8/uploaded_image_1_1764690354562.jpg
    # We need to copy it to a temp location or just use it directly if accessible.
    # Since I cannot easily copy files here without knowing the exact path structure in the container vs host, 
    # I will assume the path provided in metadata is accessible or I will use a dummy image creation if needed.
    # But wait, the user provided the absolute path in metadata:
    image_path = r"C:\Users\16473\.gemini\antigravity\brain\776ef917-6b30-402f-8cfe-b8bf2c8db5b8\uploaded_image_1_1764690354562.jpg"
    
    if not os.path.exists(image_path):
        logger.error(f"Image not found at {image_path}. Cannot run test.")
        return

    # Scenario: Text says "Black iPhone", Image is Red iPhone
    text_description = "I lost my black iPhone"
    
    logger.info(f"Testing XAI with Image: {image_path}")
    logger.info(f"Text Description: '{text_description}'")
    
    result = validator.validate_image_text_alignment(image_path, text_description)
    
    logger.info(f"Validation Result: {result['valid']}")
    logger.info(f"Similarity: {result['similarity']}")
    logger.info(f"Feedback: {result['feedback']}")
    
    # Verification
    if "Conflict detected" in result['feedback'] and "red" in result['feedback'].lower():
        logger.info("SUCCESS: XAI correctly identified the color conflict.")
    else:
        logger.error("FAILURE: XAI did not generate the expected conflict message.")

if __name__ == "__main__":
    test_explainable_discrepancy()
