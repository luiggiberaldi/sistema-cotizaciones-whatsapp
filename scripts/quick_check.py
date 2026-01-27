import requests
import sys

# URL base
API_URL = "http://localhost:8000/api/v1/quotes"

# Headers simulados (sin autenticacion real por ahora para ver si responde 401 o crash)
try:
    print(f"Probando conexion a {API_URL}...")
    response = requests.get(API_URL)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("EXITO: El servidor responde 401 (no autorizado), lo cual es correcto sin token.")
        print("El bug de shadowing 'status' parece resuelto si no dio 500.")
    elif response.status_code == 200:
        print("EXITO: El servidor respondio 200 OK.")
    else:
        print(f"ADVERTENCIA: Codigo inesperado: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"ERROR: No se pudo conectar al backend: {e}")
    sys.exit(1)
