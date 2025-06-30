import requests
import json

# Test authentication
url = "http://localhost:8000/api/auth/login/"
data = {
    "username": "testuser",
    "password": "TestPassword123!"
}

print("Testing authentication with:", data)

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    tokens = response.json()
    print("\nAuthentication successful!")
    print(f"Access Token: {tokens.get('access', '')[:50]}...")
    print(f"Refresh Token: {tokens.get('refresh', '')[:50]}...")
else:
    print("\nAuthentication failed!")
    
# Try with admin user
print("\n" + "="*50 + "\n")
data = {
    "username": "admin",
    "password": "AdminPassword123!"
}

print("Testing admin authentication with:", data)
response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")