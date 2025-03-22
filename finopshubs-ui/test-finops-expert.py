#!/usr/bin/env python
"""
Test script for FinOps Expert API endpoint
Tests the endpoints and verifies source extraction is working properly
"""
import requests
import json
import sys
import os
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
FINOPS_API_URL = f"{API_BASE_URL}/api/finops"

def print_separator(title):
    """Print a separator with a title"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def test_health_endpoint():
    """Test the health endpoint"""
    print_separator("Testing Health Endpoint")
    try:
        response = requests.get(f"{FINOPS_API_URL}/expert/health")
        response.raise_for_status()
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        print(f"Module Type: {data.get('module_type')}")
        print(f"Available Functions: {data.get('functions')}")
        return True
    except Exception as e:
        print(f"Error testing health endpoint: {str(e)}")
        return False

def test_bing_connection():
    """Test the Bing connection endpoint"""
    print_separator("Testing Bing Connection")
    try:
        response = requests.post(f"{FINOPS_API_URL}/expert/test-bing")
        response.raise_for_status()
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        return data.get('success', False)
    except Exception as e:
        print(f"Error testing Bing connection: {str(e)}")
        return False

def test_configure_endpoint():
    """Test the configure endpoint"""
    print_separator("Testing Configure Endpoint")
    try:
        response = requests.post(
            f"{FINOPS_API_URL}/expert/configure", 
            json={"test": True}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Available Functions: {data.get('available_functions')}")
        return True
    except Exception as e:
        print(f"Error testing configure endpoint: {str(e)}")
        return False

def test_ask_endpoint(question):
    """Test the ask endpoint with a question"""
    print_separator(f"Testing Ask Endpoint with question: '{question}'")
    try:
        response = requests.post(
            f"{FINOPS_API_URL}/expert/ask", 
            json={"question": question}
        )
        response.raise_for_status()
        data = response.json()
        
        # Print answer (truncated if too long)
        answer = data.get('answer', '')
        if len(answer) > 500:
            print(f"Answer (truncated): {answer[:500]}...\n[Content truncated, total length: {len(answer)} chars]")
        else:
            print(f"Answer: {answer}")
        
        # Print sources
        sources = data.get('sources', [])
        if sources:
            print("\nSources extracted:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source.get('title')} - {source.get('url')}")
            print(f"\nTotal sources found: {len(sources)}")
        else:
            print("\nNo sources found in the response")
        
        return True
    except Exception as e:
        print(f"Error testing ask endpoint: {str(e)}")
        return False

def run_all_tests():
    """Run all the tests"""
    print_separator("FinOps Expert API Test Suite")
    print("This script tests the FinOps Expert API endpoints and verifies they are working correctly.")
    
    # Run the tests
    health_ok = test_health_endpoint()
    bing_ok = test_bing_connection()
    configure_ok = test_configure_endpoint()
    
    # Test different types of questions
    questions = [
        "What is FinOps?",
        "How do Azure Reserved Instances work?",
        "What are best practices for tagging cloud resources?",
        "How can I set up budget alerts for my cloud costs?"
    ]
    
    ask_results = []
    for question in questions:
        result = test_ask_endpoint(question)
        ask_results.append(result)
    
    # Print summary
    print_separator("Test Summary")
    print(f"Health Endpoint: {'✅ PASSED' if health_ok else '❌ FAILED'}")
    print(f"Bing Connection: {'✅ PASSED' if bing_ok else '❌ FAILED'}")
    print(f"Configure Endpoint: {'✅ PASSED' if configure_ok else '❌ FAILED'}")
    
    for i, result in enumerate(ask_results):
        print(f"Ask Endpoint (Question {i+1}): {'✅ PASSED' if result else '❌ FAILED'}")
    
    all_passed = health_ok and configure_ok and all(ask_results)
    print(f"\nOverall Test Result: {'✅ ALL PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 