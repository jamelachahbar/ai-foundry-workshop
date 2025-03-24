"""
FinOps Expert with Azure AI Foundry and Bing Grounding

This module provides FinOps expertise using Azure AI Foundry and Bing Search integration.
It leverages the Azure AI Projects SDK to create an agent that can perform web searches
and provide grounded answers to FinOps-related questions.
"""

import os
import logging
import json
import requests
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from finops_insights_helpers import extract_insights_from_sources
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

# # Try to import DeepSeek SDK for enhancement
try:
    from azure.ai.inference import InferenceClient
    DEEPSEEK_AVAILABLE = True
    logger.info("DeepSeek enhancement is available via Azure AI Inference SDK")
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logger.warning("DeepSeek enhancement not available. Install azure-ai-inference package")

# Global configurations
ENHANCEMENT_ENABLED = os.environ.get("FINOPS_ENHANCEMENT_ENABLED", "True").lower() in ("true", "1", "t")

# Load environment variables
load_dotenv()

# Initialize DeepSeek client
try:
    endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
    key = os.getenv("AZURE_INFERENCE_KEY")
    model_name = os.getenv("MODEL_NAMEDS", "DeepSeek-R1")

    if not endpoint or not key:
        raise ValueError("Missing required environment variables: AZURE_INFERENCE_ENDPOINT or AZURE_INFERENCE_KEY")

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
        headers={"x-ms-model-mesh-model-name": model_name}
    )
    logger.info(f"✅ DeepSeek client initialized | Model: {model_name}")
    ENHANCEMENT_ENABLED = True
except Exception as e:
    logger.error(f"❌ DeepSeek client initialization failed: {str(e)}")
    client = None
    ENHANCEMENT_ENABLED = False

def load_env_file():
    """Load environment variables from .env file"""
    load_dotenv()
    
    # Check if we have the required keys for Azure AI Foundry
    foundry_keys = ["PROJECT_CONNECTION_STRING", "MODEL_DEPLOYMENT_NAME", "BING_CONNECTION_NAME"]
    deepseek_keys = ["AZURE_ENDPOINT", "AZURE_API_KEY"]
    
    
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
            deployment_name=os.environ["MODEL_NAMEDS"],
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=1000,
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


def get_grounded_sources_with_foundry(query: str) -> List[Dict[str, Any]]:
    """
    Use Azure AI Foundry agent with Bing grounding to get grounded responses.
    Returns a list of sources (URL, title, snippet).
    """
    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import MessageRole, BingGroundingTool
        from azure.identity import DefaultAzureCredential

        logger.info("🔍 Using Azure AI Foundry with Bing Grounding for query: %s", query)

        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=os.environ["PROJECT_CONNECTION_STRING"],
        )

        # Get Bing connection
        bing_connection = project_client.connections.get(connection_name=os.environ["BING_CONNECTION_NAME"])
        bing_tool = BingGroundingTool(connection_id=bing_connection.id)

        # Create temporary agent
        agent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="finops-bing-agent",
            instructions="You are a FinOps expert. Use Bing grounding to provide real-time insights.",
            tools=bing_tool.definitions,
            headers={"x-ms-enable-preview": "true"},
            content_type="text/plain",
            metadata={"source": "finops-bing-agent"},
            description="FinOps expert agent using Bing grounding"
        )

        thread = project_client.agents.create_thread()
        project_client.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=query,
        )

        run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)

        logger.info("Current run status: %s", run.status)

        if str(run.status).lower() not in ["succeeded", "completed"]:
            logger.warning("Agent run did not finish successfully: %s", run.status)
            project_client.agents.delete_agent(agent.id)
            return []


        response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
            MessageRole.AGENT
        )

        sources = []

        if response_message:
            # Inline citations from text messages
            for text_msg in getattr(response_message, "text_messages", []):
                for citation in getattr(text_msg, "citations", []):
                    if hasattr(citation, "url_citation"):
                        sources.append({
                            "title": citation.url_citation.title,
                            "url": citation.url_citation.url,
                            "description": getattr(citation.url_citation, "snippet", ""),
                            "is_valid": True
                        })

            # Explicit citations
            for annotation in getattr(response_message, "url_citation_annotations", []):
                sources.append({
                    "title": annotation.url_citation.title,
                    "url": annotation.url_citation.url,
                    "description": getattr(annotation.url_citation, "snippet", ""),
                    "is_valid": True
                })
        logger.info("🧠 Agent raw response message:")
        if response_message:
            for text_msg in getattr(response_message, "text_messages", []):
                logger.info(f"- Message content: {text_msg.text.value}")
                if hasattr(text_msg, "citations"):
                    logger.info(f"  ↪ Citations: {text_msg.citations}")
            if response_message.url_citation_annotations:
                logger.info(f"📌 Found {len(response_message.url_citation_annotations)} explicit citations.")
            else:
                logger.warning("⚠️ No explicit citations found in url_citation_annotations.")

        # Cleanup
        project_client.agents.delete_agent(agent.id)

        if not sources:
            logger.warning("⚠️ No grounded sources found from Bing grounding.")
        else:
            logger.info(f"✅ Retrieved {len(sources)} sources from Bing grounding.")

        return sources

    except Exception as e:
        logger.exception("❌ Exception during Bing grounding via Foundry")
        return []

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
        endpoint = os.environ.get("AZURE_INFERENCE_ENDPOINT")
        api_key = os.environ.get("AZURE_INFERENCE_KEY")
        
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
            deployment_name="DeepSeek-R1", 
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


