"""
Script de prueba para API Keys de Gemini.
Versión segura: Lee de variables de entorno o input seguro.
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_key(api_key):
    if not api_key:
        print("❌ No API Key provided")
        return

    print(f"Testing Key: {api_key[:5]}...{api_key[-5:]}")
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello")
        if response.text:
            print("   ✅ Success!")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    key = os.getenv("GEMINI_API_KEY")
    if key:
        test_key(key)
    else:
        print("No GEMINI_API_KEY found in environment.")
