"""
Test script to verify REAL Gemini Intelligence.
We use a prompt that the Mock provider DOES NOT know about.
"""
import requests
import json

def test_gemini_intelligence():
    url = 'http://localhost:8000/validate/text'
    headers = {'X-API-Key': 'test-api-key'}
    
    # Novel Scenario: Vintage Item (Mock provider has NO rules for "vintage" or "walkman")
    # If the system identifies this as "collectible" or "vintage", it MUST be using Gemini.
    payload = {'text': "I lost a vintage 1990s Sony Walkman in the park.", 'language': 'en'}
    
    print(f"Sending request: {payload['text']}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            feedback = data.get('feedback', {}).get('message', '')
            print(f"\nFeedback received:\n{feedback}")
            
            # Check for signs of real intelligence
            if "vintage" in feedback.lower() or "collectible" in feedback.lower() or "value" in feedback.lower():
                print("\n✅ SUCCESS: Real Intelligence Detected!")
                print("The system recognized the 'vintage' nature of the item, which is NOT in the mock rules.")
            else:
                print("\n⚠️ WARNING: Response seems generic.")
                print("If you are using the Mock provider, this is expected.")
                print("If you set LLM_PROVIDER=gemini, check your API key.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_gemini_intelligence()
