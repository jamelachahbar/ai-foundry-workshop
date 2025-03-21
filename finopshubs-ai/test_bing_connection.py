#!/usr/bin/env python
# test_bing_connection.py - Basic script to verify Bing connection works
# Based on Microsoft documentation: https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool

# Find and load .env file
def find_dotenv():
    """Find .env file by searching up the directory tree"""
    current_path = Path().absolute()
    
    # Try current directory and up to 3 levels up
    for _ in range(4):
        env_path = current_path / '.env'
        if env_path.exists():
            print(f"Found .env file at: {env_path}")
            return env_path
        current_path = current_path.parent
    
    # Default to current directory .env if not found
    print("Could not find .env file, defaulting to current directory")
    return '.env'

# Load environment variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

print("=== Testing Bing Grounding Connection for AI Project ===")

# Check for required variables
conn_string = os.getenv("PROJECT_CONNECTION_STRING")
bing_conn_name = os.getenv("BING_CONNECTION_NAME", "bingsearchfinopshubs")  # Default to the name in your screenshot

if not conn_string:
    print("❌ PROJECT_CONNECTION_STRING is missing! Please check your .env file.")
    sys.exit(1)

# Print values for debugging
print(f"\nProject Connection String: {conn_string[:20]}...{conn_string[-5:] if len(conn_string) > 25 else conn_string}")
print(f"Bing Connection Name: {bing_conn_name}")

try:
    # Initialize the DefaultAzureCredential
    print("\nInitializing DefaultAzureCredential...")
    credential = DefaultAzureCredential()
    print("✅ DefaultAzureCredential initialized")
    
    # Initialize AIProjectClient
    print("\nInitializing AIProjectClient...")
    project_client = AIProjectClient.from_connection_string(
        credential=credential,
        conn_str=conn_string
    )
    print("✅ AIProjectClient initialized successfully")
    
    # Get Bing connection
    print(f"\nAttempting to get Bing connection: {bing_conn_name}")
    bing_connection = project_client.connections.get(connection_name=bing_conn_name)
    
    print(f"✅ Successfully retrieved Bing connection!")
    print(f"Connection details:")
    print(f"- Name: {bing_connection.name}")
    print(f"- ID: {bing_connection.id}")
    
    # Check connection attributes - handle gracefully if properties differ
    try:
        print(f"- Type: {bing_connection.type}")
    except AttributeError:
        print("- Type: [Not available in this SDK version]")
    
    # Try to print connection properties for debugging
    print("\nConnection properties:")
    for prop in dir(bing_connection):
        if not prop.startswith('_') and prop not in ['name', 'id']:
            try:
                value = getattr(bing_connection, prop)
                if not callable(value):
                    print(f"- {prop}: {value}")
            except Exception:
                pass
    
    # Test creating a Bing grounding tool
    print("\nTesting BingGroundingTool initialization...")
    bing_tool = BingGroundingTool(connection_id=bing_connection.id)
    print(f"✅ Successfully created BingGroundingTool!")
    
    # Check if we can access definitions
    try:
        if bing_tool.definitions:
            print(f"- Tool has {len(bing_tool.definitions)} definition(s)")
        else:
            print("- Tool definitions exist but might be empty")
    except Exception as e:
        print(f"- Note: Could not access tool definitions: {str(e)}")
        
    print("\n=== TEST PASSED: Bing connection is accessible and can be used for grounding! ===")
    print("You can now use this connection with your FinOps expert implementation.")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    
    if "get_token" in str(e).lower() or "credential" in str(e).lower():
        print("\nAuthentication Error - Please try these steps:")
        print("1. Run 'az login' to refresh your Azure CLI login")
        print("2. Check your AZURE_TENANT_ID is set correctly")
        print("3. Ensure your account has access to the AI project")
    
    if "connections.get" in str(e).lower():
        print("\nConnection Error - Please try these steps:")
        print(f"1. Verify the connection name '{bing_conn_name}' exists in your AI project")
        print("2. Check if the connection is of type Bing Search")
        print("3. Ensure your credential has access to view this connection")
        print("4. Verify the connection string is correct for your AI project")
    
    if "BingGroundingTool" in str(e):
        print("\nBing Grounding Tool Error - Please try these steps:")
        print("1. Make sure your Azure AI Projects SDK is up to date")
        print("2. Verify that the connection ID is valid")
        print("3. Check that the connection type is compatible with Bing grounding")

print("\nTest completed. Check the results above for details.") 