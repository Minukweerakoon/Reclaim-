import os
import json
import argparse
from audio_validator import AudioValidator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Audio Validation Demo')
    parser.add_argument('--audio', type=str, required=True, help='Path to the audio file')
    parser.add_argument('--output', type=str, help='Path to save validation results (optional)')
    parser.add_argument('--model', type=str, default='small', choices=['tiny', 'base', 'small', 'medium', 'large'], 
                        help='Whisper model size (default: small)')
    parser.add_argument('--snr_threshold', type=float, default=20.0, help='Signal-to-noise ratio threshold (default: 20.0)')
    parser.add_argument('--min_duration', type=float, default=5.0, help='Minimum audio duration in seconds (default: 5.0)')
    parser.add_argument('--max_duration', type=float, default=120.0, help='Maximum audio duration in seconds (default: 120.0)')
    args = parser.parse_args()
    
    # Check if audio file exists
    if not os.path.exists(args.audio):
        print(f"Error: Audio file '{args.audio}' does not exist")
        return
    
    # Initialize the audio validator
    print("Initializing Audio Validator...")
    validator = AudioValidator(
        whisper_model_size=args.model,
        snr_threshold=args.snr_threshold,
        min_duration=args.min_duration,
        max_duration=args.max_duration
    )
    
    # Validate the audio
    print(f"\nValidating audio: {args.audio}")
    result = validator.validate_audio(args.audio)
    
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
    
    print("\n--- Audio Quality Assessment ---")
    audio_quality = result['audio_quality']
    print(f"Valid: {'Yes' if audio_quality['valid'] else 'No'}")
    print(f"Duration: {audio_quality['duration']:.2f} seconds")
    print(f"Signal-to-Noise Ratio: {audio_quality['snr']:.2f} dB (Threshold: {audio_quality['threshold']})")
    print(f"Clarity: {audio_quality['clarity']:.2f}")
    print(f"Message: {audio_quality['message']}")
    
    print("\n--- Speech Recognition ---")
    transcription = result['transcription']
    print(f"Valid: {'Yes' if transcription['valid'] else 'No'}")
    print(f"Confidence: {transcription['confidence']:.2f}")
    print(f"Message: {transcription['message']}")
    
    # Print transcription text
    if transcription['text']:
        print("\nTranscribed Text:")
        print(f"\"{transcription['text']}\"")
    
    # Print recommendations
    if result['recommendations']:
        print("\n--- Recommendations ---")
        for i, recommendation in enumerate(result['recommendations']):
            print(f"  {i+1}. {recommendation}")
    
    # Save JSON result if output path is provided
    if args.output:
        json_output = args.output if args.output.endswith('.json') else args.output + '.json'
        with open(json_output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nValidation result saved to: {json_output}")

if __name__ == "__main__":
    main()