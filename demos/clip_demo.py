import os
import json
import argparse
from clip_validator import CLIPValidator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Cross-Modal Consistency Validation Demo')
    parser.add_argument('--image', type=str, required=True, help='Path to the image file')
    parser.add_argument('--text', type=str, help='Text description to validate against the image')
    parser.add_argument('--file', type=str, help='Path to text file containing description')
    parser.add_argument('--output', type=str, help='Path to save validation results (optional)')
    parser.add_argument('--threshold', type=float, default=0.85, help='Similarity threshold (default: 0.85)')
    parser.add_argument('--model', type=str, default='ViT-B/32', 
                        choices=['ViT-B/32', 'ViT-L/14', 'RN50'], 
                        help='CLIP model variant (default: ViT-B/32)')
    parser.add_argument('--no-gpu', action='store_true', help='Disable GPU acceleration')
    args = parser.parse_args()
    
    # Check if image exists
    if not os.path.exists(args.image):
        print(f"Error: Image file '{args.image}' does not exist")
        return
    
    # Check if either text or file is provided
    if not args.text and not args.file:
        print("Error: Either --text or --file must be provided")
        return
    
    # Get text from file if provided
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: Text file '{args.file}' does not exist")
            return
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return
    else:
        text = args.text
    
    # Initialize the CLIP validator
    print("Initializing CLIP Validator...")
    validator = CLIPValidator(
        similarity_threshold=args.threshold,
        model_name=args.model,
        enable_gpu=not args.no_gpu
    )
    
    # Validate the image-text alignment
    print(f"\nValidating alignment between:\nImage: {args.image}\nText: \"{text}\"")
    result = validator.validate_alignment(args.image, text)
    
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
    
    print("\n--- Semantic Alignment ---")
    alignment = result['alignment']
    print(f"Valid: {'Yes' if alignment['valid'] else 'No'}")
    print(f"Similarity Score: {alignment['similarity']:.4f} (Threshold: {alignment['threshold']})")
    print(f"Confidence Interval: [{alignment['confidence_interval'][0]:.4f}, {alignment['confidence_interval'][1]:.4f}]")
    print(f"Message: {alignment['message']}")
    
    print("\n--- Mismatch Detection ---")
    mismatches = result['mismatch_detection']['mismatches']
    if mismatches:
        print(f"Detected {len(mismatches)} potential mismatches:")
        for i, mismatch in enumerate(mismatches):
            print(f"  {i+1}. Category: {mismatch['category']}")
            print(f"     Mentioned in text: {mismatch['mentioned']}")
            print(f"     Likely in image: {mismatch['likely_actual']} (confidence: {mismatch['confidence']:.2f})")
    else:
        print("No specific mismatches detected")
    
    # Print attribute scores
    print("\n--- Attribute Analysis ---")
    for category, data in result['mismatch_detection']['attribute_scores'].items():
        print(f"  {category.capitalize()}: Best match '{data['best_match']}' (score: {data['score']:.2f})")
    
    # Print suggestions
    if result['suggestions']:
        print("\n--- Improvement Suggestions ---")
        for i, suggestion in enumerate(result['suggestions']):
            print(f"  {i+1}. {suggestion}")
    
    # Perform multi-scale analysis
    print("\n===== Multi-Scale Analysis =====")
    multi_scale = validator.multi_scale_analysis(args.image, text)
    
    print(f"Full text ({multi_scale['full_text']['word_count']} words): {multi_scale['full_text']['similarity']:.4f}")
    
    if multi_scale['scales']:
        print("\nScaled Analysis:")
        for scale in multi_scale['scales']:
            print(f"  {scale['word_count']} words: {scale['similarity']:.4f}")
    
    # Save JSON result if output path is provided
    if args.output:
        json_output = args.output if args.output.endswith('.json') else args.output + '.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nValidation result saved to: {json_output}")

if __name__ == "__main__":
    main()