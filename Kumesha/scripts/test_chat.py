import requests
import json

url = "http://127.0.0.1:8000/api/chat/message"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key"
}
data = {
    "message": "Hello",
    "history": []
}

print(f"Sending POST to {url}...")
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
