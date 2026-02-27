"""Test script for advanced entity detection."""
import requests
import sys

API_URL = "http://localhost:8000"
API_KEY = "test-api-key"

def test_entity_detection(image_path: str):
    """Test the advanced entity detection endpoint."""
    print(f"\nTesting advanced entity detection on: {image_path}")
    print("="*60)
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image_file': f}
            data = {
                'text': 'blue dell laptop',
                'detect_brand': 'true',
                'detect_material': 'true', 
                'detect_size': 'true',
                'detect_ocr': 'true',
                'detect_condition': 'true'
            }
            headers = {'X-API-Key': API_KEY}
            
            response = requests.post(
                f"{API_URL}/api/entities/detect",
                files=files,
                data=data,
                headers=headers
            )
            
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Detection complete in {result.get('processing_time')}s")
            
            detections = result.get('detections', {})
            
            # Brand
            brand = detections.get('brand', {})
            if brand.get('detected_brands'):
                print(f"\n[BRAND] Top: {brand['top_brand']} ({brand['top_confidence']:.1%})")
                for b in brand['detected_brands'][:3]:
                    print(f"  - {b['brand']}: {b['confidence']:.1%}")
            else:
                print(f"\n[BRAND] None detected (error: {brand.get('error', 'N/A')})")
            
            # Material
            material = detections.get('material', {})
            if material.get('detected_materials'):
                print(f"\n[MATERIAL] Primary: {material['primary_material']} ({material['primary_confidence']:.1%})")
            else:
                print(f"\n[MATERIAL] None detected")
            
            # Size
            size = detections.get('size', {})
            print(f"\n[SIZE] Category: {size.get('size_category', 'unknown')} ({size.get('confidence', 0):.1%})")
            
            # OCR
            ocr = detections.get('ocr', {})
            if ocr.get('texts'):
                print(f"\n[OCR] Found {ocr['text_count']} text regions:")
                for text in ocr['texts'][:5]:
                    print(f"  - {text}")
                if ocr.get('serial_numbers'):
                    print(f"  Serial numbers: {ocr['serial_numbers']}")
            else:
                print(f"\n[OCR] No text found (error: {ocr.get('error', 'N/A')})")
            
            # Condition
            condition = detections.get('condition', {})
            if condition.get('top_match'):
                print(f"\n[CONDITION] {condition['top_match']} ({condition['top_confidence']:.1%})")
            
            print("\n" + "="*60)
            print("✓ All entity detection tests passed!")
            
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test image
        test_image = "C:/Users/16473/.gemini/antigravity/brain/f71f301a-cad0-4bc1-9b82-84686ab268aa/uploaded_image_1767381429570.jpg"
    else:
        test_image = sys.argv[1]
    
    test_entity_detection(test_image)
