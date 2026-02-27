
import sys
import os
import logging

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.cross_modal.enhanced_discrepancies import check_color_mismatch

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

# Mock Data based on user logs
text_result = {
    "text": "black HP laptop",
    "entities": {}
}

image_result = {
    "mismatch_detection": {}
}

cross_modal_result = {
    "image_text": {
        "valid": False,
        "similarity": 0.27,
        "feedback": "Image and text mismatch (similarity: 0.27). Conflict detected: Text mentions 'black' but image appears 'blue'.",
        "mismatch_detection": {}
    }
}

print("Running check_color_mismatch test...")
try:
    result = check_color_mismatch(image_result, text_result, cross_modal_result)
    print(f"\nResult: {result}")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
