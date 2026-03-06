import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestAPI")

def test_image_validation_api():
    url = "http://localhost:8000/validate/image"
    image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_face.jpg'))
    
    if not os.path.exists(image_path):
        logger.error(f"Test image not found at {image_path}")
        return

    logger.info(f"Sending request to {url} with image: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image_file': ('test_face.jpg', f, 'image/jpeg')}
            response = requests.post(url, files=files, headers={"X-API-Key": "test-api-key"})
        
        logger.info(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("SUCCESS: API returned 200 OK")
            logger.info(f"Response keys: {list(data.keys())}")
            if "image" in data and data["image"]:
                logger.info(f"Image validation result keys: {list(data['image'].keys())}")
                if "image_path" in data["image"] and "timestamp" in data["image"]:
                     logger.info("SUCCESS: 'image_path' and 'timestamp' are present in the response.")
                else:
                     logger.error("FAILURE: 'image_path' or 'timestamp' missing in 'image' object.")
            else:
                logger.error("FAILURE: 'image' object missing or empty.")
        else:
            logger.error(f"FAILURE: API returned {response.status_code}")
            logger.error(f"Response: {response.text}")

    except Exception as e:
        logger.error(f"Error sending request: {str(e)}")

if __name__ == "__main__":
    test_image_validation_api()
