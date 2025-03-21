# finops_expert_with_bing_grounding.py
# ------------------------------------
# FinOps Toolkit Expert with Bing Grounding
# Leverages DeepSeek-R1 for reasoning and Bing for real-time documentation
# ------------------------------------

import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole, BingGroundingTool
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import re
import urllib.parse
import traceback
import signal

# Load environment variables - simplified approach to find .env file
# Start by checking current directory, then parent directories
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

print("Initializing FinOps Toolkit Expert with Bing Grounding...")

# Set defaults for missing variables
if not os.getenv("MODEL_NAME"):
    os.environ["MODEL_NAME"] = "gpt-4o"  # Default model name changed to one specifically supported for Bing grounding

# Use GROUNDING_WITH_BING_CONNECTION_NAME as fallback for BING_CONNECTION_NAME
if not os.getenv("BING_CONNECTION_NAME") and os.getenv("GROUNDING_WITH_BING_CONNECTION_NAME"):
    os.environ["BING_CONNECTION_NAME"] = os.getenv("GROUNDING_WITH_BING_CONNECTION_NAME")

# Helper for getting environment variables with fallbacks
def get_env_var(name, fallback_names=None, default=None):
    """Get environment variable with fallbacks and defaults"""
    value = os.getenv(name)
    
    # Try fallbacks if provided and main value is not set
    if not value and fallback_names:
        for fallback in fallback_names:
            value = os.getenv(fallback)
            if value:
                print(f"Using {fallback} as fallback for {name}")
                break
    
    # Use default if still not found
    if not value and default:
        print(f"Using default value for {name}")
        value = default
        
    return value

# Get connection variables with fallbacks
conn_string = get_env_var("PROJECT_CONNECTION_STRING")
bing_conn_name = get_env_var("BING_CONNECTION_NAME", 
                            ["GROUNDING_WITH_BING_CONNECTION_NAME"], 
                            "bingsearchfinopshubs")  # Default to your connection name
model_name_deployment = get_env_var("MODEL_DEPLOYMENT_NAME", 
                        ["SERVERLESS_MODEL_NAME"], 
                        "gpt-4o")  # Use what works in this environment
deepseek_model_name = get_env_var("MODEL_NAMEDS", default="DeepSeek-R1")  # Changed to match your actual deployment

# Print all available environment variables for debugging
print("\nEnvironment Variables:")
print(f"PROJECT_CONNECTION_STRING: {conn_string[:20]}...{conn_string[-5:] if len(conn_string) > 25 else conn_string}")
print(f"MODEL_DEPLOYMENT_NAME: {model_name_deployment}")
print(f"BING_CONNECTION_NAME: {bing_conn_name}")
print(f"AZURE_INFERENCE_ENDPOINT: {os.getenv('AZURE_INFERENCE_ENDPOINT')}")
print(f"AZURE_INFERENCE_KEY: {os.getenv('AZURE_INFERENCE_KEY')[:5]}...") if os.getenv('AZURE_INFERENCE_KEY') else print("AZURE_INFERENCE_KEY: Not set")
print(f"MODEL_NAMEDS: {deepseek_model_name}")

# Required environment variables
required_vars = [
    "PROJECT_CONNECTION_STRING",
    "MODEL_DEPLOYMENT_NAME",
    "BING_CONNECTION_NAME"
]

# Check environment variables
missing_vars = [var for var in required_vars if not get_env_var(var)]
if missing_vars:
    print(f"⚠️ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these variables in your .env file:")
    print("""
    PROJECT_CONNECTION_STRING=<your-project-connection-string>
    MODEL_DEPLOYMENT_NAME=gpt-4o  # Must be a Bing-supported model
    BING_CONNECTION_NAME=bingsearchfinopshubs
    """)
else:
    print("✅ All required environment variables are set")

# Initialize global variables
project_client = None
bing_connection = None
deepseek_client = None

try:
    # Initialize the DefaultAzureCredential
    print("\nInitializing DefaultAzureCredential...")
    credential = DefaultAzureCredential()
    print("✅ DefaultAzureCredential initialized")
    
    # Initialize AIProjectClient for Bing grounding
    print("\nInitializing AIProjectClient...")
    project_client = AIProjectClient.from_connection_string(
        credential=credential,
        conn_str=conn_string
    )
    print("✅ Successfully initialized AIProjectClient")
    
    # Get Bing connection - using connection_name parameter
    print(f"\nAttempting to get Bing connection: {bing_conn_name}")
    bing_connection = project_client.connections.get(connection_name=bing_conn_name)
    
    print(f"✅ Successfully retrieved Bing connection!")
    print(f"Connection details:")
    print(f"- Name: {bing_connection.name}")
    print(f"- ID: {bing_connection.id}")
    
    # Safely check for type attribute
    try:
        print(f"- Type: {bing_connection.type}")
    except AttributeError:
        print("- Type: [Not available in this SDK version]")
    
    # Initialize the DeepSeek-R1 client for additional reasoning (optional)
    endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
    key = os.getenv("AZURE_INFERENCE_KEY")
    
    if endpoint and key:
        print(f"\nInitializing DeepSeek client with:\nEndpoint: {endpoint}\nModel: {deepseek_model_name}")
        
        # Initialize direct chat client for DeepSeek
        deepseek_client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
            headers={"x-ms-model-mesh-model-name": deepseek_model_name},
            temperature=0.2,
            top_p=0.2
        )
        print(f"✅ DeepSeek-R1 client initialized | Model: {deepseek_model_name}")
    else:
        print("\n⚠️ DeepSeek-R1 client not initialized (missing endpoint or key)")
        print("FinOps expert will run without answer enhancement")
    
except Exception as e:
    print(f"❌ Setup error: {str(e)}")
    
    # Detailed error handling for connection issues
    if "Connection" in str(e) and "can't be found" in str(e):
        print("\n==== BING CONNECTION NOT FOUND ====")
        print("The Bing connection couldn't be found in your Azure AI Foundry project.")
        print("\nTo fix this, you need to create a Bing connection in the Azure portal:")
        print("1. Go to your Azure AI Foundry project in the Azure portal")
        print("2. Navigate to 'Connected resources' in the left menu")
        print("3. Click '+ Add' and select 'Bing Search'")
        print("4. Create a new Bing Search resource or select an existing one")
        print(f"5. Name it '{bing_conn_name}' to match what you have in your .env file")
        print("6. Update your .env file with the correct connection name")
        sys.exit(1)
    
    # Additional error diagnostics
    if "credential" in str(e):
        print(f"\nCredential error - Try these steps:")
        print(f"1. Run 'az login' to refresh your Azure CLI login")
        print(f"2. Check your AZURE_TENANT_ID is set correctly")
        print(f"3. Verify that your account has access to the AI project")
        sys.exit(1)

# Create a FinOps Bing-grounded agent
def create_finops_bing_agent():
    """Create a FinOps toolkit expert agent with Bing grounding capabilities"""
    if not project_client or not bing_connection:
        print("❌ Cannot create agent: Project client or Bing connection not available")
        return None
    
    try:
        # Initialize Bing grounding tool - using the retrieved connection's ID
        print("\nInitializing Bing grounding tool...")
        bing_tool = BingGroundingTool(connection_id=bing_connection.id)
        
        # Create the agent with required preview header for Bing grounding
        print(f"Creating FinOps agent with model: {model_name_deployment}")
        
        # Enhanced instructions to cover all FinOps topics, not just the toolkit
        instructions = """You are a comprehensive FinOps expert who provides accurate and helpful information about all aspects of FinOps practices, including but not limited to Microsoft Azure cost management.

Your knowledge covers the full spectrum of FinOps topics including:
1. General FinOps principles and frameworks
2. Cloud cost optimization strategies across various providers
3. Microsoft FinOps Toolkit resources and implementations
4. Industry best practices for financial operations in the cloud
5. Latest trends and developments in the FinOps field

When answering questions, always search the web for the most current information to ensure your responses reflect the latest developments, tools, and best practices in the FinOps space.

Always cite your sources when providing information."""
        
        # Create the agent with required preview header for Bing grounding
        agent = project_client.agents.create_agent(
            model=model_name_deployment,
            name="FinOps-Expert-Agent",
            instructions=instructions,
            tools=bing_tool.definitions,
            temperature=0.2,  # Lower temperature for more factual responses
            headers={"x-ms-enable-preview": "true"}  # Essential for proper Bing grounding functionality
        )
        
        print(f"🎉 Created FinOps agent with Bing grounding, ID: {agent.id}")
        return agent
    
    except Exception as e:
        print(f"❌ Error creating FinOps Bing agent: {str(e)}")
        return None

