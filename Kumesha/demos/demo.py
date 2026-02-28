import os
import json
import cv2
import argparse
from image_validator import ImageValidator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Image Validation Demo')
    parser.add_argument('--image', type=str, required=True, help='Path to the image file')
    parser.add_argument('--output', type=str, help='Path to save processed image (optional)')
    parser.add_argument('--blur_threshold', type=float, default=100.0, help='Blur detection threshold')
    parser.add_argument('--confidence', type=float, default=0.85, help='Object detection confidence threshold')
    args = parser.parse_args()
    
    # Check if image exists
    if not os.path.exists(args.image):
        print(f"Error: Image file '{args.image}' does not exist")
        return
    
    # Initialize the image validator
    print("Initializing Image Validator...")
    validator = ImageValidator(
        blur_threshold=args.blur_threshold,
        object_confidence=args.confidence
    )
    
    # Validate the image
    print(f"\nValidating image: {args.image}")
    result = validator.validate_image(args.image)
    
    # Print validation results
    print("\n===== Validation Results =====")
    print(f"Overall validity: {'PASSED' if result['valid'] else 'FAILED'}")
    print(f"Processing time: {result['processing_time']:.2f} seconds")
    print(f"Message: {result['message']}")
    
    # Print detailed results
    print("\n--- File Validation ---")
    file_validation = result['file_validation']
    print(f"Valid: {'Yes' if file_validation['valid'] else 'No'}")
    print(f"Format: {file_validation['format']}")
    print(f"Size: {file_validation['size'] / 1024:.1f} KB")
    print(f"Message: {file_validation['message']}")
    
    print("\n--- Blur Detection ---")
    blur_detection = result['blur_detection']
    print(f"Valid: {'Yes' if blur_detection['valid'] else 'No'}")
    print(f"Variance: {blur_detection['variance']:.2f}")
    print(f"Threshold: {blur_detection['threshold']}")
    print(f"Message: {blur_detection['message']}")
    
    print("\n--- Object Detection ---")
    object_detection = result['object_detection']
    print(f"Valid: {'Yes' if object_detection['valid'] else 'No'}")
    print(f"Objects detected: {len(object_detection['objects'])}")
    print(f"Message: {object_detection['message']}")
    
    # Print detected objects
    if object_detection['objects']:
        print("\nDetected Objects:")
        for i, obj in enumerate(object_detection['objects']):
            print(f"  {i+1}. Class: {obj['class']}, Confidence: {obj['confidence']:.2f}")
    
    print("\n--- Privacy Protection ---")
    privacy = result['privacy_protection']
    print(f"Faces detected: {privacy['faces_detected']}")
    print(f"Faces blurred: {privacy['faces_blurred']}")
    print(f"Message: {privacy['message']}")
    
    # Save processed image if output path is provided
    if args.output and 'blurred_image' in privacy:
        print(f"\nSaving processed image to: {args.output}")
        cv2.imwrite(args.output, privacy['blurred_image'])
        print("Processed image saved successfully")
    
    # Save JSON result
    json_output = args.output.replace('.jpg', '.json') if args.output else 'validation_result.json'
    # Remove the blurred_image from the result before saving to JSON
    if 'blurred_image' in result['privacy_protection']:
        del result['privacy_protection']['blurred_image']
    
    with open(json_output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Validation result saved to: {json_output}")

if __name__ == "__main__":
    main()