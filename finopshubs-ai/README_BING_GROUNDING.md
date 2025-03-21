# FinOps Expert with Bing Grounding

This script implements a comprehensive FinOps expert using Azure AI Project Agents with Bing grounding capability to search the web for the latest information on FinOps principles, practices, and cloud cost management across various providers.

## Key Features

- Uses Bing grounding to search the web for up-to-date information on all FinOps topics
- Provides answers with citations to source materials
- Covers the full spectrum of FinOps principles and practices, not just the Microsoft FinOps Toolkit
- Simple interface for asking FinOps-related questions
- Includes test functions to verify Bing grounding functionality

## Scope of Knowledge

The agent can provide guidance on:

- General FinOps principles and frameworks
- Cloud cost optimization strategies across various providers
- Microsoft FinOps Toolkit resources and implementations
- Industry best practices for financial operations in the cloud
- Latest trends and developments in the FinOps field

## Setup

1. Ensure you have the following environment variables set:
   - PROJECT_CONNECTION_STRING - The project connection string from Azure AI Foundry
   - BING_CONNECTION_NAME - The name of your Bing connection (or GROUNDING_WITH_BING_CONNECTION_NAME as fallback)
   - MODEL_DEPLOYMENT_NAME - The deployment name for your model (defaults to gpt-4o-0513)

2. Install the required dependencies:
   ```
   pip install azure-ai-projects azure-identity python-dotenv
   ```

## Usage

Run the script directly:

```
python finops_expert_with_bing_grounding.py
```

Choose from the following options:
1. Ask a FinOps question with Bing grounding
2. Run basic Bing test (using the sample code pattern)
3. Exit

## Implementation Details

The implementation follows the official Azure AI Project sample for Bing grounding, with specific adaptations for comprehensive FinOps questions. Key aspects of the implementation:

1. **Agent Creation**: Creates an agent with Bing grounding tools and enhanced FinOps instructions covering all aspects of FinOps
2. **Direct Question Processing**: Uses a simplified approach where questions are passed directly to the agent
3. **Citation Extraction**: Extracts URL citations from the agent's response rather than from run steps
4. **Resource Cleanup**: Properly cleans up agents after use to manage resources

## How Bing Grounding Works

1. The agent is created with the Bing grounding tool connected via your Azure AI Foundry project
2. When a question is asked, the agent automatically decides when to search the web using Bing
3. The Bing search results are processed by the agent and incorporated into its response
4. Citations to web sources are included in the response as URL annotations
5. The script extracts these citations and formats them as part of the answer

## Troubleshooting

If you encounter issues with Bing grounding:

1. Verify your environment variables are set correctly
2. Ensure you're using a compatible model (gpt-4o-0513 is recommended)
3. Run the test function to validate Bing grounding functionality
4. Check your Azure AI Foundry connection permissions
5. Verify your Bing connection is active in Azure AI Foundry

## Key Code Components

- **create_finops_bing_agent()**: Creates an agent with the Bing grounding tool and comprehensive FinOps instructions
- **ask_finops_question_with_bing()**: Processes questions using the Bing-grounded agent
- **finops_expert_with_bing()**: Main function that orchestrates the process and formats results
- **test_bing_sample()**: Test function that follows the official sample to verify functionality

## Azure Metrics

If you want to verify Bing usage, you can check the metrics for your Bing connection in the Azure portal. Look for:
- Connection call counts
- API usage patterns
- Request success/failure rates

## Reference

This implementation is based on the official Microsoft sample for Bing grounding:
https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding 