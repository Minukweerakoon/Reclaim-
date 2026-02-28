"""
Direct test of LLMClient to debug Gemini integration
"""
from dotenv import load_dotenv
load_dotenv()  # MUST load before importing LLMClient!

from src.intelligence.llm_client import LLMClient

print("=== Testing LLMClient Directly ===\n")

client = LLMClient()
print(f"Provider loaded: {client.provider}")
if client.api_key:
    print(f"API Key (masked): {client.api_key[:4]}...{client.api_key[-4:]}\n")
else:
    print("API Key: None\n")

# Test with a simple query
text = "I lost a vintage 1990s Sony Walkman"
print(f"Testing with: '{text}'\n")

result = client.analyze_text(text)
print("Result from LLM:")
print(result)
