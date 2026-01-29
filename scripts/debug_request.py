import requests
import json

def test_get_quotes():
    url = "http://localhost:8000/api/v1/quotes/"
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print("Response:", response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_quotes()
