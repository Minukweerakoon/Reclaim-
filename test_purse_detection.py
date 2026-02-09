"""Quick test to see what YOLO detects for the purse image"""
import sys
sys.path.append('c:\\Users\\16473\\Desktop\\multimodel-validation')

from src.image.validator import ImageValidator

image_path = "C:/Users/16473/.gemini/antigravity/brain/f71f301a-cad0-4bc1-9b82-84686ab268aa/uploaded_image_3_1767496519516.jpg"

validator = ImageValidator(enable_logging=True)
result = validator.detect_objects(image_path, text_hint="black Gucci purse")

print("\n" + "="*60)
print("DETECTION RESULTS FOR PURSE:")
print("="*60)
print(f"Model: {result.get('model')}")
print(f"Valid: {result.get('valid')}")
print(f"Confidence: {result.get('confidence'):.2%}")
print(f"\nDetections:")
for i, det in enumerate(result.get('detections', [])[:5]):
    print(f"  {i+1}. {det['class']} ({det['confidence']:.2%})")
    if 'original_class' in det:
        print(f"     Original YOLO: {det['original_class']}")
print(f"\nFeedback: {result.get('feedback')}")
print("="*60)
