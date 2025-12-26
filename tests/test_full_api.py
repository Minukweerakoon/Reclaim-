"""
Full API response test to see what the server actually returns
"""
import requests
import json

url = 'http://localhost:8000/validate/text'
headers = {'X-API-Key': 'test-api-key'}

payload = {'text': "I lost my grandfather's vintage pocket watch", 'language': 'en'}

print(f"Testing: {payload['text']}\n")

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    data = response.json()
    print("=== FULL API RESPONSE ===")
    print(json.dumps(data, indent=2))
    
    print("\n\n=== KEY FIELDS ===")
    print(f"Valid: {data.get('valid')}")
    print(f"Overall Score: {data.get('overall_score')}")
    
    feedback = data.get('feedback', {})
    if isinstance(feedback, dict):
        print(f"\nFeedback Message:\n{feedback.get('message', 'N/A')}")
    else:
        print(f"\nFeedback: {feedback}")
    
    print(f"\nClarification Questions: {data.get('clarification_questions', [])}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
