"""
Quick script to verify environment variables are loaded correctly.
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Environment Variables Check ===")
print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'NOT SET')}")

gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print(f"GEMINI_API_KEY: {gemini_key[:4]}...{gemini_key[-4:]}")
else:
    print("GEMINI_API_KEY: NOT SET")

openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"OPENAI_API_KEY: {openai_key[:4]}...{openai_key[-4:]}")
else:
    print("OPENAI_API_KEY: NOT SET")
