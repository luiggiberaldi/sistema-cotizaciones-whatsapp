import google.generativeai as genai
import os

key = "AIzaSyA44HtoXiwFrMQsiv24bHW77Zwbzbu_-9k"
genai.configure(api_key=key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
