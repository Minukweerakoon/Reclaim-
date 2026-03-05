import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.intelligence.llm_client import get_llm_client

def main():
    llm = get_llm_client()
    user_message = "I found a black colour nikon camera yesterday at 9.00 p.m near the movie theator"
    
    history = [
        {"role": "bot", "content": "Describe the lost or found item, and I'll guide you through the report."}
    ]
    extracted_info = {}
    print(f"Testing with message: {user_message}")
    result = llm._gemini_guide_conversation(user_message, history, extracted_info)
    print("Result:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