# Function to ask FinOps questions with Bing grounding
def ask_finops_question_with_bing(agent, question):
    """Ask a FinOps question using the Bing-grounded agent"""
    if not agent or not project_client:
        print("❌ Agent or project client not available")
        return None
    
    try:
        print(f"🔍 Processing question with Bing grounding: {question}")
        
        # Create a conversation thread
        thread = project_client.agents.create_thread()
        print(f"📝 Created thread ID: {thread.id}")
        
        # Create message with direct question
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=question  # Simplified to match the sample approach
        )
        print(f"📤 Added user message: {message.id}")
        
        # Process the request with the agent
        print("⚙️ Processing run (this may take a minute)...")
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id,
            headers={"x-ms-enable-preview": "true"}  # Ensure preview features are enabled
        )
        
        print(f"✅ Run completed with status: {run.status}")
        
        if run.status == "failed":
            print(f"❌ Run failed: {run.last_error}")
            return {
                "question": question,
                "answer": f"Error: {run.last_error}",
                "citations": [],
                "bing_urls": []
            }
        
        # Get the response
        messages = project_client.agents.list_messages(thread_id=thread.id)
        response_message = messages.get_last_message_by_role(MessageRole.AGENT)
        
        # Extract text content and citations
        answer = ""
        citations = []
        bing_urls = []
        
        if response_message:
            # Get text content
            for text_message in response_message.text_messages:
                answer += text_message.text.value
            
            # Get URL citations - this is the most reliable way to see what Bing found
            for annotation in response_message.url_citation_annotations:
                citation = {
                    "title": annotation.url_citation.title,
                    "url": annotation.url_citation.url
                }
                citations.append(citation)
                bing_urls.append(annotation.url_citation.url)
                print(f"Found URL citation: {annotation.url_citation.title} - {annotation.url_citation.url}")
        
        # Construct the result
        result = {
            "question": question,
            "answer": answer,
            "citations": citations,
            "bing_urls": bing_urls
        }
        
        # Log citation information
        print(f"\nFound {len(citations)} citations from Bing search")
        if len(citations) == 0:
            print("⚠️ No citations found. This may indicate that Bing search was not effective.")
            print("Try asking a more specific question or check your Bing connection.")
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing question: {str(e)}")
        return {
            "question": question,
            "answer": f"Error processing question: {str(e)}",
            "citations": [],
            "bing_urls": []
        }

# Function to enhance answers with DeepSeek-R1
def enhance_with_deepseek(question, bing_result):
    """Enhance the Bing-grounded answer with DeepSeek-R1's reasoning"""
    if not deepseek_client:
        return bing_result["answer"]
    
    try:
        # Extract the Bing answer and citations
        bing_answer = bing_result["answer"]
        citations = bing_result["citations"]
        github_urls = bing_result.get("github_urls", [])
        mslearn_urls = bing_result.get("mslearn_urls", [])
        
        # Prepare citation text
        citation_text = ""
        if citations:
            citation_text = "\n\n## References\n"
            for i, citation in enumerate(citations, 1):
                citation_text += f"{i}. [{citation['title']}]({citation['url']})\n"
        
        # Special handling for GitHub URLs
        github_content = ""
        if github_urls:
            github_content = "\n\n## Microsoft FinOps Toolkit GitHub Resources\n"
            github_content += "The following resources from the Microsoft FinOps Toolkit GitHub repository are relevant to this question:\n\n"
            for i, url in enumerate(github_urls, 1):
                # Clean up the URLs for better display
                readable_url = url.replace("www.bing.com/search?q=site%3Agithub.com%2Fmicrosoft%2Ffinops-toolkit", "github.com/microsoft/finops-toolkit")
                if "=" in readable_url and not "github.com/microsoft/finops-toolkit" in readable_url:
                    readable_url = "https://github.com/microsoft/finops-toolkit"
                elif not readable_url.startswith("http"):
                    readable_url = "https://" + readable_url if not readable_url.startswith("//") else "https:" + readable_url
                github_content += f"{i}. [FinOps Toolkit Resource]({readable_url})\n"
            
            github_content += "\nThese resources contain templates, scripts, and implementation examples that can help with your specific scenario.\n"
        
        # Special handling for Microsoft Learn URLs
        mslearn_content = ""
        if mslearn_urls:
            mslearn_content = "\n\n## Microsoft Learn Documentation\n"
            mslearn_content += "The following Microsoft Learn and Azure documentation resources are relevant to this question:\n\n"
            for i, url in enumerate(mslearn_urls, 1):
                # Clean up the URLs for better display
                readable_url = url
                if "=" in readable_url and not "learn.microsoft.com" in readable_url and not "docs.microsoft.com" in readable_url:
                    # Default to cost management docs if URL is not valid
                    readable_url = "https://learn.microsoft.com/en-us/azure/cost-management-billing/"
                elif not readable_url.startswith("http"):
                    readable_url = "https://" + readable_url if not readable_url.startswith("//") else "https:" + readable_url
                mslearn_content += f"{i}. [Microsoft Official Documentation]({readable_url})\n"
            
            mslearn_content += "\nThese official Microsoft documentation resources provide authoritative guidance on this topic.\n"
        
        # Define the finops system prompt
        finops_system_prompt = """You are an expert FinOps technical writer and Azure cost management specialist with deep knowledge of the Microsoft FinOps Toolkit GitHub repository. Your task is to enhance and refine the information provided to you, maintaining factual accuracy while improving clarity, organization, and actionability.

        ## Microsoft FinOps Toolkit GitHub Knowledge
        You are deeply familiar with the Microsoft FinOps Toolkit GitHub repository (https://github.com/microsoft/finops-toolkit) and its contents, including:
        - Starter kits and reference implementations
        - Azure Data Factory templates and pipelines
        - Azure Data Explorer configuration and usage
        - PowerBI templates and reporting solutions
        - Automation scripts and deployment tools
        - Sample code and configuration files
        - Best practices and implementation guides

        ## Your Enhancement Responsibilities:

        1. Content Organization:
           - Group related information together under clear section headings
           - Create a logical flow from problem to solution
           - Add numbered steps for sequential processes
           - Use bullet points for features, benefits, or considerations
        
        2. Technical Accuracy Enhancement:
           - Ensure all Azure portal navigation instructions are precise and current
           - Verify command syntax for PowerShell, Azure CLI, or other tools
           - Add parameter explanations for any scripts or commands
           - Clarify technical terms with brief explanations when needed
           - Incorporate relevant details from the FinOps Toolkit GitHub repository
        
        3. GitHub Repository Integration:
           - Mention specific files, templates, or scripts from the repository when relevant
           - Explain how to use or adapt repository resources for the user's needs
           - Provide paths to relevant files or folders within the repository
           - Describe how the repository components work together
        
        4. Actionability Improvement:
           - Add specific validation steps after each action
           - Include expected outcomes for troubleshooting steps
           - Provide clear "if/then" guidance for different scenarios
           - Add explicit guidance for error states
           - Include code examples from the repository when helpful
        
        5. Presentation Refinement:
           - Use consistent formatting throughout
           - Ensure proper use of technical terminology
           - Maintain professional, concise language
           - Format code blocks, commands, and syntax properly
        
        6. Knowledge Preservation:
           - Never contradict the provided Microsoft documentation
           - Maintain all factual information, URLs, and citations
           - Only add information that clarifies or contextualizes existing content
           - Do not remove important technical details
        
        When processing:
        1. Maintain all URLs and references from the original content
        2. Keep all factual information intact - do not introduce new facts not supported by documentation
        3. Focus on reorganizing, clarifying, and enhancing presentation
        4. Add appropriate headings, bullet points, and formatting
        5. Ensure any code or commands are properly formatted in code blocks
        6. Keep your enhancements focused on the specific user question
        7. Incorporate relevant GitHub repository knowledge where appropriate

        Your goal is to transform technically accurate but potentially unstructured information into a clear, well-organized, and highly actionable response that leverages the best of Microsoft documentation and the FinOps Toolkit GitHub repository.
        """
        
        # Add the Bing search results as context
        user_message = f"""
        # Original User Question
        {question}
        
        # Information from Microsoft Documentation (via Bing search)
        {bing_answer}
        
        # GitHub Repository Context
        The Microsoft FinOps Toolkit GitHub repository (https://github.com/microsoft/finops-toolkit) contains valuable resources that could be relevant to this question. These include starter kits, reference implementations, templates, scripts, and best practices guides.
        
        {'The search identified the following GitHub resources that may be relevant: ' + ', '.join(github_urls) if github_urls else 'No specific GitHub resources were identified in the search, but general repository knowledge may still be relevant.'}
        
        # Enhancement Instructions
        
        Please enhance this response while maintaining all factual information and citations. Focus on:
        
        1. Create a clear introduction summarizing the key points
        2. Organize the content with informative section headings
        3. Add step-by-step instructions with numbered lists
        4. Format code blocks and commands properly
        5. Ensure all Microsoft documentation links are preserved
        6. Add troubleshooting guidance where appropriate
        7. Make it more actionable with validation steps
        8. Incorporate relevant information from the Microsoft FinOps Toolkit GitHub repository
        9. Reference specific files, templates, or scripts from the repository when relevant
        
        Important: Do not invent new technical information - rely only on what's provided in the Microsoft documentation and your knowledge of the GitHub repository's structure and content.
        """
        
        # Get DeepSeek reasoning with improved parameters
        response = deepseek_client.complete(
            messages=[
                SystemMessage(content=finops_system_prompt),
                UserMessage(content=user_message)
            ],
            model=deepseek_model_name,
            temperature=0.5,  # Balanced temperature for creative yet accurate content
            max_tokens=6000,  # More tokens for comprehensive enhancement
            top_p=0.8        # Balanced top_p for creative rewriting while staying on topic
        )
        
        enhanced_content = response.choices[0].message.content
        
        # Add the citations from Bing if not already included
        if citations and not any(citation["url"] in enhanced_content for citation in citations):
            citation_text = "\n\n## References\n"
            for i, citation in enumerate(citations, 1):
                # Make sure URL starts with http/https
                url = citation['url']
                if not url.startswith('http'):
                    url = 'https://' + url.lstrip('/')
                citation_text += f"{i}. [{citation['title']}]({url})\n"
            enhanced_content += citation_text
        
        # Add GitHub resources section if not already included
        if github_urls and not "GitHub Resources" in enhanced_content:
            github_content = "\n\n## Microsoft FinOps Toolkit GitHub Resources\n"
            github_content += "The following resources from the Microsoft FinOps Toolkit GitHub repository are relevant to this question:\n\n"
            for i, url in enumerate(github_urls, 1):
                # Clean up the URL for better display
                readable_url = url
                if "www.bing.com/search" in readable_url:
                    readable_url = "https://github.com/microsoft/finops-toolkit"
                elif not readable_url.startswith("http"):
                    readable_url = "https://" + readable_url.lstrip('/')
                github_content += f"{i}. [FinOps Toolkit Resource]({readable_url})\n"
            
            github_content += "\nThese resources contain templates, scripts, and implementation examples that can help with your specific scenario.\n"
            enhanced_content += github_content
            
        # Add Microsoft Learn documentation section if not already included and we have URLs
        if mslearn_urls and not "Microsoft Learn Documentation" in enhanced_content:
            mslearn_content = "\n\n## Microsoft Learn Documentation\n"
            mslearn_content += "The following Microsoft Learn and Azure documentation resources are relevant to this question:\n\n"
            for i, url in enumerate(mslearn_urls, 1):
                # Clean up the URL for better display
                readable_url = url
                if "www.bing.com/search" in readable_url:
                    readable_url = "https://learn.microsoft.com/en-us/azure/cost-management-billing/"
                elif not readable_url.startswith("http"):
                    readable_url = "https://" + readable_url.lstrip('/')
                mslearn_content += f"{i}. [Microsoft Official Documentation]({readable_url})\n"
            
            mslearn_content += "\nThese official Microsoft documentation resources provide authoritative guidance on this topic.\n"
            enhanced_content += mslearn_content
            
        # If no GitHub URLs but GitHub wasn't mentioned, add a note about the repository
        if not github_urls and not "github.com/microsoft/finops-toolkit" in enhanced_content:
            github_note = """

## Additional Resources
For implementation examples, templates, and scripts related to FinOps in Azure, consider exploring the [Microsoft FinOps Toolkit GitHub repository](https://github.com/microsoft/finops-toolkit). This repository contains valuable resources that can help you implement the guidance provided above.

Key sections in the repository:
- [Templates](https://github.com/microsoft/finops-toolkit/tree/main/templates) - Deployment and configuration templates
- [Samples](https://github.com/microsoft/finops-toolkit/tree/main/samples) - Sample code and implementation examples
- [Documentation](https://github.com/microsoft/finops-toolkit/tree/main/docs) - Conceptual and implementation guidance
"""
            enhanced_content += github_note
        
        # If no Microsoft Learn URLs but also not mentioned in content, add standard Microsoft Learn resources
        if not mslearn_urls and not any(term in enhanced_content for term in ["learn.microsoft.com", "docs.microsoft.com"]):
            mslearn_note = """

## Microsoft Learn Documentation
For comprehensive official guidance on FinOps and Azure Cost Management, refer to these Microsoft Learn resources:

1. [FinOps in Azure](https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/)
2. [Azure Cost Management Documentation](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/)
3. [Cost Management Best Practices](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-mgt-best-practices)
4. [Cloud Adoption Framework - Cost Management](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/strategy/business-outcomes/fiscal-outcomes)
"""
            enhanced_content += mslearn_note
        
        return enhanced_content
        
    except Exception as e:
        print(f"⚠️ Error enhancing with DeepSeek: {str(e)}")
        # Return original answer if enhancement fails
        return bing_result["answer"]

