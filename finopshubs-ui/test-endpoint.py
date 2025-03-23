import requests
import os
import sys
import json

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("FinOps API Test Script")
print("======================")

BASE_URL = "http://localhost:8000"

def test_endpoint(url, method="GET", data=None):
    """Test a specific endpoint and return the response"""
    full_url = f"{BASE_URL}{url}"
    print(f"\nTesting {method} {full_url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(full_url, timeout=10)
        elif method.upper() == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(full_url, json=data, headers=headers, timeout=10)
        else:
            print(f"Unsupported method: {method}")
            return None
        
        # Print status code
        print(f"Status Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            json_data = response.json()
            print(f"Response: {json.dumps(json_data, indent=2)}")
            return json_data
        except json.JSONDecodeError:
            print(f"Response (text): {response.text[:200]}...")
            return response.text
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return None

print("\n1. Testing basic API endpoint...")
test_endpoint("/")

print("\n2. Testing health check endpoint...")
test_endpoint("/health")

print("\n3. Testing FinOps test endpoint...")
test_endpoint("/api/finops/test")

print("\n4. Testing FinOps Expert module health...")
test_endpoint("/api/finops/expert/health")

print("\n5. Testing FinOps Expert module configuration...")
test_endpoint("/api/finops/expert/configure", method="POST", data={})

print("\n6. Testing FinOps Expert Bing connection...")
test_endpoint("/api/finops/expert/test-bing", method="POST")

print("\n7. Testing FinOps Expert ask endpoint with a simple question...")
question_data = {
    "question": "What is FinOps?",
    "options": {
        "verify_links": True,
        "include_agent_thoughts": True
    }
}
test_endpoint("/api/finops/expert/ask", method="POST", data=question_data)

print("\nTests completed.") 