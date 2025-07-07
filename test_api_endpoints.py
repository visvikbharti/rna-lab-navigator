#!/usr/bin/env python3
"""
RNA Lab Navigator API Testing Script
Tests all critical endpoints to verify the system is working
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://rnalab.pythonanywhere.com"
FRONTEND_URL = "https://rna-lab-navigator-production-ctbr1wtbw.vercel.app"
TEST_USER = "admin"
TEST_PASSWORD = "GODisone@1"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")

def test_result(test_name, success, message=""):
    """Print test result"""
    if success:
        print(f"{GREEN}✓{RESET} {test_name}")
    else:
        print(f"{RED}✗{RESET} {test_name}")
        if message:
            print(f"  {YELLOW}→ {message}{RESET}")

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        
    def test_backend_health(self):
        """Test if backend is accessible"""
        print_header("Testing Backend Health")
        try:
            response = requests.get(f"{BASE_URL}/api/", timeout=10)
            test_result("Backend accessible", response.status_code < 500)
            return response.status_code < 500
        except Exception as e:
            test_result("Backend accessible", False, str(e))
            return False
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        print_header("Testing CORS Configuration")
        try:
            # Test preflight request
            headers = {
                'Origin': FRONTEND_URL,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type,authorization'
            }
            response = requests.options(
                f"{BASE_URL}/api/auth/login/", 
                headers=headers,
                timeout=10
            )
            
            cors_headers_present = 'access-control-allow-origin' in response.headers
            test_result("CORS headers present", cors_headers_present)
            
            if cors_headers_present:
                allowed_origin = response.headers.get('access-control-allow-origin', '')
                correct_origin = allowed_origin == FRONTEND_URL or allowed_origin == '*'
                test_result("Correct origin allowed", correct_origin, 
                          f"Allowed: {allowed_origin}")
            
            return cors_headers_present
        except Exception as e:
            test_result("CORS test", False, str(e))
            return False
    
    def test_login(self):
        """Test login endpoint"""
        print_header("Testing Authentication")
        try:
            # Test login endpoint exists
            login_url = f"{BASE_URL}/api/auth/login/"
            
            # First test if endpoint exists
            response = requests.post(login_url, json={}, timeout=10)
            endpoint_exists = response.status_code != 404
            test_result("Login endpoint exists", endpoint_exists)
            
            if not endpoint_exists:
                return False
            
            # Test actual login
            login_data = {
                "username": TEST_USER,
                "password": TEST_PASSWORD
            }
            response = requests.post(login_url, json=login_data, timeout=10)
            
            login_success = response.status_code == 200
            test_result("Login with credentials", login_success, 
                       f"Status: {response.status_code}")
            
            if login_success:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                
                test_result("Access token received", bool(self.access_token))
                test_result("Refresh token received", bool(self.refresh_token))
                
                return bool(self.access_token)
            
            return False
        except Exception as e:
            test_result("Login test", False, str(e))
            return False
    
    def test_authenticated_endpoint(self):
        """Test an authenticated endpoint"""
        print_header("Testing Authenticated Access")
        
        if not self.access_token:
            test_result("Authentication required", False, "No access token")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Origin': FRONTEND_URL
            }
            
            # Test profile endpoint
            response = requests.get(
                f"{BASE_URL}/api/auth/profile/",
                headers=headers,
                timeout=10
            )
            
            auth_success = response.status_code == 200
            test_result("Authenticated request", auth_success,
                       f"Status: {response.status_code}")
            
            return auth_success
        except Exception as e:
            test_result("Authenticated request", False, str(e))
            return False
    
    def test_query_endpoint(self):
        """Test the main query endpoint"""
        print_header("Testing Query Endpoint")
        
        if not self.access_token:
            test_result("Authentication required", False, "No access token")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Origin': FRONTEND_URL
            }
            
            query_data = {
                "query": "What is RNA extraction protocol?",
                "session_id": "test-session"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/query/",
                headers=headers,
                json=query_data,
                timeout=30
            )
            
            query_success = response.status_code == 200
            test_result("Query endpoint", query_success,
                       f"Status: {response.status_code}")
            
            if query_success:
                data = response.json()
                has_answer = 'answer' in data or 'response' in data
                test_result("Query returns answer", has_answer)
                
                # Measure response time
                if has_answer:
                    print(f"  {YELLOW}→ Response preview: {str(data)[:100]}...{RESET}")
            
            return query_success
        except Exception as e:
            test_result("Query test", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BLUE}RNA Lab Navigator API Test Suite{RESET}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend: {BASE_URL}")
        print(f"Frontend: {FRONTEND_URL}")
        
        # Track results
        results = {
            'backend_health': self.test_backend_health(),
            'cors': self.test_cors_headers(),
            'login': self.test_login(),
            'authenticated': self.test_authenticated_endpoint(),
            'query': self.test_query_endpoint()
        }
        
        # Summary
        print_header("Test Summary")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print(f"{GREEN}✓ All tests passed! System is ready for beta testing.{RESET}")
        elif results['backend_health'] and not results['cors']:
            print(f"{YELLOW}⚠ Backend is up but CORS needs configuration.{RESET}")
            print(f"{YELLOW}  Action needed: Update PythonAnywhere and reload.{RESET}")
        else:
            print(f"{RED}✗ Some tests failed. Please check the issues above.{RESET}")
        
        return passed == total

def main():
    """Main function"""
    tester = APITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()