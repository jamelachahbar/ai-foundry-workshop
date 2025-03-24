# FinOps Hubs Backend

This is the backend server for FinOps Hubs, providing FinOps expertise with Azure AI Foundry and Bing grounding integration.

## Features

- **Azure AI Foundry Integration**: Uses Azure AI Foundry to create an agent that can answer FinOps-related questions
- **Bing Grounding**: Grounds answers in real-time web search results using Bing Search
- **DeepSeek Enhancement**: Optionally enhances answers using DeepSeek model for improved quality and comprehensiveness

## Setup

### Prerequisites

- Python 3.8 or higher
- Azure AI Foundry project with a Bing connection
- (Optional) Azure DeepSeek deployment for enhancement

### Installation

1. Clone the repository and navigate to the backend directory:

```bash
cd finopshubs-ui/backend
```

2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file and edit it with your settings:

```bash
cp .env.example .env
```

4. Edit the `.env` file with your Azure AI Foundry and DeepSeek settings

5. Run the environment fixer to ensure all settings are properly configured:

```bash
python fix_env.py
```

6. For DeepSeek enhancement, install the required package and test the connection:

```bash
python install_deepseek.py
```

7. Test all connections:

```bash
python test_connections.py
```

### Environment Variables

#### Azure AI Foundry (Required for Bing integration)
- `PROJECT_CONNECTION_STRING`: Your Azure AI Foundry project connection string
- `MODEL_DEPLOYMENT_NAME`: The model deployment to use (e.g., "gpt-4o")
- `BING_CONNECTION_NAME`: The name of your Bing connection in Azure AI Foundry

#### DeepSeek Enhancement (Optional)
- `AZURE_INFERENCE_ENDPOINT`: Your Azure Inference endpoint URL
- `AZURE_INFERENCE_KEY`: Your Azure Inference API key
- `MODEL_NAMEDS`: The DeepSeek model name (default: "DeepSeek-R1")

#### Feature Flags
- `MOCK_MODE`: Set to "true" to use simulated responses instead of real API calls
- `FINOPS_ENHANCEMENT_ENABLED`: Set to "true" to enable DeepSeek enhancement
- `FINOPS_DEBUG_MODE`: Set to "true" to enable detailed logging

## Running the Server

Use the start script to run the server:

```bash
./start_server.sh
```

Or manually:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at http://localhost:8000.

## Troubleshooting

### Missing Packages

If you see errors about missing packages, install them with:

```bash
pip install azure-ai-projects azure-identity azure-ai-inference
```

### DeepSeek Connection Issues

If you're having issues connecting to DeepSeek:

1. Verify your `AZURE_INFERENCE_ENDPOINT` and `AZURE_INFERENCE_KEY` are correct
2. Run the DeepSeek tester to try different model names:

```bash
python install_deepseek.py
```

3. Update your `.env` file with the working model name

### Azure AI Foundry Connection Issues

If you can't connect to Azure AI Foundry:

1. Verify your `PROJECT_CONNECTION_STRING` is correct and not expired
2. Ensure that `BING_CONNECTION_NAME` matches exactly with your connection in Azure AI Foundry
3. Check that your Azure credentials have the proper permissions
4. Verify that `MODEL_DEPLOYMENT_NAME` refers to an active deployment

## Mock Mode

If you don't have access to Azure AI Foundry or are experiencing issues, you can use mock mode by setting `MOCK_MODE=true` in your `.env` file or running:

```bash
python update_config.py --mock-mode true
```

This will use simulated responses instead of making real API calls.

## Debug Mode

To enable detailed logging for troubleshooting, set `FINOPS_DEBUG_MODE=true` in your `.env` file or run:

```bash
python update_config.py --debug true
```

This will output detailed logs about the Bing search process and agent execution. 