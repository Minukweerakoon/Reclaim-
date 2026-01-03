import os
import logging
import requests
import json
from typing import Dict, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ExternalIntegrationService')

class ExternalIntegrationService:
    """
    Handles forwarding of validated validation data to the external Matching Engine.
    """
    
    def __init__(self):
        self.service_url = os.getenv("MATCHING_SERVICE_URL", "http://localhost:8080/api/items")
        self.api_key = os.getenv("MATCHING_SERVICE_API_KEY", "")
        self.enabled = bool(self.service_url)
        
        if not self.enabled:
            logger.warning("MATCHING_SERVICE_URL not set. Integration disabled.")

    def post_validated_item(self, 
                          validation_data: Dict[str, Any], 
                          image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Forward validated item data to the matching engine.
        
        Args:
            validation_data: The JSON result from validate_complete
            image_path: Path to the image file to upload
        
        Returns:
            Response from the external service
        """
        if not self.enabled:
            return {"status": "integration_disabled"}
            
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            
        # Prepare Data Payload
        # Extract key fields to ensure a clean payload for the matching engine
        payload = {
            "validation_id": validation_data.get("request_id"),
            "timestamp": validation_data.get("timestamp"),
            "input_types": validation_data.get("input_types"),
            "confidence_score": validation_data.get("confidence", {}).get("overall_confidence"),
            "validation_action": validation_data.get("confidence", {}).get("action"),
            # Include specialized results directly
            "text": validation_data.get("text"), # Raw text if available in response? Usually it's in input
            "image_result": json.dumps(validation_data.get("image")), # Serialize complex nested objects
            "voice_result": json.dumps(validation_data.get("voice")),
            "metadata": {
                "source": "multimodal_validator",
                "version": "v1.0"
            }
        }
        
        # If we have original inputs in the validation_data (which we might not, 
        # usually validate_result only has OUTPUTS. Check app.py to see if we pass originals)
        # Assuming validation_data is the RESPONSE object.
        
        files = {}
        if image_path and os.path.exists(image_path):
            try:
                files["image"] = open(image_path, "rb")
            except Exception as e:
                logger.error(f"Could not open image file {image_path}: {e}")

        try:
            logger.info(f"Forwarding item {payload['validation_id']} to {self.service_url}")
            response = requests.post(
                self.service_url,
                data=payload,
                files=files,
                headers=headers,
                timeout=10 # Short timeout to avoiding blocking
            )
            response.raise_for_status()
            
            logger.info(f"Integration success: {response.status_code}")
            return {"status": "success", "external_id": response.json().get("id")}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Integration failed: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            # Close file handles
            for f in files.values():
                f.close()