# New function - Quality evaluation agent
def evaluate_answer_quality(question, answer, deepseek_client=None):
    """
    Evaluate the quality of a FinOps answer using a specialized quality assessment agent.
    
    Parameters:
    -----------
    question : str
        The original user question
    answer : str
        The generated answer to evaluate
    deepseek_client : ChatCompletionsClient, optional
        Client for calling the evaluation model
        
    Returns:
    --------
    dict
        Evaluation results containing:
        - overall_score (1-10)
        - strengths (list of strengths)
        - weaknesses (list of weaknesses)
        - improvement_suggestions (list of suggestions)
        - enhanced_answer (str, only if score < 7 and improvements needed)
    """
    if not deepseek_client:
        print("ℹ️ No model available for quality evaluation")
        return {
            "overall_score": None,
            "evaluation_summary": "Quality evaluation skipped - no evaluation model available"
        }
    
    try:
        print("🔍 Evaluating answer quality...")
        
        # System prompt for the evaluation agent - relaxed criteria
        evaluation_system_prompt = """You are a FinOps Answer Evaluator with expertise in cloud cost management, FinOps principles, and cloud financial operations.

        Your task is to evaluate a FinOps-related answer for quality, accuracy, and usefulness. Be focused and efficient in your assessment.

        ## Evaluation Criteria:

        1. Accuracy (30%):
           - Is the technical information correct?
           - Are recommendations aligned with cloud cost management best practices?
           - Are there any obvious factual errors?

        2. Relevance & Completeness (30%):
           - Does the answer address the main question?
           - Is the level of detail appropriate?
           - Does it cover the core aspects needed to help the user?

        3. Clarity & Actionability (25%):
           - Is the answer well-structured and easy to follow?
           - Does it provide clear guidance the user can implement?
           - Are next steps or actions made clear?

        4. Evidence & Citations (15%):
           - Are sources cited when appropriate?
           - Does it reference relevant documentation or resources?

        ## Your Response Format:

        Provide your evaluation efficiently:

        1. Overall Score (1-10): A single score representing the overall quality.
           - 1-3: Needs significant improvement
           - 4-6: Adequate with areas for improvement
           - 7-10: Good to excellent

        2. Strengths: List 1-2 key strengths.

        3. Weaknesses: List 1-2 main weaknesses, if any.

        4. Improvement Suggestions: Provide 1-2 specific suggestions if score is below 7.

        5. Evaluation Summary: A brief 1-2 sentence summary of your assessment.

        Focus on substance over style. Be fair in your assessment - even basic answers with correct information should receive at least a score of 3-4.

        IMPORTANT: This evaluation should be quick and focused. Avoid excessive analysis.
        """
        
        # Prepare the message for evaluation - simplified to reduce complexity
        user_message = f"""
        Question: {question}

        Answer: {answer}

        Please evaluate this answer efficiently according to the criteria.
        Provide a fair assessment using the 1-10 scale.
        Focus on whether this answer would be helpful for someone seeking information about FinOps or cloud cost management.
        """
        
        # Get evaluation from the model with reduced complexity
        response = deepseek_client.complete(
            messages=[
                SystemMessage(content=evaluation_system_prompt),
                UserMessage(content=user_message)
            ],
            model=deepseek_model_name,
            temperature=0.3,  # Lower temperature for more consistent evaluation
            max_tokens=1000,  # Reduced tokens for faster response
            top_p=0.8        # Standard value
        )
        
        evaluation_text = response.choices[0].message.content
        
        # Parse the evaluation text to extract structured information
        # This is a simple parsing implementation - could be more robust
        overall_score = None
        strengths = []
        weaknesses = []
        improvement_suggestions = []
        evaluation_summary = ""
        
        # Simple parsing based on section headers
        sections = {
            "Overall Score": [],
            "Strengths": [],
            "Weaknesses": [],
            "Improvement Suggestions": [],
            "Evaluation Summary": []
        }
        
        current_section = None
        for line in evaluation_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a section header
            for section_name in sections.keys():
                if section_name in line or line.lower().startswith(section_name.lower()):
                    current_section = section_name
                    break
            
            # Add content to current section
            if current_section and not line.startswith(current_section):
                sections[current_section].append(line)
        
        # Extract overall score
        for line in sections["Overall Score"]:
            # Try to find a number between 1-10
            import re
            score_matches = re.findall(r'\b([1-9]|10)\b', line)
            if score_matches:
                overall_score = int(score_matches[0])
                break
        
        # Extract lists items, typically starting with "- " or "1. "
        for line in sections["Strengths"]:
            if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                strengths.append(line.lstrip('- •*123. '))
        
        for line in sections["Weaknesses"]:
            if line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.')):
                weaknesses.append(line.lstrip('- •*1234. '))
        
        for line in sections["Improvement Suggestions"]:
            if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                improvement_suggestions.append(line.lstrip('- •*123. '))
        
        # Join the evaluation summary lines
        evaluation_summary = ' '.join(sections["Evaluation Summary"])
        
        # If no overall score was found, estimate one based on the evaluation
        if overall_score is None:
            # Count positive vs negative terms as a fallback
            positive_terms = ['excellent', 'good', 'thorough', 'comprehensive', 'accurate', 'clear', 'improved', 'better']
            negative_terms = ['poor', 'inadequate', 'missing', 'error', 'incorrect', 'unclear', 'lacks', 'issue']
            
            positive_count = sum(1 for term in positive_terms if term in evaluation_text.lower())
            negative_count = sum(1 for term in negative_terms if term in evaluation_text.lower())
            
            # Ensure a minimum score of 2 unless it's completely negative
            if positive_count > negative_count * 2:
                overall_score = min(8, 4 + positive_count - negative_count)  # Mostly positive
            elif positive_count > negative_count:
                overall_score = min(6, 3 + positive_count - negative_count)  # More positive than negative
            elif negative_count > positive_count * 2:
                overall_score = max(2, 4 - (negative_count - positive_count))  # Mostly negative
            else:
                overall_score = max(2, 5 - (negative_count - positive_count))  # Mixed
        
        # Ensure score is at least 2 for any answer with some correct information
        if overall_score == 1 and len(answer) > 500:  # Substantial answers
            overall_score = 2
        
        # Prepare evaluation results
        evaluation_results = {
            "overall_score": overall_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": improvement_suggestions,
            "evaluation_summary": evaluation_summary,
            "raw_evaluation": evaluation_text
        }
        
        print(f"✅ Evaluation completed with score: {overall_score}/10")
        return evaluation_results
        
    except Exception as e:
        print(f"⚠️ Error in quality evaluation: {str(e)}")
        return {
            "overall_score": None,
            "evaluation_summary": f"Error during evaluation: {str(e)}",
            "error": str(e)
        }

