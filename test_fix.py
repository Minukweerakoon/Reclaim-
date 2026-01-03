import sys
import os
sys.path.append('c:\\Users\\16473\\Desktop\\multimodel-validation')

from src.image.validator import ImageValidator

def test_image_validation():
    print("Initializing ImageValidator...")
    validator = ImageValidator(enable_logging=True, use_vit=True)
    
    image_path = "C:/Users/16473/.gemini/antigravity/brain/f71f301a-cad0-4bc1-9b82-84686ab268aa/uploaded_image_1767380000574.png"
    
    print(f"\nValidating image: {image_path}")
    if not os.path.exists(image_path):
        print("Error: Image file not found!")
        return

    result = validator.validate_image(image_path)
    
    print("\n" + "="*50)
    print("VALIDATION RESULTS")
    print("="*50)
    
    objects = result.get("objects", {})
    print(f"Model Used: {objects.get('model')}")
    print(f"Model Loaded: {objects.get('model_loaded')}")
    
    detections = objects.get("detections", [])
    print(f"\nDetections ({len(detections)}):")
    for i, det in enumerate(detections):
        print(f"  {i+1}. {det['class']} ({det['confidence']:.2%})")
        
    print(f"\nFeedback: {objects.get('feedback')}")
    
    if 'headphone' in [d['class'] for d in detections] or 'headphones' in [d['class'] for d in detections]:
        print("\n✓ SUCCESS: Headphones/Headset detected in top 3!")
    else:
        print("\n⚠️  WARNING: Headphones NOT in top 3. Model might need retraining.")

if __name__ == "__main__":
    test_image_validation()
