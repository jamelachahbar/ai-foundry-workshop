"""
Alternative Test script for Bing API connection
This script uses a different approach to test your Bing API connection
"""
import os
import sys
import logging
import requests
import json
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file"""
    load_dotenv()
    
    # Check for different types of Bing keys
    key_types = [
        "BING_SEARCH_KEY", 
        "BING_SEARCH_V7_SUBSCRIPTION_KEY",
        "AZURE_BING_SEARCH_KEY"
    ]
    
    keys_found = False
    for key_type in key_types:
        if os.environ.get(key_type):
            keys_found = True
            value = os.environ.get(key_type)
            if value == "your-bing-search-key" or len(value) < 20:
                logger.warning(f"{key_type} appears to be invalid or a placeholder")
            else:
                # Mask the key for security
                masked_key = value[:4] + "..." + value[-4:] if len(value) > 8 else "***" 
                logger.info(f"Found {key_type} (length: {len(value)}, preview: {masked_key})")
    
    if not keys_found:
        logger.warning("No Bing search keys found in environment variables")
    
    # Check for endpoints
    endpoint_types = [
        "BING_SEARCH_ENDPOINT",
        "BING_SEARCH_V7_ENDPOINT",
        "AZURE_BING_ENDPOINT"
    ]
    
    endpoints_found = False
    for endpoint_type in endpoint_types:
        if os.environ.get(endpoint_type):
            endpoints_found = True
            logger.info(f"Found {endpoint_type}: {os.environ.get(endpoint_type)}")
    
    if not endpoints_found:
        logger.warning("No Bing search endpoints found in environment variables")

def test_bing_v7():
    """Test if the Bing API v7 connection works"""
    logger.info("Testing Bing API v7 connection...")
    
    # Get API key - try multiple environment variables
    subscription_key = (
        os.environ.get("BING_SEARCH_KEY") or 
        os.environ.get("BING_SEARCH_V7_SUBSCRIPTION_KEY") or 
        os.environ.get("AZURE_BING_SEARCH_KEY")
    )
    
    # Get endpoint - try multiple environment variables
    endpoint = (
        os.environ.get("BING_SEARCH_ENDPOINT") or 
        os.environ.get("BING_SEARCH_V7_ENDPOINT") or 
        os.environ.get("AZURE_BING_ENDPOINT") or
        "https://api.bing.microsoft.com/"
    )
    
    # Check if API key is available
    if not subscription_key or subscription_key == "your-bing-search-key":
        logger.error("Missing or invalid Bing Search API key")
        print("❌ ERROR: No valid Bing Search API key found in environment variables")
        print("Please add a valid key to your .env file using one of these variable names:")
        print("  - BING_SEARCH_KEY")
        print("  - BING_SEARCH_V7_SUBSCRIPTION_KEY")
        print("  - AZURE_BING_SEARCH_KEY")
        return False
    
    # Check if the API key looks valid
    if len(subscription_key) < 20:
        logger.error(f"Bing Search API key appears to be too short (length: {len(subscription_key)})")
        print(f"❌ ERROR: Bing Search API key is too short (length: {len(subscription_key)})")
        print("A valid Bing API key should be much longer")
        return False
    
    # Ensure the endpoint has trailing slash
    if not endpoint.endswith('/'):
        endpoint += '/'
    
    # Construct the search URL
    search_url = endpoint + "v7.0/search"
    
    # Use a simple query for testing
    params = {
        "q": "Azure FinOps",
        "count": 1,
        "offset": 0,
        "mkt": "en-US",
        "responseFilter": "Webpages"
    }
    
    # Set headers with API key
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key
    }
    
    logger.info(f"Using search URL: {search_url}")
    logger.info(f"API key length: {len(subscription_key)}")
    
    try:
        # Make the request
        print(f"Making test request to Bing API v7...")
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        # Check the response
        if response.status_code == 200:
            logger.info(f"Received successful response (200 OK)")
            print(f"✅ SUCCESS: Received 200 OK response from Bing API")
            
            search_results = response.json()
            
            # Check if we have web page results
            if "webPages" in search_results and "value" in search_results["webPages"]:
                result_count = len(search_results["webPages"]["value"])
                logger.info(f"Successfully retrieved {result_count} result(s) from Bing")
                print(f"✅ SUCCESS: Retrieved {result_count} result(s) from Bing API")
                print(f"First result: {search_results['webPages']['value'][0]['name']}")
                return True
            else:
                logger.warning("No web page results found in Bing response")
                print("⚠️ WARNING: No web page results found in Bing response")
                print("Response contains these fields:", list(search_results.keys()))
                return False
        else:
            logger.error(f"Bing API returned status code {response.status_code}")
            print(f"❌ ERROR: Bing API returned status code {response.status_code}")
            
            # Special handling for common error codes
            if response.status_code == 401:
                print("401 Unauthorized: Your Bing Search API key is invalid or has expired")
                print("Please check your API key and ensure it's correctly formatted")
            elif response.status_code == 403:
                print("403 Forbidden: Your API key doesn't have permission to access this resource")
            elif response.status_code == 429:
                print("429 Too Many Requests: You've exceeded your quota or rate limit")
            
            # Try to get error details from response
            try:
                error_content = response.json() if response.text else "No error details provided"
                logger.error(f"Error details: {error_content}")
                print(f"Error details: {json.dumps(error_content, indent=2)}")
            except:
                logger.error(f"Raw response: {response.text[:200]}...")
                print(f"Raw response: {response.text[:200]}...")
            
            return False
            
    except Exception as e:
        logger.error(f"Error connecting to Bing API: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return False

def test_azure_ai_search():
    """Test if the Azure AI Search connection works (alternative to Bing Search)"""
    logger.info("Testing Azure AI Search connection...")
    
    # Get API key
    subscription_key = os.environ.get("AZURE_SEARCH_KEY", "")
    service_name = os.environ.get("AZURE_SEARCH_SERVICE", "")
    
    if not subscription_key or not service_name:
        logger.warning("Azure AI Search credentials not found, skipping test")
        print("⚠️ NOTE: Azure AI Search credentials not found, skipping test")
        return False
    
    # Construct the search URL
    endpoint = f"https://{service_name}.search.windows.net/"
    search_url = endpoint + "indexes?api-version=2021-04-30-Preview"
    
    # Set headers with API key
    headers = {
        "api-key": subscription_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Make the request
        print(f"Making test request to Azure AI Search...")
        response = requests.get(search_url, headers=headers, timeout=10)
        
        # Check the response
        if response.status_code == 200:
            logger.info(f"Azure AI Search connection successful (200 OK)")
            print(f"✅ SUCCESS: Azure AI Search connection successful")
            return True
        else:
            logger.error(f"Azure AI Search returned status code {response.status_code}")
            print(f"❌ ERROR: Azure AI Search returned status code {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error connecting to Azure AI Search: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return False

def print_troubleshooting_tips():
    """Print troubleshooting tips for common issues"""
    print("\n=== Troubleshooting Tips for Bing API ===")
    print("1. Make sure you're using the correct API key:")
    print("   - Azure Portal > Bing Search resource > Keys and Endpoint")
    print("   - Copy Key 1 or Key 2 (not the hidden value)")
    print("   - Check for extra whitespace when copying")
    print("2. Add the key to your .env file with the correct format:")
    print("   BING_SEARCH_KEY=your_actual_key_here")
    print("   (no quotes, no spaces around the equals sign)")
    print("3. Make sure you're using the correct endpoint:")
    print("   - Should be like: https://api.bing.microsoft.com/")
    print("   - Add to .env as: BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/")
    print("4. Try using the Azure AI Foundry approach:")
    print("   - Create an Azure AI Project")
    print("   - Add your Bing Search as a connection")
    print("   - Use the sample code in sample_finops_with_azure.py")
    print("5. Check if your Bing Search resource is active in Azure Portal")
    print("6. Verify you haven't exceeded your API usage quota")

def main():
    print("="*50)
    print("Alternative Bing API Connection Test")
    print("="*50)
    
    # Load environment variables
    load_env_file()
    
    # Test the Bing API v7 connection
    bing_v7_result = test_bing_v7()
    
    # If Bing test failed, try Azure AI Search as fallback
    if not bing_v7_result:
        print("\n" + "-"*50)
        print("Trying Azure AI Search as alternative...")
        azure_search_result = test_azure_ai_search()
        
        if not azure_search_result:
            print("\nBoth Bing API and Azure AI Search tests failed.")
            print_troubleshooting_tips()
    
    print("="*50)

if __name__ == "__main__":
    main() 