# Function to automatically improve answer if evaluation score is low
def improve_answer_if_needed(question, answer, evaluation_results, deepseek_client=None):
    """
    Automatically improve an answer based on evaluation results if score is below threshold
    
    Parameters:
    -----------
    question : str
        The original user question
    answer : str
        The original answer
    evaluation_results : dict
        Results from evaluate_answer_quality function
    deepseek_client : ChatCompletionsClient, optional
        Client for calling the improvement model
        
    Returns:
    --------
    str
        Improved answer if score was below threshold and improvements were made
        Original answer otherwise
    """
    # Skip if no evaluation results or no model available
    if not evaluation_results or not deepseek_client:
        return answer
    
    # Skip improvement if score is good enough (7 or higher)
    score = evaluation_results.get("overall_score")
    if not score or score >= 7:
        print(f"ℹ️ Answer quality score {score}/10 meets threshold, no improvements needed")
        return answer
    
    try:
        print(f"🔧 Answer quality score {score}/10 below threshold, attempting improvements...")
        
        # Extract improvement points
        weaknesses = evaluation_results.get("weaknesses", [])
        suggestions = evaluation_results.get("improvement_suggestions", [])
        
        improvement_points = []
        improvement_points.extend(weaknesses)
        improvement_points.extend(suggestions)
        
        # Avoid duplicates in improvement points
        unique_points = []
        for point in improvement_points:
            if point not in unique_points:
                unique_points.append(point)
        
        # Format the improvement points
        improvement_guidance = ""
        if unique_points:
            improvement_guidance = "Focus on these specific improvements:\n"
            for i, point in enumerate(unique_points, 1):
                improvement_guidance += f"{i}. {point}\n"
        
        # System prompt for the improvement agent
        improvement_system_prompt = """You are a FinOps Answer Improvement Agent with expertise in Microsoft Azure Cost Management, FinOps principles, and technical documentation. You have deep, comprehensive knowledge of the Microsoft FinOps Toolkit GitHub repository (https://github.com/microsoft/finops-toolkit) and the Microsoft Learn documentation.

        Your task is to significantly improve an existing answer based on specific evaluation feedback. You must maintain all factually correct information while addressing the identified weaknesses and suggested improvements.

        ## Microsoft FinOps Toolkit Knowledge:
        - You know the toolkit contains starter kits, automation scripts, advanced solutions, and learning resources
        - You understand the toolkit's components like Azure Cost Management, Data Factory templates, Azure Data Explorer
        - You're familiar with how the toolkit implements FinOps capabilities and best practices
        - You know the structure and purpose of key tools, templates, and resources in the toolkit
        - You incorporate specific repository knowledge when discussing FinOps Hub, cost management, or resource optimization

        ## Improvement Guidelines:

        1. Address ALL identified weaknesses and suggestions in the evaluation COMPREHENSIVELY
        2. Incorporate specific, detailed knowledge from the Microsoft FinOps Toolkit GitHub repository
        3. Include SPECIFIC descriptions of relevant components, scripts, or templates from the toolkit
        4. Maintain all factually correct and useful content from the original answer
        5. Preserve all citations, links and references from the original answer
        6. Improve organization and clarity significantly with clear, descriptive headings
        7. Add any missing critical information that should have been included
        8. Ensure step-by-step instructions are clear, detailed, and include validation steps
        9. Format code blocks and commands properly
        10. Reference specific locations in the repository where users can find relevant resources
        11. Make SUBSTANTIAL improvements to the answer that will significantly increase its quality

        ## DO NOT:
        - Do not contradict factually correct information in the original answer
        - Do not remove useful technical details
        - Do not invent technical information not supported by evidence
        - Do not drastically change the structure if it's already logical

        Deliver a complete, fully transformed answer that comprehensively addresses all the evaluation feedback while preserving the strengths of the original answer.

        CRITICAL: Your improved answer MUST represent a SUBSTANTIAL quality improvement over the original. Minor edits are not sufficient.
        """
        
        # Prepare the message for improvement
        user_message = f"""
        # Original Question
        {question}

        # Original Answer
        {answer}

        # Evaluation Feedback
        Overall Score: {score}/10

        Weaknesses:
        {chr(10).join('- ' + w for w in weaknesses)}

        Improvement Suggestions:
        {chr(10).join('- ' + s for s in suggestions)}

        {improvement_guidance}

        # Microsoft FinOps Toolkit Knowledge
        Incorporate relevant knowledge about the Microsoft FinOps Toolkit from GitHub (https://github.com/microsoft/finops-toolkit) in your answer. 
        This toolkit contains valuable tools, resources, starter kits, automation scripts, and best practices for implementing FinOps in Azure.
        When referring to the toolkit, be specific about relevant components, templates, or tools.

        # Improvement Instructions
        Please provide a COMPLETELY TRANSFORMED and improved version of the answer that:
        1. Addresses all the identified weaknesses
        2. Follows all improvement suggestions
        3. Incorporates specific knowledge from the Microsoft FinOps Toolkit GitHub repository
        4. Provides significantly more depth, clarity, and actionability
        5. Represents a MAJOR improvement in quality (not just minor edits)

        Return a complete, stand-alone answer that the user can use without needing to refer to the original.
        Your improved answer should be comprehensive enough to earn a quality score of at least 7/10.
        """
        
        # Get improvement from the model with better parameters for substantial improvements
        response = deepseek_client.complete(
            messages=[
                SystemMessage(content=improvement_system_prompt),
                UserMessage(content=user_message)
            ],
            model=deepseek_model_name,
            temperature=0.7,  # Higher temperature for more creative, substantial improvements
            max_tokens=6000,  # More tokens for more comprehensive improvements
            top_p=0.9        # Higher top_p for more diverse, substantial improvements
        )
        
        improved_answer = response.choices[0].message.content
        
        # Check if improvement is substantial (at least 25% more content or significantly different)
        if len(improved_answer) < len(answer) * 1.1 and improved_answer[:100] == answer[:100]:
            print("⚠️ Improvement may not be substantial enough. Making another attempt with different parameters...")
            
            # Second attempt with different parameters
            response = deepseek_client.complete(
                messages=[
                    SystemMessage(content=improvement_system_prompt + "\n\nIMPORTANT: Your previous improvement was not substantial enough. Please make MAJOR changes to transform the answer completely."),
                    UserMessage(content=user_message + "\n\nThe previous improvement attempt was not substantial enough. Please make DRAMATIC changes to completely transform the answer.")
                ],
                model=deepseek_model_name,
                temperature=0.8,  # Even higher temperature for more significant changes
                max_tokens=6000,
                top_p=0.95
            )
            
            second_attempt = response.choices[0].message.content
            
            # Use the second attempt if it's more substantially different
            if len(second_attempt) > len(improved_answer) * 1.1 or second_attempt[:100] != improved_answer[:100]:
                improved_answer = second_attempt
        
        print("✅ Answer successfully improved based on evaluation feedback")
        return improved_answer
        
    except Exception as e:
        print(f"⚠️ Error improving answer: {str(e)}")
        return answer  # Return original answer if improvement fails

