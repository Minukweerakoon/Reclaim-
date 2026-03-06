import os
import json
import argparse
from multimodal_validator import MultimodalValidator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Multimodal Consistency Validation Demo')
    parser.add_argument('--text', type=str, help='Text description to validate')
    parser.add_argument('--text_file', type=str, help='Path to text file containing description')
    parser.add_argument('--image', type=str, help='Path to the image file')
    parser.add_argument('--audio', type=str, help='Path to the audio file')
    parser.add_argument('--language', type=str, default='en', choices=['en', 'si', 'ta'], help='Language code (en, si, ta)')
    parser.add_argument('--output', type=str, help='Path to save validation results (optional)')
    parser.add_argument('--bayesian', action='store_true', help='Enable Bayesian confidence estimation')
    args = parser.parse_args()
    
    # Check if at least one modality is provided
    if not args.text and not args.text_file and not args.image and not args.audio:
        print("Error: At least one modality (text, image, or audio) must be provided")
        return
    
    # Get text from file if provided
    text = None
    if args.text_file:
        if not os.path.exists(args.text_file):
            print(f"Error: Text file '{args.text_file}' does not exist")
            return
        try:
            with open(args.text_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return
    elif args.text:
        text = args.text
    
    # Check if image file exists
    if args.image and not os.path.exists(args.image):
        print(f"Error: Image file '{args.image}' does not exist")
        return
    
    # Check if audio file exists
    if args.audio and not os.path.exists(args.audio):
        print(f"Error: Audio file '{args.audio}' does not exist")
        return
    
    # Initialize the multimodal validator
    print("Initializing Multimodal Validator...")
    validator = MultimodalValidator(
        enable_bayesian_estimation=args.bayesian
    )
    
    # Validate the inputs
    print("\nValidating multimodal inputs...")
    result = validator.validate(
        text=text,
        image_path=args.image,
        audio_path=args.audio,
        language=args.language
    )
    
    # Print validation results
    print("\n===== Validation Results =====")
    print(f"Overall validity: {'PASSED' if result['valid'] else 'FAILED'}")
    print(f"Confidence: {result['confidence']:.4f} [{result['confidence_interval'][0]:.4f}, {result['confidence_interval'][1]:.4f}]")
    print(f"Routing: {result['routing']}")
    print(f"Processing time: {result['processing_time']:.2f} seconds")
    print(f"Message: {result['message']}")
    
    # Print modal scores
    print("\n--- Modal Scores ---")
    for modality, data in result['modal_scores'].items():
        if data:  # Only print if data exists for this modality
            print(f"\n{modality.upper()} VALIDATION:")
            if modality == 'text' and 'completeness' in data:
                print(f"  Completeness: {data['completeness']['score']:.2f} ({'Valid' if data['completeness']['valid'] else 'Invalid'})")
                print(f"  Coherence: {data['coherence']['score']:.2f} ({'Valid' if data['coherence']['valid'] else 'Invalid'})")
            elif modality == 'audio' and 'transcription' in data:
                print(f"  Transcription: {'Valid' if data['transcription']['valid'] else 'Invalid'}")
                if data['transcription']['text']:
                    print(f"  Text: \"{data['transcription']['text']}\"")
                print(f"  Audio Quality: {'Valid' if data['audio_quality']['valid'] else 'Invalid'}")
            elif modality == 'cross_modal' and 'scores' in data:
                for pair, pair_data in data['scores'].items():
                    print(f"  {pair}: {pair_data['similarity']:.4f} ({'Valid' if pair_data['valid'] else 'Invalid'})")
    
    # Print consistency results
    if result['consistency']['temporal']['references'] or result['consistency']['geographic']['references']:
        print("\n--- Consistency Analysis ---")
        
        if result['consistency']['temporal']['references']:
            print("\nTemporal References:")
            for i, ref in enumerate(result['consistency']['temporal']['references']):
                print(f"  {i+1}. {ref['text']} ({ref['type']})")
        
        if result['consistency']['geographic']['references']:
            print("\nGeographic References:")
            for i, ref in enumerate(result['consistency']['geographic']['references']):
                print(f"  {i+1}. {ref['text']} ({ref['type']})")
        
        if result['consistency']['contradictions']:
            print("\nContradictions Detected:")
            for i, contradiction in enumerate(result['consistency']['contradictions']):
                print(f"  {i+1}. Between: \"{contradiction['sentence1']}\" and \"{contradiction['sentence2']}\"")
                print(f"     Severity: {contradiction['severity']}")
    
    # Print feedback
    print("\n--- Feedback ---")
    if result['feedback']['missing_elements']:
        print(f"Missing elements: {', '.join(result['feedback']['missing_elements'])}")
    
    if result['feedback']['suggestions']:
        print("\nSuggestions for improvement:")
        for i, suggestion in enumerate(result['feedback']['suggestions']):
            print(f"  {i+1}. {suggestion}")
    
    # Save JSON result if output path is provided
    if args.output:
        json_output = args.output if args.output.endswith('.json') else args.output + '.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nValidation result saved to: {json_output}")

if __name__ == "__main__":
    main()