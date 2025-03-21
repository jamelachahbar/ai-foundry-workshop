import requests
import json
import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

# Test 1: Check if the server is running
def test_server_health():
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            print("✅ Server is running and health check passed")
            return True
        else:
            print(f"❌ Server is running but health check failed with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://127.0.0.1:8000")
        return False

# Test 2: Check if the FinOps API test endpoint works
def test_finops_api():
    try:
        response = requests.get("http://127.0.0.1:8000/api/finops/test")
        if response.status_code == 200:
            print("✅ FinOps API test endpoint is working")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ FinOps API test endpoint failed with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://127.0.0.1:8000/api/finops/test")
        return False

# Test 3: Check if the ask endpoint works
def test_ask_endpoint():
    try:
        data = {"question": "What is FinOps?"}
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            "http://127.0.0.1:8000/api/finops/expert/ask",
            data=json.dumps(data),
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ FinOps Expert Ask endpoint is working")
            print(f"   Question: {data['question']}")
            print(f"   Response: {response.json()['answer'][:100]}..." if len(response.json()['answer']) > 100 else response.json()['answer'])
            return True
        else:
            print(f"❌ FinOps Expert Ask endpoint failed with status code: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://127.0.0.1:8000/api/finops/expert/ask")
        return False
    except Exception as e:
        print(f"❌ Error testing ask endpoint: {str(e)}")
        return False

# Test 4: Test Bing connection
def test_bing_connection():
    try:
        response = requests.post("http://127.0.0.1:8000/api/finops/expert/test-bing")
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print("✅ Bing connection test successful")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print("❌ Bing connection test failed")
                print(f"   Message: {result.get('message')}")
                return False
        else:
            print(f"❌ Bing connection test endpoint failed with status code: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://127.0.0.1:8000/api/finops/expert/test-bing")
        return False
    except Exception as e:
        print(f"❌ Error testing Bing connection: {str(e)}")
        return False

# Test 5: Check FinOps Expert module configuration
def test_finops_expert_config():
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/finops/expert/configure",
            data=json.dumps({}),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                print("✅ FinOps Expert module configuration successful")
                print(f"   Message: {result.get('message')}")
                functions = result.get("available_functions", [])
                print(f"   Available functions: {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}")
                return True
            else:
                print("❌ FinOps Expert module configuration failed")
                print(f"   Message: {result.get('message')}")
                return False
        else:
            print(f"❌ FinOps Expert config endpoint failed with status code: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://127.0.0.1:8000/api/finops/expert/configure")
        return False
    except Exception as e:
        print(f"❌ Error testing FinOps Expert configuration: {str(e)}")
        return False

# Test 6: Check the FinOps Expert module health
def test_finops_expert_health():
    try:
        response = requests.get("http://127.0.0.1:8000/api/finops/expert/health")
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok":
                print("✅ FinOps Expert health check passed")
                print(f"   Message: {result.get('message')}")
                print(f"   Version: {result.get('version')}")
                print(f"   Module type: {result.get('module_type')}")
                print(f"   Functions: {', '.join(result.get('functions', []))}")
                return True
            else:
                print("❌ FinOps Expert health check failed")
                print(f"   Message: {result.get('message')}")
                return False
        else:
            print(f"❌ FinOps Expert health check failed with status code: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://127.0.0.1:8000/api/finops/expert/health")
        return False
    except Exception as e:
        print(f"❌ Error testing FinOps Expert health: {str(e)}")
        return False

# Display information about the module path
def print_module_path_info():
    expected_module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "finops_expert_with_bing_grounding.py")
    print("\n📂 Module Path Information:")
    print(f"   Expected module path: {expected_module_path}")
    print(f"   File exists: {os.path.exists(expected_module_path)}")
    
    # Check Python path
    print(f"   Working directory: {os.getcwd()}")
    print(f"   Python path [0]: {sys.path[0]}")
    
    # Check backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    print(f"   backend directory exists: {os.path.exists(backend_dir)}")
    if os.path.exists(backend_dir):
        print(f"   Contents of backend: {', '.join(os.listdir(backend_dir))}")

if __name__ == "__main__":
    print("🔍 Testing FinOps Expert API...")
    
    # Print module path information
    print_module_path_info()
    
    # Run tests
    server_running = test_server_health()
    
    if server_running:
        test_finops_api()
        test_ask_endpoint()
        test_bing_connection()
        test_finops_expert_config()
        test_finops_expert_health()
    else:
        print("⚠️ Cannot proceed with API tests because server is not running")
        print("   Please start the server with `python test_server.py` in the backend directory")
    
    print("\n✨ Test complete") 