import requests
import json

# Railway backend URL
backend_url = "https://rna-lab-navigator-production.up.railway.app"

print("Testing RNA Lab Navigator Backend on Railway...")
print("=" * 50)

# Test endpoints
endpoints = [
    ("Root", "/"),
    ("Health", "/health"),
    ("Health with slash", "/health/"),
    ("API Health", "/api/health"),
    ("API Health with slash", "/api/health/"),
    ("Auth Login", "/api/auth/login/"),
]

for name, endpoint in endpoints:
    url = f"{backend_url}{endpoint}"
    print(f"\nTesting {name}: {url}")
    
    try:
        # Test GET request
        response = requests.get(url, allow_redirects=False, timeout=5)
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        if response.status_code == 301:
            print(f"  Redirect Location: {response.headers.get('Location')}")
        elif response.status_code == 200:
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response Text: {response.text[:100]}...")
                
    except Exception as e:
        print(f"  Error: {str(e)}")

# Test login endpoint with POST
print("\n" + "=" * 50)
print("Testing Login Endpoint with POST...")
login_url = f"{backend_url}/api/auth/login/"
login_data = {
    "username": "admin",
    "password": "admin123"
}

try:
    # Test OPTIONS (preflight)
    print(f"\nOPTIONS {login_url}")
    options_response = requests.options(login_url, 
                                      headers={
                                          "Origin": "https://rna-lab-navigator.vercel.app",
                                          "Access-Control-Request-Method": "POST",
                                          "Access-Control-Request-Headers": "Content-Type"
                                      },
                                      allow_redirects=False)
    print(f"  Status Code: {options_response.status_code}")
    print(f"  CORS Headers: {options_response.headers.get('Access-Control-Allow-Origin')}")
    
    # Test POST
    print(f"\nPOST {login_url}")
    post_response = requests.post(login_url, 
                                 json=login_data,
                                 headers={
                                     "Content-Type": "application/json",
                                     "Origin": "https://rna-lab-navigator.vercel.app"
                                 },
                                 allow_redirects=False)
    print(f"  Status Code: {post_response.status_code}")
    
    if post_response.status_code == 200:
        print(f"  Response: {post_response.json()}")
    elif post_response.status_code == 301:
        print(f"  Redirect Location: {post_response.headers.get('Location')}")
        
except Exception as e:
    print(f"  Error: {str(e)}")