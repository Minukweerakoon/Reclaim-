"""
Test script to verify Research-Grade Intelligence on running API.
"""
import requests
import json

def test_api():
    url = 'http://localhost:8000/validate/text'
    headers = {'X-API-Key': 'test-api-key'}
    
    # Case 1: Sentimental Value (LLM)
    payload1 = {'text': "I lost my late grandmother's locket.", 'language': 'en'}
    print(f"Sending request 1: {payload1['text']}")
    try:
        response = requests.post(url, headers=headers, json=payload1)
        if response.status_code == 200:
            data = response.json()
            feedback = data.get('feedback', {}).get('message', '')
            if "sentimental value" in feedback.lower() or "family connection" in feedback.lower():
                print("✅ SUCCESS: LLM Sentimental Analysis detected!")
            else:
                print("❌ FAILURE: LLM Analysis NOT detected.")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection failed: {e}")

    # Case 2: Plausibility Check (Rule-Based)
    payload2 = {'text': "I lost my red Gucci iPhone", 'language': 'en'}
    print(f"\nSending request 2: {payload2['text']}")
    try:
        response = requests.post(url, headers=headers, json=payload2)
        if response.status_code == 200:
            data = response.json()
            questions = data.get('clarification_questions', [])
            print(f"Questions received: {questions}")
            if any("gucci case" in q.lower() for q in questions):
                print("✅ SUCCESS: Plausibility Check detected!")
            else:
                print("❌ FAILURE: Plausibility Check NOT detected.")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_api()
