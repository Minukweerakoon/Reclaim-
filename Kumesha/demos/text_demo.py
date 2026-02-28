import os
import json
import argparse
from text_validator import TextValidator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Text Validation Demo')
    parser.add_argument('--text', type=str, help='Text description to validate')
    parser.add_argument('--file', type=str, help='Path to text file containing description')
    parser.add_argument('--language', type=str, default='en', choices=['en', 'si', 'ta'], help='Language code (en, si, ta)')
    parser.add_argument('--output', type=str, help='Path to save validation results (optional)')
    parser.add_argument('--completeness', type=float, default=0.7, help='Completeness threshold (default: 0.7)')
    parser.add_argument('--coherence', type=float, default=0.6, help='Coherence threshold (default: 0.6)')
    args = parser.parse_args()
    
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
    
    # Initialize the text validator
    print("Initializing Text Validator...")
    validator = TextValidator(
        completeness_threshold=args.completeness,
        coherence_threshold=args.coherence
    )
    
    # Validate the text
    print(f"\nValidating text in {args.language}:")
    print(f"\"{text}\"")
    result = validator.validate_text(text, args.language)
    
    # Print validation results
    print("\n===== Validation Results =====")
    print(f"Overall validity: {'PASSED' if result['valid'] else 'FAILED'}")
    print(f"Processing time: {result['processing_time']:.2f} seconds")
    print(f"Message: {result['message']}")
    
    # Print detailed results
    print("\n--- Completeness Analysis ---")
    completeness = result['completeness']
    print(f"Valid: {'Yes' if completeness['valid'] else 'No'}")
    print(f"Score: {completeness['score']:.2f} (Threshold: {completeness['threshold']})")
    print(f"Item Type: {'Found: ' + completeness['item_type']['value'] if completeness['item_type']['found'] else 'Not found'}")
    print(f"Color: {'Found: ' + completeness['color']['value'] if completeness['color']['found'] else 'Not found'}")
    print(f"Location: {'Found: ' + completeness['location']['value'] if completeness['location']['found'] else 'Not found'}")
    print(f"Message: {completeness['message']}")
    
    print("\n--- Semantic Coherence ---")
    coherence = result['coherence']
    print(f"Valid: {'Yes' if coherence['valid'] else 'No'}")
    print(f"Score: {coherence['score']:.2f} (Threshold: {coherence['threshold']})")
    print(f"Message: {coherence['message']}")
    
    print("\n--- Entity Extraction ---")
    entities = result['entities']
    print(f"Valid: {'Yes' if entities['valid'] else 'No'}")
    print(f"Entities extracted: {len(entities['extracted'])}")
    print(f"Message: {entities['message']}")
    
    # Print extracted entities
    if entities['extracted']:
        print("\nExtracted Entities:")
        for i, entity in enumerate(entities['extracted']):
            print(f"  {i+1}. {entity['text']} ({entity['label']})")
    
    print("\n--- Feedback Generation ---")
    feedback = result['feedback']
    print(f"Missing elements: {', '.join(feedback['missing_elements']) if feedback['missing_elements'] else 'None'}")
    print(f"Message: {feedback['message']}")
    
    # Print suggestions
    if feedback['suggestions']:
        print("\nSuggestions for improvement:")
        for i, suggestion in enumerate(feedback['suggestions']):
            print(f"  {i+1}. {suggestion}")
    
    # Save JSON result if output path is provided
    if args.output:
        json_output = args.output if args.output.endswith('.json') else args.output + '.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nValidation result saved to: {json_output}")

if __name__ == "__main__":
    main()