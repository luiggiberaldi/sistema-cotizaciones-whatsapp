import google.generativeai as genai
import time

keys = [
    "AIzaSyA44HtoXiwFrMQsiv24bHW77Zwbzbu_-9k",
    "AIzaSyD0H0OfXtGC8T9vBO98kJu4-VDXrY94mOI"
]

models_to_test = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash-exp"]

print(f"Testing {len(keys)} keys against models: {models_to_test}\n")

for i, key in enumerate(keys):
    masked_key = f"{key[:5]}...{key[-5:]}"
    print(f"--- Testing Key {i+1}: {masked_key} ---")
    
    genai.configure(api_key=key)
    
    for model_name in models_to_test:
        print(f"  > Attempting model: {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello, system check.")
            print(f"    ✅ SUCCESS! Response: {response.text.strip()}")
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                print(f"    ❌ QUOTA EXCEEDED (429)")
            elif "404" in error_msg:
                print(f"    ❌ MODEL NOT FOUND (404) - Model might not exist or no access.")
            elif "400" in error_msg:
                print(f"    ❌ BAD REQUEST (API Key invalid or other error): {error_msg.split('details')[0]}")
            else:
                print(f"    ❌ ERROR: {error_msg}")
        
    print("\n")
    time.sleep(1) # Be nice
