"""
Simple Mock Matching Engine Service
Accepts validated items from the multimodal validation system.
Run on port 8080 to demonstrate external integration.
"""

from flask import Flask, request, jsonify
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MockMatchingEngine')

app = Flask(__name__)

# Store received items in memory
received_items = []

@app.route('/api/items', methods=['POST'])
def receive_item():
    """
    Endpoint to receive validated items from the validation system.
    """
    try:
        # Log the incoming request
        logger.info("=" * 80)
        logger.info("📦 RECEIVED NEW VALIDATED ITEM")
        logger.info("=" * 80)
        
        # Get form data
        data = request.form.to_dict()
        
        # Log all received fields
        logger.info(f"Validation ID: {data.get('validation_id')}")
        logger.info(f"Timestamp: {data.get('timestamp')}")
        logger.info(f"Input Types: {data.get('input_types')}")
        logger.info(f"Confidence Score: {data.get('confidence_score')}")
        logger.info(f"Validation Action: {data.get('validation_action')}")
        logger.info(f"Source: {data.get('metadata')}")
        
        # Check if image was uploaded
        if 'image' in request.files:
            image_file = request.files['image']
            logger.info(f"📸 Image received: {image_file.filename}")
        
        # Store the item
        item_record = {
            "id": len(received_items) + 1,
            "validation_id": data.get('validation_id'),
            "received_at": datetime.now().isoformat(),
            "confidence_score": data.get('confidence_score'),
            "validation_action": data.get('validation_action'),
            "has_image": 'image' in request.files
        }
        received_items.append(item_record)
        
        logger.info(f"✅ Item stored with ID: {item_record['id']}")
        logger.info(f"📊 Total items received: {len(received_items)}")
        logger.info("=" * 80)
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": "Item received and stored successfully",
            "id": item_record['id'],
            "timestamp": item_record['received_at']
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing item: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/items', methods=['GET'])
def list_items():
    """
    List all received items.
    """
    return jsonify({
        "total_items": len(received_items),
        "items": received_items
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    """
    return jsonify({
        "status": "healthy",
        "service": "Mock Matching Engine",
        "total_items_received": len(received_items)
    }), 200

if __name__ == '__main__':
    logger.info("🚀 Starting Mock Matching Engine Service")
    logger.info("📍 Listening on http://localhost:8080")
    logger.info("📥 Ready to receive validated items at /api/items")
    logger.info("=" * 80)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
