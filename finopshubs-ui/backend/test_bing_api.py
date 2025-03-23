"""
Test script for Bing API connection
This script tests your Bing API connection and provides detailed feedback
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
    
    # Check if we have the required keys
    required_keys = ["BING_SEARCH_KEY", "BING_SEARCH_ENDPOINT"]
    for key in required_keys:
        if not os.environ.get(key):
            logger.warning(f"Required key {key} not found in environment")
        else:
            if key == "BING_SEARCH_KEY":
                value = os.environ.get(key)
                if value == "your-bing-search-key" or len(value) < 20:
                    logger.warning(f"{key} appears to be invalid or a placeholder")
                else:
                    # Mask the key for security
                    masked_key = value[:4] + "..." + value[-4:] if len(value) > 8 else "***" 
                    logger.info(f"Found {key} (length: {len(value)}, preview: {masked_key})")
            else:
                logger.info(f"Found {key}: {os.environ.get(key)}")

def test_bing_api():
    """Test if the Bing API connection works"""
    logger.info("Testing Bing API connection...")
    
    # Get API key and endpoint from environment
    subscription_key = os.environ.get("BING_SEARCH_KEY", "")
    endpoint = os.environ.get("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/")
    
    # Check if API key and endpoint are available
    if not subscription_key or subscription_key == "your-bing-search-key":
        logger.error("Missing or invalid BING_SEARCH_KEY in environment")
        print("❌ ERROR: BING_SEARCH_KEY is missing or invalid")
        print("Please add your Bing API key to the .env file or environment variables")
        return False
    
    # Check if the API key looks valid
    if len(subscription_key) < 20:
        logger.error(f"BING_SEARCH_KEY appears to be too short (length: {len(subscription_key)})")
        print(f"❌ ERROR: BING_SEARCH_KEY is too short (length: {len(subscription_key)})")
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
    
    try:
        # Log the request details (without the full API key)
        masked_key = subscription_key[:4] + "..." + subscription_key[-4:] if len(subscription_key) > 8 else "***"
        logger.info(f"Making request to: {search_url}")
        logger.info(f"Using headers: {{'Ocp-Apim-Subscription-Key': '{masked_key}'}}")
        logger.info(f"Using parameters: {params}")
        
        # Make the request
        print(f"Making test request to Bing API...")
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        # Check the response
        if response.status_code == 200:
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
                print("This could indicate a problem with the search query or API configuration")
                print(f"Response fields: {list(search_results.keys())}")
                return False
        else:
            logger.error(f"Bing API returned status code {response.status_code}")
            print(f"❌ ERROR: Bing API returned status code {response.status_code}")
            
            # Special handling for common error codes
            if response.status_code == 401:
                print("401 Unauthorized: Your Bing Search API key is invalid or has expired")
                print("Please check your API key and ensure it's correctly formatted with no extra spaces or quotes")
            elif response.status_code == 403:
                print("403 Forbidden: Your API key doesn't have permission to access this resource")
            
            # Try to get error details from response
            try:
                error_content = response.json() if response.text else "No error details provided"
                print(f"Error details: {json.dumps(error_content, indent=2)}")
            except:
                print(f"Response text: {response.text[:200]}...")
            
            return False
            
    except Exception as e:
        logger.error(f"Error connecting to Bing API: {str(e)}")
        print(f"❌ ERROR: {str(e)}")
        return False

def print_troubleshooting_tips():
    """Print troubleshooting tips for common issues"""
    print("\n=== Troubleshooting Tips ===")
    print("1. Make sure your API key is correctly formatted in your .env file")
    print("   - No quotes around the value")
    print("   - No extra spaces or newlines")
    print("   - Example: BING_SEARCH_KEY=your_actual_key_here")
    print("2. Check that your Bing Search resource is active in Azure Portal")
    print("3. Verify you're using the correct endpoint URL")
    print("4. If you created the API key recently, it may take a few minutes to activate")
    print("5. Check if you've exceeded your API usage quota")
    print("6. Ensure your Azure subscription is active and payments are up to date")

if __name__ == "__main__":
    print("="*50)
    print("Bing API Connection Test")
    print("="*50)
    
    # Load environment variables
    load_env_file()
    
    # Test the API connection
    result = test_bing_api()
    
    if not result:
        print_troubleshooting_tips()
    
    print("="*50) 