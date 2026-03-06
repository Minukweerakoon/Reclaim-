import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Force an invalid model to test the fallback
os.environ['LLM_MODEL'] = 'gemini-broken-test'

from src.intelligence.llm_client import get_llm_client

def test_extraction():
    client = get_llm_client()
    print("INITIALIZED GENERATIVE MODEL:", client.gemini_model.model_name)
    try:
        result = client.guide_conversation("I lost my nike shoes yesterday at the park")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("EXCEPTION:", repr(e))

if __name__ == "__main__":
    test_extraction()
