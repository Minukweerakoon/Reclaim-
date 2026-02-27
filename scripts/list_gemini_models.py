"""
List available Gemini models to debug the 404 error
"""
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
import os

api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key: {api_key[:4]}...{api_key[-4:]}")

genai.configure(api_key=api_key)

print("\n=== Listing Available Models ===\n")
with open("gemini_models.txt", "w") as f:
    try:
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                output = f"Model: {model.name}\n"
                output += f"  Display Name: {model.display_name}\n"
                output += f"  Description: {model.description[:100] if model.description else 'N/A'}\n\n"
                print(output)
                f.write(output)
        print("Models saved to gemini_models.txt")
    except Exception as e:
        error_msg = f"Error listing models: {e}"
        print(error_msg)
        f.write(error_msg)
