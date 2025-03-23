#!/bin/bash
# Script to start the FinOps Hubs backend server

# Display banner
echo "================================================="
echo "     FinOps Hubs AI API Server Startup Script    "
echo "================================================="

# Check for environment file
if [ -f .env ]; then
    echo "Found .env file"
else
    echo "Warning: No .env file found. Creating a sample one."
    cat > .env << EOL
# Azure AI Foundry Settings (required for Bing integration)
PROJECT_CONNECTION_STRING=your-connection-string
MODEL_DEPLOYMENT_NAME=your-model-deployment
BING_CONNECTION_NAME=your-bing-connection

# DeepSeek Enhancement Settings (optional)
AZURE_ENDPOINT=your-azure-endpoint
AZURE_API_KEY=your-azure-api-key

# Configuration Options
FINOPS_MOCK_MODE=false
FINOPS_ENHANCEMENT_ENABLED=true
EOL
    echo "Please edit the .env file with your actual credentials"
    echo "and restart this script."
    exit 1
fi

# Check if Python environment exists
if [ -d "finopshubsaivenv" ]; then
    echo "Found Python virtual environment"
else
    echo "Creating new Python virtual environment..."
    python -m venv finopshubsaivenv
fi

# Activate virtual environment
case "$(uname -s)" in
    CYGWIN*|MINGW*|MSYS*)
        echo "Activating virtual environment (Windows)..."
        source finopshubsaivenv/Scripts/activate
        ;;
    *)
        echo "Activating virtual environment (Unix)..."
        source finopshubsaivenv/bin/activate
        ;;
esac

# Install requirements
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Test connections
echo "Testing connections to required services..."
python -c "
import logging
logging.basicConfig(level=logging.INFO)
try:
    from finops_expert_azure_ai import test_azure_ai_connection, test_deepseek_connection, MOCK_MODE, ENHANCEMENT_ENABLED
    print(f'MOCK_MODE: {MOCK_MODE}')
    print(f'ENHANCEMENT_ENABLED: {ENHANCEMENT_ENABLED}')
    if not MOCK_MODE:
        print(f'Azure AI Foundry connection: {test_azure_ai_connection()}')
    if ENHANCEMENT_ENABLED:
        print(f'DeepSeek connection: {test_deepseek_connection()}')
except ImportError as e:
    print(f'Error: {e}')
    from finops_expert_with_bing_grounding import test_bing_connection, MOCK_MODE
    print(f'MOCK_MODE: {MOCK_MODE}')
    if not MOCK_MODE:
        print(f'Bing connection: {test_bing_connection()}')
"

# Start the server
echo "Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 