import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

models_to_test = [
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-1.5-pro"
]

for m in models_to_test:
    try:
        model = genai.GenerativeModel(m)
        res = model.generate_content("hello")
        print(f"SUCCESS: {m}")
    except Exception as e:
        print(f"FAILED {m}: {repr(e)}")
