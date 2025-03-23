"""
DESCRIPTION:
    This sample demonstrates how to connect to Azure AI Foundry for FinOps expertise 
    with Bing grounding capability.

USAGE:
    python sample_finops_with_azure.py

    Before running the sample:
    1. Create a new Azure AI Foundry project with a deployed model
    2. Create a Bing Search resource in Azure and connect it to your AI Foundry project
    3. Set these environment variables with your own values:
       - PROJECT_CONNECTION_STRING - From the overview page of your Azure AI Foundry project
       - MODEL_DEPLOYMENT_NAME - From the "Models + endpoints" tab in your project
       - BING_CONNECTION_NAME - From the "Connected resources" tab in your project
"""

import os
import logging
from dotenv import load_dotenv

# Try to import the Azure AI Projects SDK - if not installed, display error message
try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import MessageRole, BingGroundingTool
    from azure.identity import DefaultAzureCredential
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    print("Azure AI Projects SDK not installed. Please install with:")
    print("pip install azure-ai-projects azure-identity")
    
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def load_env_vars():
    """Load environment variables and check required variables"""
    load_dotenv()
    
    required_vars = [
        "PROJECT_CONNECTION_STRING",
        "MODEL_DEPLOYMENT_NAME",
        "BING_CONNECTION_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or environment")
        return False
    
    logger.info("All required environment variables found")
    return True

def run_finops_with_bing_grounding(question):
    """Run a FinOps query with Bing grounding through Azure AI Foundry"""
    
    if not AZURE_SDK_AVAILABLE:
        logger.error("Azure AI Projects SDK not installed")
        return "Error: Azure AI Projects SDK not installed. Please install with: pip install azure-ai-projects azure-identity"
    
    if not load_env_vars():
        return "Error: Missing required environment variables. Check the logs for details."
    
    try:
        # Create the project client
        logger.info("Creating AI Project client")
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        )
        
        # Get the Bing connection
        logger.info(f"Getting Bing connection: {os.environ['BING_CONNECTION_NAME']}")
        bing_connection = project_client.connections.get(
            connection_name=os.environ["BING_CONNECTION_NAME"]
        )
        conn_id = bing_connection.id
        logger.info(f"Bing connection ID: {conn_id}")
        
        # Initialize Bing grounding tool
        bing = BingGroundingTool(connection_id=conn_id)
        
        # Create the agent with Bing tool
        with project_client:
            logger.info(f"Creating agent with model: {os.environ['MODEL_DEPLOYMENT_NAME']}")
            agent = project_client.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"],
                name="finops-assistant",
                instructions="""You are a FinOps expert assistant. 
                Your goal is to help users understand cloud financial management, cost optimization, 
                and FinOps best practices. Use the latest information available from your 
                Bing search capabilities to provide accurate and up-to-date answers.""",
                tools=bing.definitions,
                headers={"x-ms-enable-preview": "true"},
            )
            
            logger.info(f"Created agent, ID: {agent.id}")
            
            # Create a thread for the conversation
            thread = project_client.agents.create_thread()
            logger.info(f"Created thread, ID: {thread.id}")
            
            # Send the user's question
            logger.info(f"Sending question: {question}")
            message = project_client.agents.create_message(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=question,
            )
            
            # Run the agent to process the question
            logger.info("Processing the question with the agent")
            run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
            logger.info(f"Run finished with status: {run.status}")
            
            if run.status == "failed":
                logger.error(f"Run failed: {run.last_error}")
                return f"Error: The agent encountered an error: {run.last_error}"
            
            # Get the agent's response
            response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
                MessageRole.AGENT
            )
            
            if response_message:
                # Build the response text
                response_text = ""
                for text_message in response_message.text_messages:
                    response_text += f"{text_message.text.value}\n\n"
                
                # Add citations if available
                citations = []
                for annotation in response_message.url_citation_annotations:
                    citation = f"[{annotation.url_citation.title}]({annotation.url_citation.url})"
                    citations.append(citation)
                
                if citations:
                    response_text += "\n\nSources:\n"
                    response_text += "\n".join(citations)
                
                # Clean up resources
                project_client.agents.delete_agent(agent.id)
                logger.info("Deleted agent")
                
                return response_text
            else:
                project_client.agents.delete_agent(agent.id)
                logger.info("Deleted agent")
                return "No response received from the agent."
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"

def main():
    print("="*50)
    print("FinOps Expert with Azure AI Foundry and Bing Grounding")
    print("="*50)
    
    if not AZURE_SDK_AVAILABLE:
        print("Please install the required packages:")
        print("pip install azure-ai-projects azure-identity")
        return
    
    if not load_env_vars():
        print("Please set the required environment variables in your .env file")
        return
    
    # Test question
    question = "What are the latest blog articles about FOCUS at Microsoft? Can you provide a summary of the articles?"
    print(f"Question: {question}")
    print("-"*50)
    
    answer = run_finops_with_bing_grounding(question)
    print("Answer:")
    print(answer)
    print("="*50)

if __name__ == "__main__":
    main()