import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Fallback only for local testing if needed, do not commit keys
    print("Please set GEMINI_API_KEY in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            print(f"  Max Output Tokens: {m.output_token_limit}")
            print("-" * 20)
except Exception as e:
    print(f"Error listing models: {e}")
