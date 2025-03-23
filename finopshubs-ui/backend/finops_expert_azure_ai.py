"""
FinOps Expert with Azure AI Foundry and Bing Grounding

This module provides FinOps expertise using Azure AI Foundry and Bing Search integration.
It leverages the Azure AI Projects SDK to create an agent that can perform web searches
and provide grounded answers to FinOps-related questions.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Try to import Azure AI Projects SDK
try:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import MessageRole, BingGroundingTool
    from azure.identity import DefaultAzureCredential
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    logger.warning("Azure AI Projects SDK not installed. Real-time search will be unavailable.")
    logger.warning("Install with: pip install azure-ai-projects azure-identity")

# Try to import DeepSeek SDK for enhancement
try:
    from azure.ai.inference import InferenceClient
    DEEPSEEK_AVAILABLE = True
    logger.info("DeepSeek enhancement is available via Azure AI Inference SDK")
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logger.warning("DeepSeek enhancement not available. Install azure-ai-inference package")

# Global configurations
MOCK_MODE = os.environ.get("FINOPS_MOCK_MODE", "False").lower() in ("true", "1", "t")
ENHANCEMENT_ENABLED = os.environ.get("FINOPS_ENHANCEMENT_ENABLED", "True").lower() in ("true", "1", "t")

def load_env_file():
    """Load environment variables from .env file"""
    load_dotenv()
    
    # Check if we have the required keys for Azure AI Foundry
    foundry_keys = ["PROJECT_CONNECTION_STRING", "MODEL_DEPLOYMENT_NAME", "BING_CONNECTION_NAME"]
    deepseek_keys = ["AZURE_ENDPOINT", "AZURE_API_KEY"]
    
    # If we're in mock mode, don't check for Azure AI Foundry keys
    if MOCK_MODE:
        logger.info("Running in mock mode, skipping Azure AI Foundry key checks")
        return True
    
    missing_foundry_keys = []
    for key in foundry_keys:
        if not os.environ.get(key):
            missing_foundry_keys.append(key)
    
    if missing_foundry_keys:
        logger.warning(f"Missing required Azure AI Foundry keys: {', '.join(missing_foundry_keys)}")
        logger.warning("Real-time search will be unavailable")
        return False
    
    # If enhancement is enabled, check for DeepSeek keys
    if ENHANCEMENT_ENABLED:
        missing_deepseek_keys = []
        for key in deepseek_keys:
            if not os.environ.get(key):
                missing_deepseek_keys.append(key)
        
        if missing_deepseek_keys:
            logger.warning(f"Missing required DeepSeek keys: {', '.join(missing_deepseek_keys)}")
            logger.warning("Answer enhancement will be unavailable")
        else:
            logger.info("All required DeepSeek keys found")
    
    logger.info("All required Azure AI Foundry keys found")
    return True

def test_azure_ai_connection() -> bool:
    """Test if the Azure AI Foundry connection works"""
    if MOCK_MODE:
        logger.info("Running in mock mode, skipping Azure AI Foundry connection test")
        return True
        
    if not AZURE_SDK_AVAILABLE:
        logger.warning("Azure AI Projects SDK not installed, skipping connection test")
        return False
    
    # Check for required environment variables
    if not load_env_file():
        return False
    
    try:
        # Create the project client to test the connection
        logger.info("Testing Azure AI Foundry connection...")
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        )
        
        # Try to get the Bing connection
        bing_connection_name = os.environ["BING_CONNECTION_NAME"]
        logger.info(f"Testing Bing connection: {bing_connection_name}")
        bing_connection = project_client.connections.get(
            connection_name=bing_connection_name
        )
        
        if bing_connection and bing_connection.id:
            logger.info(f"Azure AI Foundry connection test successful")
            return True
        else:
            logger.warning(f"Could not get Bing connection {bing_connection_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing Azure AI Foundry connection: {str(e)}")
        return False

def test_deepseek_connection() -> bool:
    """Test if the DeepSeek enhancement connection works"""
    if not ENHANCEMENT_ENABLED or not DEEPSEEK_AVAILABLE:
        logger.info("DeepSeek enhancement disabled or SDK not available, skipping test")
        return False
    
    try:
        # Get required variables
        endpoint = os.environ.get("AZURE_ENDPOINT")
        api_key = os.environ.get("AZURE_API_KEY")
        
        if not endpoint or not api_key:
            logger.warning("Missing DeepSeek credentials, skipping test")
            return False
        
        # Create client to test connection
        logger.info("Testing DeepSeek connection...")
        inference_client = InferenceClient(endpoint=endpoint, api_key=api_key)
        
        # Try a simple test to check if the connection works
        test_prompt = "What is FinOps? Respond in one sentence."
        
        logger.info("Sending test request to DeepSeek model...")
        response = inference_client.get_chat_completions(
            deployment_name="deepseek-ai-r1", 
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=50,
            temperature=0.5
        )
        
        if response and response.choices and len(response.choices) > 0:
            logger.info("DeepSeek connection test successful")
            return True
        else:
            logger.warning("DeepSeek connection test failed - no valid response")
            return False
            
    except Exception as e:
        logger.error(f"Error testing DeepSeek connection: {str(e)}")
        return False

def get_simulated_search_results(question: str) -> List[Dict[str, Any]]:
    """Return simulated search results for testing purposes"""
    logger.info(f"Generating simulated search results for question: {question}")
    
    # Simple mapping of keywords to simulated sources
    sources = [
        {
            "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/",
            "title": "What is FinOps? - Microsoft Learn",
            "snippet": "FinOps, or cloud financial management, is the discipline of managing cloud costs. "
                     "It involves tracking cloud spend, optimizing usage, and ensuring accountability.",
            "date": "2023-10-15"
        },
        {
            "url": "https://www.finops.org/introduction/what-is-finops/",
            "title": "What is FinOps? - FinOps Foundation",
            "snippet": "FinOps is an operational framework and cultural practice that brings together technology, "
                     "finance, and business teams to manage cloud costs effectively.",
            "date": "2023-09-01"
        },
        {
            "url": "https://azure.microsoft.com/en-us/blog/best-practices-for-cloud-cost-optimization/",
            "title": "Best Practices for Cloud Cost Optimization - Azure Blog",
            "snippet": "Learn how to optimize your Azure costs with right-sizing, scheduling, autoscaling, "
                     "and other proven strategies for cloud cost management.",
            "date": "2023-08-20"
        }
    ]
    
    return sources

def enhance_with_deepseek(question: str, bing_result: Dict[str, Any]) -> str:
    """
    Enhance the answer using DeepSeek model
    
    Args:
        question: The original user question
        bing_result: The result from the Bing search, containing answer and sources
        
    Returns:
        Enhanced answer text
    """
    if not ENHANCEMENT_ENABLED or not DEEPSEEK_AVAILABLE:
        logger.info("DeepSeek enhancement disabled or unavailable, returning original answer")
        return bing_result.get("answer", "")
    
    try:
        # Get required variables
        endpoint = os.environ.get("AZURE_ENDPOINT")
        api_key = os.environ.get("AZURE_API_KEY")
        
        if not endpoint or not api_key:
            logger.warning("Missing DeepSeek credentials, returning original answer")
            return bing_result.get("answer", "")
        
        # Create client
        logger.info("Enhancing answer with DeepSeek model...")
        inference_client = InferenceClient(endpoint=endpoint, api_key=api_key)
        
        # Extract answer and sources
        original_answer = bing_result.get("answer", "")
        citations = bing_result.get("citations", [])
        
        # Build reference text from citations
        references = ""
        for citation in citations:
            title = citation.get("title", "")
            url = citation.get("url", "")
            references += f"- {title}: {url}\n"
        
        # Create the enhancement prompt
        prompt = f"""You are a FinOps expert enhancing an answer about cloud financial management. 