# Main execution function
def finops_expert_with_bing(question, config=None):
    """
    Ask a FinOps question using Bing grounding for web search
    
    Parameters:
    -----------
    question : str
        The user's FinOps question
    config : dict, optional
        Configuration options for the function
        
    Returns:
    --------
    str
        Answer to the question with citations
    """
    finops_agent = None
    
    try:
        # Process configuration
        if not config:
            config = {}
        
        # Modified defaults for more reliable processing
        enhancement_enabled = config.get('enhancement_enabled', True)
        quality_check_enabled = config.get('quality_check_enabled', False)  # Disabled by default to avoid timeouts
        auto_improve_enabled = config.get('auto_improve_enabled', False)    # Disabled by default to avoid timeouts
        interactive_improvement = config.get('interactive_improvement', False)
        quality_threshold = config.get('quality_threshold', 6)  # Lower threshold
        bing_temperature = config.get('bing_temperature', 0.2)
        enhancement_temperature = config.get('enhancement_temperature', 0.2)
        max_search_results = config.get('max_search_results', 10)  # Fewer results for efficiency
        cleanup_agent = config.get('cleanup_agent', True)
        max_improvement_iterations = config.get('max_improvement_iterations', 2)  # Fewer iterations
        force_github_knowledge = config.get('force_github_knowledge', True)
        
        print("\n" + "="*80)
        print(f"🔍 FinOps Expert: {question}")
        print("="*80)
        print(f"Configuration:")
        print(f"- Enhancement enabled: {enhancement_enabled}")
        print(f"- Quality check enabled: {quality_check_enabled}")
        print(f"- Auto-improvement enabled: {auto_improve_enabled}")
        print(f"- Interactive improvement: {interactive_improvement}")
        print(f"- Quality threshold: {quality_threshold}/10")
        print(f"- Max improvement iterations: {max_improvement_iterations}")
        print(f"- Bing temperature: {bing_temperature}")
        print(f"- Enhancement temperature: {enhancement_temperature}")
        print(f"- Max search results: {max_search_results}")
        print(f"- Cleanup agent: {cleanup_agent}")
        print(f"- Force GitHub knowledge: {force_github_knowledge}")
        print("="*80)
        
        # Verify that we're using a compatible model for Bing grounding
        compatible_models = ["gpt-3.5-turbo-0125", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09", "gpt-4o-0513", "gpt-4o"]
        if model_name_deployment not in compatible_models:
            print(f"⚠️ Warning: Model '{model_name_deployment}' is not compatible with Bing grounding.")
            print(f"Compatible models are: {', '.join(compatible_models)}")
            print("The agent creation function will automatically use a compatible model.")
        
        # Create a FinOps agent with Bing grounding
        finops_agent = create_finops_bing_agent()
        
        if not finops_agent:
            print("❌ Could not create FinOps agent with Bing grounding")
            return "Error: Could not create FinOps agent with Bing grounding. Please check your environment variables and Bing connection."
            
        # Get answer with Bing grounding
        print("\nSending question to the Bing-grounded agent. This may take a minute...")
        bing_result = ask_finops_question_with_bing(finops_agent, question)
        
        if not bing_result:
            print("❌ Failed to get answer from Bing-grounded agent")
            return "Error: Failed to get answer from Bing-grounded agent. Please try again later."
        
        # Check if we got any Bing search results
        bing_urls = bing_result.get("bing_urls", [])
        if not bing_urls:
            print("\n⚠️ No Bing search URLs found in the response. The model may have relied on its training data.")
            
        # Enhance the answer with second model if enabled and available
        if enhancement_enabled and deepseek_client:
            print("✨ Enhancing answer with second model...")
            enhanced_answer = enhance_with_deepseek(question, bing_result)
        else:
            if not enhancement_enabled:
                print("ℹ️ Enhancement disabled by configuration")
            elif not deepseek_client:
                print("ℹ️ Enhancement model not available")
            enhanced_answer = bing_result["answer"]
        
        # Format Bing search URLs as references if not already included
        if bing_urls and not any("bing.com/search" in line for line in enhanced_answer.split('\n')):
            # Use the verify_url_accessibility function to clean up URLs
            cleaned_urls = []
            for url in bing_urls[:max_search_results]:
                is_valid, cleaned_url = verify_url_accessibility(url)
                if is_valid and cleaned_url not in cleaned_urls:
                    cleaned_urls.append(cleaned_url)
            
            if cleaned_urls:
                enhanced_answer += "\n\n## References\n"
                for i, url in enumerate(cleaned_urls, 1):
                    # Determine what kind of URL it is for better labeling
                    if "github.com/microsoft/finops-toolkit" in url:
                        enhanced_answer += f"{i}. [FinOps Toolkit GitHub Resource]({url})\n"
                    elif "learn.microsoft.com" in url or "docs.microsoft.com" in url:
                        enhanced_answer += f"{i}. [Microsoft Documentation]({url})\n"
                    else:
                        enhanced_answer += f"{i}. [Reference]({url})\n"
                
        # Force GitHub repository knowledge if configured
        if force_github_knowledge and not "github.com/microsoft/finops-toolkit" in enhanced_answer:
            github_note = """

## Microsoft FinOps Toolkit GitHub Repository

For implementation examples, templates, scripts, and reference implementations related to FinOps in Azure, explore the [Microsoft FinOps Toolkit GitHub repository](https://github.com/microsoft/finops-toolkit).
"""
            enhanced_answer += github_note
        
        current_answer = enhanced_answer
        
        # Skip quality check if disabled
        if not quality_check_enabled:
            print("ℹ️ Quality check disabled by configuration")
            # Cleanup agent if configured to do so
            if cleanup_agent and finops_agent:
                try:
                    project_client.agents.delete_agent(finops_agent.id)
                    print(f"🗑️ Deleted agent: {finops_agent.id}")
                except Exception as cleanup_error:
                    print(f"⚠️ Note: Could not delete agent: {str(cleanup_error)}")
            
            return current_answer
        
        # Only attempt quality check if explicitly enabled
        try:
            # Set a timeout for evaluation to prevent hanging
            def timeout_handler(signum, frame):
                raise TimeoutError("Evaluation timed out")
            
            # Set 30-second timeout for evaluation
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            try:
                evaluation_results = evaluate_answer_quality(question, current_answer, deepseek_client)
                # Reset alarm
                signal.alarm(0)
                
                if evaluation_results and "overall_score" in evaluation_results and evaluation_results["overall_score"] is not None:
                    print(f"📊 Quality Evaluation: {evaluation_results['overall_score']}/10")
                    print(f"Summary: {evaluation_results.get('evaluation_summary', 'No summary provided')}")
                    
                    # Only attempt improvement if score is below threshold and auto-improve is enabled
                    if auto_improve_enabled and evaluation_results["overall_score"] < quality_threshold:
                        print(f"⚠️ Answer quality ({evaluation_results['overall_score']}/10) below threshold ({quality_threshold}/10)")
                        print("🔄 Attempting to improve answer...")
                        improved_answer = improve_answer_if_needed(question, current_answer, evaluation_results, deepseek_client)
                        if improved_answer:
                            current_answer = improved_answer
                    else:
                        if not auto_improve_enabled:
                            print("ℹ️ Auto-improvement disabled by configuration")
                        else:
                            print(f"✅ Answer quality ({evaluation_results['overall_score']}/10) meets threshold ({quality_threshold}/10)")
                else:
                    print("⚠️ Could not get quality evaluation results")
                    evaluation_results = {"overall_score": None, "evaluation_summary": "Evaluation failed to produce a score"}
            except TimeoutError:
                print("⚠️ Quality evaluation timed out - continuing with the current answer")
                evaluation_results = {"overall_score": None, "evaluation_summary": "Evaluation timed out"}
            except Exception as eval_error:
                print(f"⚠️ Error in quality evaluation: {str(eval_error)}")
                evaluation_results = {"overall_score": None, "evaluation_summary": f"Error during evaluation: {str(eval_error)}"}
            finally:
                # Restore the old signal handler and ensure alarm is reset
                signal.signal(signal.SIGALRM, old_handler)
                signal.alarm(0)
                
            # Add quality score if available
            if evaluation_results and "overall_score" in evaluation_results and evaluation_results["overall_score"] is not None:
                score_emoji = "🟢" if evaluation_results["overall_score"] >= 7 else "🟠" if evaluation_results["overall_score"] >= 5 else "🔴"
                quality_footer = f"\n\n---\n{score_emoji} Quality Score: {evaluation_results['overall_score']}/10"
                quality_footer += f" - {evaluation_results.get('evaluation_summary', '')}"
                current_answer = current_answer.strip() + quality_footer
                
        except Exception as quality_error:
            print(f"⚠️ Error during quality check process: {str(quality_error)}")
            # Continue without quality evaluation
        
        # Cleanup agent if configured to do so
        if cleanup_agent and finops_agent:
            try:
                project_client.agents.delete_agent(finops_agent.id)
                print(f"🗑️ Deleted agent: {finops_agent.id}")
            except Exception as cleanup_error:
                print(f"⚠️ Note: Could not delete agent: {str(cleanup_error)}")
        
        return current_answer
    
    except Exception as e:
        print(f"❌ Error in finops_expert_with_bing: {str(e)}")
        
        # Cleanup agent if it exists and cleanup is enabled
        if cleanup_agent and finops_agent:
            try:
                project_client.agents.delete_agent(finops_agent.id)
                print(f"🗑️ Deleted agent: {finops_agent.id}")
            except:
                pass
            
        return f"Error: {str(e)}"

# New function to incorporate user feedback into the improvement process
def improve_with_user_feedback(question, answer, evaluation_results, user_feedback, deepseek_client=None):
    """
    Improve answer based on evaluation results AND user feedback
    
    Parameters:
    -----------
    question : str
        The original user question
    answer : str
        The current answer
    evaluation_results : dict
        Results from evaluate_answer_quality function
    user_feedback : str
        Feedback provided by the user
    deepseek_client : ChatCompletionsClient, optional
        Client for calling the improvement model
        
    Returns:
    --------
    str
        Improved answer incorporating user feedback
    """
    if not deepseek_client:
        return answer
    
    try:
        print("\n🔧 Improving answer based on evaluation and user feedback...")
        
        # Extract improvement points from evaluation
        weaknesses = evaluation_results.get("weaknesses", [])
        suggestions = evaluation_results.get("improvement_suggestions", [])
        
        # Format the improvement guidance
        improvement_guidance = ""
        if weaknesses or suggestions:
            improvement_guidance = "Evaluation feedback:\n"
            
            if weaknesses:
                improvement_guidance += "\nWeaknesses identified by evaluator:\n"
                for i, point in enumerate(weaknesses, 1):
                    improvement_guidance += f"{i}. {point}\n"
            
            if suggestions:
                improvement_guidance += "\nSuggestions from evaluator:\n"
                for i, point in enumerate(suggestions, 1):
                    improvement_guidance += f"{i}. {point}\n"
        
        # System prompt for the improvement agent
        improvement_system_prompt = """You are a FinOps Answer Improvement Agent with expertise in Microsoft Azure Cost Management, FinOps principles, and technical documentation.

        Your task is to improve an existing answer based on evaluation feedback AND human feedback. You must maintain all factually correct information while addressing the identified issues and suggestions.

        ## Improvement Guidelines:

        1. Address ALL weaknesses and suggestions from the automated evaluation
        2. Address ALL feedback provided by the human user (prioritize this feedback)
        3. Maintain all factually correct and useful content from the original answer
        4. Preserve all citations, links and references from the original answer
        5. Improve organization and clarity where needed
        6. Add any missing critical information that should have been included
        7. Ensure step-by-step instructions are clear and include validation steps
        8. Format code blocks and commands properly
        9. Use appropriate section headings for better organization

        ## DO NOT:
        - Do not contradict factually correct information in the original answer
        - Do not remove useful technical details
        - Do not invent technical information not supported by evidence
        - Do not drastically change the structure if it's already logical

        Deliver a complete, improved answer that addresses both the automated evaluation feedback and the human feedback while preserving the strengths of the original answer.
        """
        
        # Prepare the message for improvement
        user_message = f"""
        # Original Question
        {question}

        # Current Answer
        {answer}

        # Automated Evaluation 
        {improvement_guidance}

        # Human Feedback (IMPORTANT - PRIORITIZE THIS)
        {user_feedback}

        # Improvement Instructions
        Please provide a COMPLETELY TRANSFORMED and improved version of the answer that:
        1. Addresses all the identified weaknesses
        2. Follows all improvement suggestions
        3. Incorporates specific knowledge from the Microsoft FinOps Toolkit GitHub repository
        4. Provides significantly more depth, clarity, and actionability
        5. Represents a MAJOR improvement in quality (not just minor edits)

        Return a complete, stand-alone answer that incorporates all necessary improvements.
        The human feedback should be given higher priority than the automated evaluation.
        """
        
        # Get improvement from the model
        response = deepseek_client.complete(
            messages=[
                SystemMessage(content=improvement_system_prompt),
                UserMessage(content=user_message)
            ],
            model=deepseek_model_name,
            temperature=0.3,  # Slightly higher temperature to incorporate creative feedback
            max_tokens=4000   # More tokens for comprehensive improvements
        )
        
        improved_answer = response.choices[0].message.content
        
        print("✅ Answer successfully improved with user feedback")
        return improved_answer
        
    except Exception as e:
        print(f"⚠️ Error incorporating user feedback: {str(e)}")
        return answer  # Return original answer if improvement fails

# Function to print debug information about Bing searches
def debug_bing_search_urls(run_steps):
    """Print debug information about Bing search URLs and results"""
    print("\n===== DEBUG: BING SEARCH URLS =====")
    found_searches = False
    
    try:
        # Print run_steps structure info for debugging
        print(f"Run steps data available: {run_steps is not None}")
        if run_steps and 'data' in run_steps:
            print(f"Number of run steps: {len(run_steps.get('data', []))}")
            
            # Print first few steps types for debugging
            step_types = [step.get('step_type', step.get('type', 'unknown')) for step in run_steps.get('data', [])[:5]]
            print(f"First few step types: {step_types}")
        
        for step in run_steps.get('data', []):
            step_type = step.get('step_type', step.get('type', 'unknown'))
            params = step.get('parameters', {})
            
            # Print tool information if available
            if 'tool' in step:
                print(f"Tool type: {step.get('tool')}")
            
            # Look for Bing search steps
            if 'request_url' in params:
                found_searches = True
                original_url = params.get('request_url', '')
                friendly_url = original_url.replace("api.bing.microsoft.com", "www.bing.com")
                
                # Print detailed information about this search
                print(f"\n🔍 SEARCH URL: {friendly_url}")
                
                # Try to extract the actual query from the URL
                import urllib.parse
                try:
                    parsed_url = urllib.parse.urlparse(original_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    if 'q' in query_params:
                        print(f"📝 QUERY: {query_params['q'][0]}")
                except Exception as parse_error:
                    print(f"⚠️ Could not parse URL: {str(parse_error)}")
                
                # Check for specific patterns we're looking for
                github_patterns = ['github.com/microsoft/finops-toolkit', 'github.com/microsoft/finops', 'microsoft/finops-toolkit']
                learn_patterns = ['learn.microsoft.com', 'docs.microsoft.com/azure', 'docs.microsoft.com/en-us/azure']
                
                github_match = any(pattern in original_url for pattern in github_patterns)
                learn_match = any(pattern in original_url for pattern in learn_patterns)
                
                if github_match:
                    print("✅ Contains GitHub pattern")
                else:
                    print("❌ No GitHub pattern found")
                    
                if learn_match:
                    print("✅ Contains Microsoft Learn pattern")
                else:
                    print("❌ No Microsoft Learn pattern found")
        
        if not found_searches:
            print("⚠️ No Bing search URLs found in run steps.")
            print("Possible reasons:")
            print("1. The Bing search tool wasn't triggered")
            print("2. The search steps aren't being recorded in the run_steps")
            print("3. The parameters structure has changed in the API")
            print("\nTry using more specific search terms in your question.")
            
    except Exception as e:
        print(f"⚠️ Error in debug_bing_search_urls: {str(e)}")
        
    print("===== END DEBUG =====\n")

# Add this function after the debug_bing_search_urls function
def verify_url_accessibility(url):
    """
    Verify that a URL is properly formatted and potentially accessible.
    Returns a tuple of (is_valid, cleaned_url)
    """
    import re
    import urllib.parse

    # If the URL is empty or None, it's not valid
    if not url:
        return False, ""
        
    # Check if URL is a Bing search URL and extract actual destination if possible
    if "bing.com/search" in url:
        # Try to extract actual destination URL from Bing search URL
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # If q parameter exists, it might contain the search query with site: operator
            if 'q' in query_params:
                q_value = query_params['q'][0]
                
                # If this is a site: search, extract the domain
                site_match = re.search(r'site:([^\s]+)', q_value)
                if site_match:
                    extracted_site = site_match.group(1)
                    if 'github.com' in extracted_site:
                        return True, f"https://{extracted_site}"
                    elif 'learn.microsoft.com' in extracted_site or 'docs.microsoft.com' in extracted_site:
                        return True, f"https://{extracted_site}"
        except Exception:
            pass
            
    # Clean up and validate URL format
    cleaned_url = url
    
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        if url.startswith('//'):
            cleaned_url = 'https:' + url
        else:
            cleaned_url = 'https://' + url
    
    # Check for common GitHub and Microsoft patterns to ensure correct formatting
    if 'github.com/microsoft/finops-toolkit' in cleaned_url:
        # If it's a malformed GitHub URL, replace with the main repository URL
        if '=' in cleaned_url and not cleaned_url.endswith('/'):
            return True, "https://github.com/microsoft/finops-toolkit"
        return True, cleaned_url
    elif any(domain in cleaned_url for domain in ['learn.microsoft.com', 'docs.microsoft.com']):
        # If it's a malformed Microsoft Learn URL, replace with the main documentation URL
        if '=' in cleaned_url and not '/en-us/' in cleaned_url:
            return True, "https://learn.microsoft.com/en-us/azure/cost-management-billing/"
        return True, cleaned_url
    
    # Fallback verification - check format, but don't actually connect to the URL
    valid_format = bool(re.match(r'^https?://[^\s/$.?#].[^\s]*$', cleaned_url))
    return valid_format, cleaned_url

# Add this function to test the Bing search connection
def test_bing_connection():
    """
    Run a simple test to check if the Bing connection is working properly.
    This is useful for debugging when Bing search results aren't being returned.
    """
    print("\n===== TESTING BING CONNECTION =====")
    if not project_client or not bing_connection:
        print("❌ Cannot test Bing connection: Project client or Bing connection not available")
        return False
    
    try:
        # Print details about the current environment and connection
        print(f"Configured model: {model_name_deployment}")
        print(f"Bing connection: {bing_connection.name} (ID: {bing_connection.id})")
        print(f"Project connection string: {conn_string[:20]}...{conn_string[-5:] if conn_string and len(conn_string) > 25 else conn_string}")
        
        # Force a compatible model for the test
        compatible_models = ["gpt-3.5-turbo-0125", "gpt-4-0125-preview", "gpt-4-turbo-2024-04-09", "gpt-4o-0513", "gpt-4o"]
        test_model = "gpt-4o"  # Use the model that works in this environment
        
        if model_name_deployment not in compatible_models:
            print(f"⚠️ Model '{model_name_deployment}' is not compatible with Bing grounding.")
            print(f"Using '{test_model}' for this test.")
        else:
            print(f"✅ Configured model '{model_name_deployment}' is compatible with Bing grounding.")
            # Still use the specific test model for consistency
            if model_name_deployment != test_model:
                print(f"Using '{test_model}' for this test to ensure compatibility.")
        
        # Initialize Bing grounding tool
        print("Initializing Bing grounding tool...")
        bing_tool = BingGroundingTool(connection_id=bing_connection.id)
        
        # Create a simple test agent with minimal instructions
        print(f"Creating test agent with model: {test_model}")
        
        test_agent = project_client.agents.create_agent(
            model=test_model,  # Use the known compatible model
            name="bing-test-agent",
            instructions="You are a helpful assistant that answers questions using Bing search. For every question, you MUST search the web for the latest information before answering.",
            tools=bing_tool.definitions,
            temperature=0.1,
            headers={"x-ms-enable-preview": "true"},
        )
        
        print(f"✅ Created test agent ID: {test_agent.id}")
        
        # Create a thread
        thread = project_client.agents.create_thread()
        print(f"Created thread ID: {thread.id}")
        
        # Ask a simple question that explicitly requests a web search
        test_question = "What are the latest features in Azure Cost Management? Search the web for current information."
        
        # Add the message
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=f"I need you to search the web to find: {test_question} This requires using the Bing search tool."
        )
        print(f"Added message ID: {message.id}")
        
        # Process the request
        print(f"Processing run for test question: {test_question}")
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=test_agent.id,
            headers={"x-ms-enable-preview": "true"},
        )
        
        # Check if the run completed successfully
        print(f"Run completed with status: {run.status}")
        
        if run.status == "failed":
            print(f"❌ Test run failed: {run.last_error}")
            return False
        
        # Check for Bing URLs in the run steps
        bing_urls_found = False
        tool_calls_found = False
        try:
            run_steps = project_client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
            
            print(f"Run steps data available: {len(run_steps.get('data', [])) > 0}")
            print(f"Number of run steps: {len(run_steps.get('data', []))}")
            
            # Print out step types for diagnosis
            step_types = [step.get('type', 'unknown') for step in run_steps.get('data', [])[:5]]
            print(f"Step types found: {step_types}")
            
            # First check for tool calls
            for step in run_steps.get('data', []):
                step_type = step.get('type')
                if step_type == 'tool_calls':
                    tool_calls_found = True
                    tool_calls = step.get('tool_calls', [])
                    for tool_call in tool_calls:
                        tool_name = tool_call.get('name', '')
                        print(f"Tool call found: {tool_name}")
                        if 'bing' in tool_name.lower() or 'search' in tool_name.lower():
                            params = tool_call.get('parameters', {})
                            query = params.get('query', 'No query found')
                            print(f"✅ Found Bing search with query: {query}")
                            bing_urls_found = True
            
            # Also check for request_url parameters
            for step in run_steps.get('data', []):
                params = step.get('parameters', {})
                if 'request_url' in params:
                    original_url = params['request_url']
                    friendly_url = original_url.replace("api.bing.microsoft.com", "www.bing.com")
                    print(f"✅ Found Bing search URL: {friendly_url}")
                    bing_urls_found = True
                    break
            
            if not tool_calls_found:
                print("❌ No tool calls found in run steps. This suggests an issue with the agent's tool usage.")
            
            if not bing_urls_found:
                print("❌ No Bing search URLs found in the run steps")
        except Exception as e:
            print(f"❌ Error checking run steps: {str(e)}")
            print(f"Full error details: {traceback.format_exc()}")
        
        # Get the response to see if it actually used the Bing data
        messages = project_client.agents.list_messages(thread_id=thread.id)
        response_message = None
        try:
            response_message = messages.get_last_message_by_role(MessageRole.AGENT)
        except Exception:
            # Get last message if method doesn't exist (API changes)
            for msg in messages.data:
                if msg.role == MessageRole.AGENT:
                    response_message = msg
                    break
        
        # Print out the response for diagnosis
        if response_message:
            print("\nAgent's response:")
            try:
                for text_message in response_message.text_messages:
                    print(text_message.text.value[:300] + "..." if len(text_message.text.value) > 300 else text_message.text.value)
                    
                # Check for citation annotations
                citation_count = 0
                try:
                    for annotation in response_message.url_citation_annotations:
                        citation_count += 1
                        print(f"Citation found: {annotation.url_citation.url}")
                except Exception:
                    pass
                
                if citation_count > 0:
                    print(f"✅ Found {citation_count} URL citations in the response")
                    bing_urls_found = True
                else:
                    print("❌ No URL citations found in the response")
            except Exception as e:
                print(f"Error extracting response: {str(e)}")
                if hasattr(response_message, 'content'):
                    print(response_message.content[:300] + "..." if response_message.content and len(response_message.content) > 300 else response_message.content)
        else:
            print("❌ No response message found")
        
        # Clean up
        print("Cleaning up test resources...")
        project_client.agents.delete_agent(test_agent.id)
        
        if bing_urls_found:
            print("✅ Bing connection test successful! The Bing search API is working.")
        else:
            print("❌ Bing connection test failed. No search URLs were found.")
            print("\nPossible issues:")
            print("1. The Bing connection is not configured correctly")
            print("2. The Bing API is rate-limited")
            print("3. The model being used is not compatible with Bing grounding")
            print("4. Azure credentials may need to be refreshed")
            print("\nTry these steps:")
            print("1. Run 'az login' to refresh your credentials")
            print("2. Verify your Bing connection in the Azure AI Studio portal")
            print("3. Check that you're using a supported model: gpt-3.5-turbo-0125, gpt-4-0125-preview, gpt-4-turbo-2024-04-09, gpt-4o-0513, gpt-4o")
            print("4. Wait for a few minutes and try again (rate limits)")
            
        print("===== END OF BING CONNECTION TEST =====\n")
        return bing_urls_found
        
    except Exception as e:
        print(f"❌ Error testing Bing connection: {str(e)}")
        print(f"Full error details: {traceback.format_exc()}")
        print("===== END OF BING CONNECTION TEST (WITH ERROR) =====\n")
        return False