def finops_expert_with_azure_ai(question: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
    """
    Get expert FinOps advice using DeepSeek and Bing search
    
    Args:
        question: The user's question
        conversation_history: Optional conversation history
        
    Returns:
        Dictionary containing answer, citations, and formatted answer
    """
    if not client:
        raise ValueError("DeepSeek client not initialized")
        
    try:
        # First, get relevant sources from Bing
        sources = get_grounded_sources_with_foundry(question)

        
        if not sources:
            logger.warning("No sources found from Bing search")
            return {
                "answer": "I couldn't find any relevant information about this FinOps topic. Please try rephrasing your question.",
                "citations": [],
                "formatted_answer": "No relevant information found."
            }
            
        # Extract insights from sources
        insights = extract_insights_from_sources(sources, question)
        
        # Create system prompt
        system_prompt = """You are a Microsoft FinOps toolkit expert. Your goal is to provide clear, actionable advice about cloud financial management.
When answering:
1. Be specific and practical
2. Include Azure-specific details when relevant
3. Reference sources to support your points
4. Structure your response with clear sections
5. Focus on real-world implementation"""

        # Create user prompt with context
        user_prompt = f"""Based on the following sources:

{insights}

Please provide a comprehensive answer to: {question}

Structure your response with clear sections and include specific, actionable recommendations."""

        # Get response from DeepSeek
        response = client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt)
            ],
            temperature=0.3,
            max_tokens=2048
        )
        
        answer = response.choices[0].message.content
        
        # Format citations
        citations = []
        for i, source in enumerate(sources[:5], 1):  # Limit to top 5 sources
            citation = {
                "number": str(i),
                "title": source["title"],
                "url": source["url"]
            }
            citations.append(citation)
            
        # Format the answer with citations
        formatted_answer = f"{answer}\n\n## Sources\n"
        for citation in citations:
            formatted_answer += f"\n[{citation['title']}]({citation['url']})"
            
        return {
            "answer": answer,
            "citations": citations,
            "formatted_answer": formatted_answer
        }
        
    except Exception as e:
        logger.error(f"Error in finops_expert_with_azure_ai: {str(e)}")
        raise

# Test the module if run directly
if __name__ == "__main__":
    print("="*50)
    print("FinOps Expert with Azure AI Foundry")
    print("="*50)
    print(f"Enhancement Enabled: {ENHANCEMENT_ENABLED}")
    
    # Test the connections
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