Your goal is to improve the following answer by:
1. Making it more comprehensive and actionable
2. Structuring it clearly with headings
3. Including concrete examples where helpful
4. Ensuring all information is accurate based on the provided sources
5. Maintaining the same key points and sources as the original answer

Original question: {question}

Original answer: 
{original_answer}

Available sources:
{references}

Please provide an enhanced version of the answer that maintains all factual information
but improves clarity, comprehensiveness, and actionability.
"""
        
        logger.info("Sending enhancement request to DeepSeek model...")
        response = inference_client.get_chat_completions(
            deployment_name="deepseek-ai-r1", 
            messages=[
                {"role": "system", "content": "You are a FinOps expert assistant helping enhance answers about cloud financial management."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.5
        )
        
        if response and response.choices and len(response.choices) > 0:
            enhanced_answer = response.choices[0].message.content
            logger.info("Successfully enhanced answer with DeepSeek")
            return enhanced_answer
        else:
            logger.warning("DeepSeek enhancement failed - no valid response")
            return original_answer
            
    except Exception as e:
        logger.error(f"Error enhancing answer with DeepSeek: {str(e)}")
        return bing_result.get("answer", "")

def finops_expert_with_azure_ai(question: str, conversation_history: Optional[List[Dict]] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a FinOps question using Azure AI Foundry with Bing grounding
    
    Args:
        question: The user's FinOps-related question
        conversation_history: Optional conversation history for context
        config: Optional configuration parameters
            - enhancement_enabled: Whether to enhance the answer with DeepSeek (default: True)
            - use_mock_mode: Override the global MOCK_MODE setting
            
    Returns:
        Dictionary containing the answer, citations, and metadata
    """
    logger.info(f"Processing question via FinOps Expert with Azure AI: {question}")
    
    # Initialize conversation history and config if not provided
    if conversation_history is None:
        conversation_history = []
    
    if config is None:
        config = {}
    
    # Check if config overrides the global settings
    use_mock = config.get("use_mock_mode", MOCK_MODE)
    enhancement = config.get("enhancement_enabled", ENHANCEMENT_ENABLED)
    
    logger.info(f"Mock mode: {use_mock}, Enhancement enabled: {enhancement}")
    
    # Check if we should use mock mode
    if use_mock or not AZURE_SDK_AVAILABLE or not load_env_file():
        logger.info("Using mock mode for FinOps expert")
        
        # Simplified mock response
        mock_answer = {
            "answer": "FinOps (Cloud Financial Operations) is a framework for managing cloud costs effectively. "
                     "It involves tracking cloud spend, optimizing usage, and ensuring accountability across teams. "
                     "By implementing FinOps practices, organizations can better control their cloud spending while "
                     "maintaining operational efficiency.",
            "citations": [
                {"number": "1", "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/", 
                 "title": "What is FinOps? - Microsoft Learn"},
                {"number": "2", "url": "https://www.finops.org/introduction/what-is-finops/", 
                 "title": "What is FinOps? - FinOps Foundation"}
            ],
            "formatted_answer": "FinOps (Cloud Financial Operations) is a framework for managing cloud costs effectively. "
                               "It involves tracking cloud spend, optimizing usage, and ensuring accountability across teams. "
                               "By implementing FinOps practices, organizations can better control their cloud spending while "
                               "maintaining operational efficiency.\n\n"
                               "Sources:\n"
                               "[1] [What is FinOps? - Microsoft Learn](https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/)\n"
                               "[2] [What is FinOps? - FinOps Foundation](https://www.finops.org/introduction/what-is-finops/)"
        }
        
        return mock_answer
    
    try:
        # Create the project client
        logger.info("Creating AI Project client")
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        )
        
        # Get the Bing connection
        bing_connection_name = os.environ["BING_CONNECTION_NAME"]
        logger.info(f"Getting Bing connection: {bing_connection_name}")
        bing_connection = project_client.connections.get(
            connection_name=bing_connection_name
        )
        conn_id = bing_connection.id
        logger.info(f"Bing connection ID: {conn_id}")
        
        # Initialize Bing grounding tool
        bing = BingGroundingTool(connection_id=conn_id)
        
        # Create the agent with Bing tool
        with project_client:
            model_name = os.environ["MODEL_DEPLOYMENT_NAME"]
            logger.info(f"Creating agent with model: {model_name}")
            
            # Define the system prompt for the agent
            finops_instructions = """You are a FinOps expert assistant specialized in cloud financial management. 
            Your goal is to help users understand cloud cost optimization, governance, and FinOps best practices.
            Provide comprehensive, accurate, and practical advice. When answering:
            1. Use the latest information from your web search capabilities
            2. Focus on practical, actionable advice for cloud cost optimization
            3. Consider multi-cloud environments (Azure, AWS, GCP) when relevant
            4. Explain FinOps concepts clearly for both technical and non-technical users
            5. Cite your sources when providing specific recommendations or data
            """
            
            # Create the agent
            agent = project_client.agents.create_agent(
                model=model_name,
                name="finops-assistant",
                instructions=finops_instructions,
                tools=bing.definitions,
                headers={"x-ms-enable-preview": "true"},
            )
            
            logger.info(f"Created agent, ID: {agent.id}")
            
            # Create a thread for the conversation
            thread = project_client.agents.create_thread()
            logger.info(f"Created thread, ID: {thread.id}")
            
            # Add conversation history if provided
            if conversation_history and len(conversation_history) > 0:
                logger.info(f"Adding {len(conversation_history)} messages from conversation history")
                for message in conversation_history:
                    role = MessageRole.USER if message.get("role") == "user" else MessageRole.AGENT
                    project_client.agents.create_message(
                        thread_id=thread.id,
                        role=role,
                        content=message.get("content", "")
                    )
            
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
                error_msg = run.last_error if run.last_error else "Unknown error"
                logger.error(f"Run failed: {error_msg}")
                return {
                    "answer": f"I encountered an error while trying to answer your question: {error_msg}",
                    "citations": [],
                    "formatted_answer": f"I encountered an error while trying to answer your question: {error_msg}"
                }
            
            # Get the agent's response
            response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
                MessageRole.AGENT
            )
            
            if response_message:
                # Build the response text
                response_text = ""
                for text_message in response_message.text_messages:
                    response_text += f"{text_message.text.value}\n\n"
                response_text = response_text.strip()
                
                # Prepare citations
                citations = []
                for i, annotation in enumerate(response_message.url_citation_annotations):
                    citation = {
                        "number": str(i+1),  # Convert to string to match expected type
                        "url": annotation.url_citation.url,
                        "title": annotation.url_citation.title
                    }
                    citations.append(citation)
                
                # Clean up resources first before doing enhancement
                # This is important to avoid keeping resources hanging
                logger.info("Cleaning up Azure AI Foundry resources")
                project_client.agents.delete_agent(agent.id)
                
                # Prepare the initial result
                result = {
                    "answer": response_text,
                    "citations": citations
                }
                
                # Enhance with DeepSeek if enabled
                if enhancement and DEEPSEEK_AVAILABLE:
                    logger.info("Enhancing answer with DeepSeek...")
                    enhanced_answer = enhance_with_deepseek(question, result)
                    result["answer"] = enhanced_answer
                
                # Format the answer with markdown citations
                formatted_answer = result["answer"]
                if citations:
                    formatted_answer += "\n\nSources:\n"
                    for citation in citations:
                        formatted_answer += f"[{citation['number']}] [{citation['title']}]({citation['url']})\n"
                
                result["formatted_answer"] = formatted_answer.strip()
                return result
            else:
                # Clean up resources
                logger.info("Cleaning up Azure AI Foundry resources")
                project_client.agents.delete_agent(agent.id)
                
                logger.warning("No response received from the agent")
                return {
                    "answer": "I couldn't generate a response to your question. Please try again.",
                    "citations": [],
                    "formatted_answer": "I couldn't generate a response to your question. Please try again."
                }
                
    except Exception as e:
        logger.error(f"Error using Azure AI Foundry: {str(e)}")
        return {
            "answer": f"I encountered an error while processing your question: {str(e)}",
            "citations": [],
            "formatted_answer": f"I encountered an error while processing your question: {str(e)}"
        }

# Test the module if run directly
if __name__ == "__main__":
    print("="*50)
    print("FinOps Expert with Azure AI Foundry")
    print("="*50)
    print(f"Mock Mode: {MOCK_MODE}")
    print(f"Enhancement Enabled: {ENHANCEMENT_ENABLED}")
    
    # Test the connections
    if not MOCK_MODE:
        print(f"Testing Azure AI Foundry connection: {test_azure_ai_connection()}")
    
    if ENHANCEMENT_ENABLED:
        print(f"Testing DeepSeek connection: {test_deepseek_connection()}")
    
    print("-"*50)
    
    # Test question
    test_question = "What is FinOps and how can it help reduce cloud costs?"
    print(f"Test Question: {test_question}")
    
    # Process the question
    answer = finops_expert_with_azure_ai(test_question)
    
    print("-"*50)
    print("Answer:")
    print(answer["formatted_answer"])
    print("="*50) 