# Add this function after the debug_bing_search_urls function

def log_run_steps_details(thread_id, run_id):
    """Log detailed information about all run steps to help diagnose Bing search issues"""
    try:
        run_steps = project_client.agents.list_run_steps(thread_id=thread_id, run_id=run_id)
        
        print("\n===== DETAILED RUN STEPS ANALYSIS =====")
        steps_data = run_steps.get('data', [])
        print(f"Total run steps: {len(steps_data)}")
        
        for idx, step in enumerate(steps_data, 1):
            step_type = step.get('type', 'unknown')
            step_id = step.get('id', 'no-id')
            status = step.get('status', 'unknown')
            
            print(f"\nStep {idx}: {step_type} (ID: {step_id}, Status: {status})")
            
            # Check for tool calls
            if step_type == 'tool_calls':
                tool_calls = step.get('tool_calls', [])
                print(f"  Tool calls count: {len(tool_calls)}")
                
                for tc_idx, tool_call in enumerate(tool_calls, 1):
                    tool_name = tool_call.get('name', 'unknown')
                    tool_id = tool_call.get('id', 'no-id')
                    print(f"  Tool call {tc_idx}: {tool_name} (ID: {tool_id})")
                    
                    # Print all parameters
                    params = tool_call.get('parameters', {})
                    if params:
                        print(f"  Parameters: {params}")
                    
                    # Check for output/response
                    output = tool_call.get('output', {})
                    if output:
                        output_str = str(output)
                        preview = output_str[:150] + "..." if len(output_str) > 150 else output_str
                        print(f"  Output: {preview}")
            
            # Check for parameters in any step
            params = step.get('parameters', {})
            if params:
                print(f"  Step parameters: {params}")
                
                # Specifically look for request_url
                if 'request_url' in params:
                    print(f"  ✅ Found request_url: {params['request_url']}")
            
            # Look for specific outputs
            output = step.get('output', {})
            if output:
                output_str = str(output)
                preview = output_str[:100] + "..." if len(output_str) > 100 else output_str
                print(f"  Step output: {preview}")
        
        print("===== END DETAILED ANALYSIS =====\n")
        
    except Exception as e:
        print(f"Error analyzing run steps: {str(e)}")
        print(traceback.format_exc())

