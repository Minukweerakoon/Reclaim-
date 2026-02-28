import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.text.validator import TextValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestZeroShot")

def test_zero_shot_classification():
    logger.info("Initializing TextValidator (this may take a moment to download models)...")
    validator = TextValidator()
    
    # Test case 1: Ambiguous description implying a phone
    text1 = "I lost my communication device that I use to call people."
    logger.info(f"Testing text: '{text1}'")
    result1 = validator.validate_text(text1)
    
    item_type1 = result1['completeness']['entities']['item_type']
    logger.info(f"Detected item types: {item_type1}")
    
    # Check if 'phone' was detected (mapped from 'phone' label or similar)
    # The labels are keys of ITEM_KEYWORDS: phone, bag, electronics, accessories
    if 'phone' in item_type1:
        logger.info("SUCCESS: Correctly identified 'phone' from ambiguous text.")
    else:
        logger.error(f"FAILURE: Failed to identify 'phone'. Got: {item_type1}")

    # Test case 2: Ambiguous description implying a bag
    text2 = "I left my leather container that holds my money and cards on the table."
    logger.info(f"Testing text: '{text2}'")
    result2 = validator.validate_text(text2)
    
    item_type2 = result2['completeness']['entities']['item_type']
    logger.info(f"Detected item types: {item_type2}")
    
    # The refined logic might return 'wallet' specifically
    if 'bag' in item_type2 or 'wallet' in item_type2:
        logger.info("SUCCESS: Correctly identified 'bag' or 'wallet' from ambiguous text.")
    else:
        logger.error(f"FAILURE: Failed to identify 'bag' or 'wallet'. Got: {item_type2}")

if __name__ == "__main__":
    test_zero_shot_classification()