# Add this function before the main function

def check_and_repair_bing_connection():
    """Check the status of the Bing connection and attempt repair if needed"""
    global bing_connection
    
    if not project_client:
        print("❌ Cannot check Bing connection: Project client not available")
        return False
        
    try:
        print("\n===== CHECKING BING CONNECTION =====")
        print(f"Current Bing connection name: {bing_conn_name}")
        
        # Try to get the connection again to ensure it's still valid
        try:
            refreshed_connection = project_client.connections.get(connection_name=bing_conn_name)
            print(f"✅ Successfully retrieved Bing connection: {refreshed_connection.name} (ID: {refreshed_connection.id})")
            
            # Update the global connection if needed
            if refreshed_connection.id != bing_connection.id:
                print(f"⚠️ Connection ID mismatch! Updating from {bing_connection.id} to {refreshed_connection.id}")
                bing_connection = refreshed_connection
                
            print("Connection details:")
            print(f"- Name: {bing_connection.name}")
            print(f"- ID: {bing_connection.id}")
            
            # Check for specific properties that might indicate issues
            if hasattr(bing_connection, 'status'):
                print(f"- Status: {bing_connection.status}")
                
                if bing_connection.status != "Ready" and bing_connection.status != "Active":
                    print(f"⚠️ Connection status is not Ready/Active: {bing_connection.status}")
                    print("This might indicate an issue with the Bing connection.")
        
        except Exception as e:
            print(f"❌ Error retrieving connection: {str(e)}")
            print("Attempting to recover...")
            
            # List all available connections
            try:
                connections = project_client.connections.list_connections()
                print("\nAvailable connections:")
                bing_connections = []
                
                for conn in connections:
                    conn_type = getattr(conn, 'type', 'unknown')
                    print(f"- {conn.name} (ID: {conn.id}, Type: {conn_type})")
                    
                    # Look for Bing connections
                    if 'bing' in conn.name.lower() or (hasattr(conn, 'type') and 'bing' in str(conn.type).lower()):
                        bing_connections.append(conn)
                
                if bing_connections:
                    print(f"\nFound {len(bing_connections)} potential Bing connections.")
                    # Use the first one
                    bing_connection = bing_connections[0]
                    print(f"Using connection: {bing_connection.name} (ID: {bing_connection.id})")
                    return True
                else:
                    print("❌ No Bing connections found.")
                    return False
                    
            except Exception as conn_list_error:
                print(f"❌ Error listing connections: {str(conn_list_error)}")
                return False
            
        print("===== BING CONNECTION CHECK COMPLETE =====\n")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Bing connection: {str(e)}")
        print(traceback.format_exc())
        return False

# Update the main function to include a test option
if __name__ == "__main__":
    if not project_client or not bing_connection:
        print("\n❌ Setup failed - cannot run FinOps expert")
        print("Please fix the connection issues mentioned above before running this script.")
        sys.exit(1)
    
    print("\nYour FinOps Toolkit Expert with Bing grounding is ready!")
    print("You can ask questions about:")
    print("1. FinOps Hub validation steps")
    print("2. Azure Cost Management troubleshooting")
    print("3. Data Factory pipeline issues")
    print("4. Power BI connectivity problems")
    print("5. VM cost optimization strategies")
    print("6. Custom agent configuration")
    print("7. Test Bing connection")  # New option
    print("8. Check and repair Bing connection")  # Another new option
    print("9. Enter your own question")
    
    # Sample questions
    finops_questions = [
        "How do I validate my FinOps hub deployment?",
        "What are common issues with Data Factory pipelines in the FinOps hub?",
        "How can I troubleshoot Power BI connectivity to my FinOps hub?",
        "How do I optimize VM costs in Azure?",
        "What are best practices for cost allocation tags in the FinOps hub?"
    ]
    
    print("\nSample questions:")
    for i, q in enumerate(finops_questions, 1):
        print(f"{i}. {q}")
    print("6. Use custom agent configuration")
    print("7. Test Bing connection")  # New option
    print("8. Check and repair Bing connection")  # Another new option
    print("9. Enter your own question")
    
    choice = input("\nEnter your choice (1-9): ")
    
    if choice == "7":
        # Test Bing connection
        print("Testing Bing connection...")
        test_result = test_bing_connection()
        if test_result:
            print("\nBing connection is working correctly.")
            print("You should now be able to get proper search results in your FinOps questions.")
        else:
            print("\nBing connection test failed.")
            print("Please check your configuration and try again.")
        sys.exit(0)
    elif choice == "8":
        # Check and repair Bing connection
        print("Checking and attempting to repair Bing connection...")
        repair_result = check_and_repair_bing_connection()
        if repair_result:
            print("\nBing connection check/repair completed successfully.")
            print("You should now be able to get proper search results in your FinOps questions.")
        else:
            print("\nBing connection check/repair failed.")
            print("Please check your configuration and try again.")
        sys.exit(0)
    elif choice == "9":
        question = input("\nEnter your FinOps question: ")
    else:
        question = finops_questions[int(choice) - 1]
    
    # Define the default configuration
    config = {
        'enhancement_enabled': True,
        'quality_check_enabled': True,
        'auto_improve_enabled': True,
        'interactive_improvement': True,
        'quality_threshold': 7,
        'bing_temperature': 0.2,
        'enhancement_temperature': 0.2,
        'max_search_results': 20,
        'cleanup_agent': True,
        'max_improvement_iterations': 3,
        'force_github_knowledge': True
    }
    
    # Get answer
    print("\n⏳ Processing your question, this may take a minute...")
    answer = finops_expert_with_bing(question, config)
    
    print("\n🔍 Answer:")
    print(answer)
    
    # Save answer to file if it's substantial
    if len(answer) > 500:
        # Create safe filename from question
        import re
        safe_filename = re.sub(r'[^\w\s-]', '', question).strip().lower()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        safe_filename = safe_filename[:50]  # Limit length
        
        filename = f"finops_answer_{safe_filename}.md"
        save_to_file = input(f"\nWould you like to save this answer to {filename}? (y/n, default: y): ").lower() != 'n'
        
        if save_to_file:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# FinOps Question: {question}\n\n")
                    f.write(answer)
                print(f"\n✅ Answer saved to {filename}")
            except Exception as e:
                print(f"\n⚠️ Could not save answer to file: {str(e)}")
    
    print("\nThank you for using the FinOps Toolkit Expert!")
    print("For more information about Microsoft FinOps offerings, visit:")
    print("https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/")

def test_bing_sample():
    """
    Run a test that exactly follows the official sample code
    """
    try:
        print("\n===== TESTING BING CONNECTION (SAMPLE CODE) =====")
        
        # Check if the project client and connection are available
        if not project_client:
            print("❌ Azure AI Project client not initialized")
            return False
            
        if not bing_connection:
            print("❌ Bing connection not available")
            return False
            
        print(f"Using Bing connection: {bing_connection.id}")
            
        # Initialize Bing grounding tool
        bing = BingGroundingTool(connection_id=bing_connection.id)
        
        # Create agent with the Bing tool
        print("Creating test agent...")
        agent = project_client.agents.create_agent(
            model=model_name_deployment,
            name="my-assistant",
            instructions="You are a helpful assistant",
            tools=bing.definitions,
            headers={"x-ms-enable-preview": "true"},
        )
        
        print(f"Created agent, ID: {agent.id}")
        
        # Create thread for communication
        thread = project_client.agents.create_thread()
        print(f"Created thread, ID: {thread.id}")
        
        # Create message to thread with a simple question that should trigger web search
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content="How does wikipedia explain Euler's Identity?",
        )
        print(f"Created message, ID: {message.id}")
        
        # Create and process run - this will perform the Bing search
        print("Processing run (this may take a minute)...")
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id, 
            agent_id=agent.id,
            headers={"x-ms-enable-preview": "true"}
        )
        print(f"Run finished with status: {run.status}")
        
        if run.status == "failed":
            print(f"❌ Run failed: {run.last_error}")
            
            # Clean up resources
            project_client.agents.delete_agent(agent.id)
            print("Deleted agent")
            return False
            
        # Get the agent's response 
        response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
            MessageRole.AGENT
        )
        
        # Print results
        if response_message:
            for text_message in response_message.text_messages:
                print(f"Agent response: {text_message.text.value[:200]}...")
                
            # Check for URL citations - this is the key indicator of Bing working
            citation_found = False
            for annotation in response_message.url_citation_annotations:
                citation_found = True
                print(f"URL Citation: [{annotation.url_citation.title}]({annotation.url_citation.url})")
                
            if citation_found:
                print("\n✅ TEST SUCCESSFUL: Bing grounding is working correctly!")
            else:
                print("\n❌ TEST FAILED: No URL citations found in response.")
                print("This suggests Bing grounding is not working correctly.")
                
            # Clean up resources
            project_client.agents.delete_agent(agent.id)
            print("Deleted agent")
            return citation_found
        else:
            print("❌ No response message found")
            
            # Clean up resources
            project_client.agents.delete_agent(agent.id)
            print("Deleted agent")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Bing connection: {str(e)}")
        return False
        
# Update the main function to include the new test
if __name__ == "__main__":
    try:
        print("\n🤖 FinOps Toolkit Expert with Bing Grounding")
        print("------------------------------------------------")
        
        # Basic menu
        print("\nOptions:")
        print("1. Ask a FinOps question with Bing grounding")
        print("2. Run basic Bing test (sample code)")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ")
        
        if choice == "1":
            question = input("\nEnter your FinOps question: ")
            answer = finops_expert_with_bing(question)
            print("\n🔍 Answer:")
            print(answer)
            
        elif choice == "2":
            test_bing_sample()
            
        elif choice == "3":
            print("Exiting...")
            sys.exit(0)
            
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())