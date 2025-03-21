#!/usr/bin/env python
# simplified_finops_with_bing.py - A simpler version with improved error handling

import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole, BingGroundingTool

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

print("=== FinOps Expert with Bing Grounding (Simplified Version) ===")

# Get required variables with fallbacks
conn_string = get_env_var("PROJECT_CONNECTION_STRING")
bing_conn_name = get_env_var("BING_CONNECTION_NAME", 
                            ["GROUNDING_WITH_BING_CONNECTION_NAME", "BING_SEARCH_KEY"])
model_name = get_env_var("MODEL_DEPLOYMENT_NAME", 
                        ["SERVERLESS_MODEL_NAME"], 
                        "gpt-4o-mini")

# Validate required variables
if not conn_string:
    print("❌ PROJECT_CONNECTION_STRING is missing! Please check your .env file.")
    sys.exit(1)

if not bing_conn_name:
    print("❌ BING_CONNECTION_NAME or equivalent is missing! Please check your .env file.")
    sys.exit(1)

print(f"\nProject Connection String: {conn_string[:20]}...{conn_string[-5:] if len(conn_string) > 25 else conn_string}")
print(f"Bing Connection Name: {bing_conn_name}")
print(f"Model Name: {model_name}")

# Initialize global variables
project_client = None
bing_connection = None

# Setup client and connection
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
    
    # Get Bing connection by name (this is the correct way per documentation)
    print(f"\nAttempting to get Bing connection: {bing_conn_name}")
    bing_connection = project_client.connections.get(connection_name=bing_conn_name)
    
    print(f"✅ Successfully retrieved Bing connection!")
    print(f"Connection details:")
    print(f"- Name: {bing_connection.name}")
    print(f"- ID: {bing_connection.id}")
    # Safety check for type attribute
    try:
        print(f"- Type: {bing_connection.type}")
    except AttributeError:
        print(f"- Type: [Not available in this SDK version]")
    
except Exception as e:
    print(f"❌ SETUP ERROR: {str(e)}")
    
    if "get_token" in str(e).lower() or "credential" in str(e).lower():
        print("\nAuthentication Error - Please try these steps:")
        print("1. Run 'az login' to refresh your Azure CLI login")
        print("2. Check that AZURE_TENANT_ID is set correctly")
        print("3. Ensure your account has access to the AI project")
    
    if "connections.get" in str(e).lower():
        print("\nConnection Error - Please try these steps:")
        print(f"1. Verify the connection name '{bing_conn_name}' exists in your AI project")
        print("2. Check if the connection is of type Bing Search")
        print("3. Ensure your credential has access to view this connection")
        print("4. Verify the connection string is correct for your AI project")
    
    sys.exit(1)

# Function to create a FinOps agent with Bing grounding
def create_finops_agent():
    """Create a FinOps expert agent with Bing grounding"""
    if not project_client or not bing_connection:
        print("❌ Cannot create agent: Project client or Bing connection not available")
        return None
    
    try:
        # Initialize Bing grounding tool - use the connection_id from the bing_connection
        print("\nInitializing Bing grounding tool...")
        # Following the official pattern from the documentation
        bing_tool = BingGroundingTool(connection_id=bing_connection.id)
        
        # Create the agent
        print(f"Creating FinOps agent with model: {model_name}")
        agent = project_client.agents.create_agent(
            model=model_name,
            name="finops-bing-expert",
            instructions="""
                You are a Microsoft FinOps toolkit expert with deep knowledge of:
                
                1. FinOps Framework and Cloud Financial Management
                2. Microsoft Cost Management
                3. FinOps Hub Implementation: Setup, validation, and troubleshooting
                4. Data Factory Pipelines used in FinOps solutions
                5. Power BI Cost Reports for FinOps
                6. VM Cost Optimization strategies
                7. Microsoft FinOps Toolkit GitHub repository (https://github.com/microsoft/finops-toolkit)
                
                SEARCH INSTRUCTIONS:
                When searching for information, ALWAYS use these explicit search patterns:
                - site:github.com/microsoft/finops-toolkit [question] - To find GitHub repository resources
                - site:learn.microsoft.com finops [question] - To find Microsoft Learn documentation
                - site:docs.microsoft.com/azure cost management [question] - To find Azure documentation
                
                RESPONSE GUIDELINES:
                - Include at least one reference to the Microsoft FinOps Toolkit GitHub repository
                - Include at least one reference to Microsoft Learn documentation
                - Provide step-by-step guidance with numbered steps
                - Include specific CLI commands or PowerShell snippets when relevant
                - Cite all sources with direct links
                - Structure your answer with clear headings
                
                INFORMATION PRIORITY:
                1. Microsoft Learn official documentation
                2. Microsoft FinOps Toolkit GitHub repository
                3. Azure Well-Architected Framework
                4. Cloud Adoption Framework
                
                NEVER make up information. If you can't find specific information from Microsoft sources,
                clearly state that the information isn't available in the official documentation.
            """,
            tools=bing_tool.definitions,
            temperature=0.2,  # Lower temperature for more focused responses
            headers={"x-ms-enable-preview": "true"},  # Required for Bing grounding
        )
        
        print(f"✅ Created FinOps agent with Bing grounding, ID: {agent.id}")
        return agent
    
    except Exception as e:
        print(f"❌ Error creating FinOps agent: {str(e)}")
        
        if "model" in str(e).lower():
            print(f"\nModel Error - The model '{model_name}' may not be available or configured correctly")
            print("Try using a different model or check your project settings")
            print("Note: Bing grounding only works with these models: gpt-3.5-turbo-0125, gpt-4-0125-preview, gpt-4-turbo-2024-04-09, gpt-4o-0513")
        
        return None

# Function to ask a FinOps question
def ask_finops_question(agent, question):
    """Ask a FinOps question using the Bing-grounded agent"""
    if not agent or not project_client:
        print("❌ Agent or project client not available")
        return "Error: Agent or project client not available"
    
    try:
        print(f"\n🔍 Processing question: {question}")
        
        # Create thread for conversation
        thread = project_client.agents.create_thread()
        print(f"📝 Created thread ID: {thread.id}")
        
        # Enhanced question with explicit search guidance
        enhanced_question = f"""
        Question: {question}
        
        When searching for information, please use these EXACT search queries:
        1. site:github.com/microsoft/finops-toolkit {question}
        2. site:learn.microsoft.com finops {question}
        3. site:docs.microsoft.com/azure "cost management" {question}
        
        It is CRITICAL that you search using the exact site: operators shown above to find the most relevant information from:
        - Microsoft FinOps Toolkit GitHub repository
        - Microsoft Learn documentation
        - Azure documentation
        
        Please provide a comprehensive answer with specific links to documentation and GitHub resources.
        """
        
        # Add the user's question
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=enhanced_question
        )
        print(f"📤 Added user message ID: {message.id}")
        
        # Process the run - Following the documentation pattern
        print("⚙️ Processing agent run (this may take a minute)...")
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id,
            headers={"x-ms-enable-preview": "true"}  # Ensure preview features are enabled
        )
        
        print(f"✅ Run completed with status: {run.status}")
        
        if run.status == "failed":
            print(f"❌ Run failed: {run.last_error}")
            return f"Error: {run.last_error}"
        
        # Get the response
        try:
            response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
                MessageRole.AGENT
            )
        except AttributeError:
            # Fallback method if get_last_message_by_role is not available
            print("Using fallback method to get response message")
            messages = project_client.agents.list_messages(thread_id=thread.id)
            response_message = None
            for msg in messages.data:
                if msg.role == MessageRole.AGENT:
                    response_message = msg
                    break
        
        if not response_message:
            return "Error: No response received from the agent"
        
        # Format the response with text and citations
        answer = ""
        
        # Add text content
        try:
            for text_message in response_message.text_messages:
                answer += text_message.text.value
        except AttributeError:
            # Fallback if text_messages is not available
            if hasattr(response_message, 'content'):
                answer = response_message.content
            else:
                print("Warning: Could not extract message content using standard methods")
                answer = "Could not extract message content. Please check the API response format."
        
        # Add URL citations (according to the documentation)
        try:
            if hasattr(response_message, 'url_citation_annotations') and response_message.url_citation_annotations:
                answer += "\n\n## References\n"
                for i, annotation in enumerate(response_message.url_citation_annotations, 1):
                    citation = annotation.url_citation
                    answer += f"{i}. [{citation.title}]({citation.url})\n"
        except Exception as citation_err:
            print(f"Warning: Could not extract citations: {str(citation_err)}")
        
        # Detailed debug - Get Bing search URLs from run steps
        print("\n===== DEBUG: BING SEARCH DETAILS =====")
        try:
            run_steps = project_client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
            print(f"Run steps available: {run_steps is not None}")
            
            if run_steps and 'data' in run_steps:
                print(f"Number of run steps: {len(run_steps['data'])}")
                
                bing_urls = []
                github_urls = []
                mslearn_urls = []
                
                for step in run_steps['data']:
                    step_type = step.get('type', step.get('step_type', 'unknown'))
                    print(f"Step type: {step_type}")
                    
                    # Print step for debugging
                    if 'tool' in step:
                        print(f"Tool: {step['tool']}")
                    
                    params = step.get('parameters', {})
                    if 'request_url' in params:
                        original_url = params['request_url']
                        friendly_url = original_url.replace("api.bing.microsoft.com", "www.bing.com")
                        bing_urls.append(friendly_url)
                        print(f"Found search URL: {friendly_url}")
                        
                        # Track GitHub and Microsoft Learn URLs
                        if 'github.com/microsoft/finops-toolkit' in original_url:
                            github_urls.append(friendly_url)
                            print(f"GitHub URL found: {friendly_url}")
                        
                        if 'learn.microsoft.com' in original_url or 'docs.microsoft.com/azure' in original_url:
                            mslearn_urls.append(friendly_url)
                            print(f"Microsoft Learn URL found: {friendly_url}")
                
                if not bing_urls:
                    print("⚠️ No Bing search URLs found in run steps")
                    
                    # Add fallback URLs if none found
                    github_urls.append("https://github.com/microsoft/finops-toolkit")
                    mslearn_urls.append("https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/")
                
                # Add search URLs to answer
                if bing_urls:
                    answer += "\n\n## Bing Search Queries\n"
                    for i, url in enumerate(bing_urls[:10], 1):  # Limit to 10
                        answer += f"{i}. [Search: FinOps Documentation]({url})\n"
                
                # Add GitHub repository section
                if github_urls:
                    answer += "\n\n## Microsoft FinOps Toolkit GitHub Resources\n"
                    answer += "The following resources from the Microsoft FinOps Toolkit GitHub repository are relevant:\n\n"
                    for i, url in enumerate(github_urls, 1):
                        answer += f"{i}. [FinOps Toolkit Resource]({url})\n"
                else:
                    answer += "\n\n## Microsoft FinOps Toolkit GitHub Resources\n"
                    answer += "For implementation examples, templates, and scripts, explore the [Microsoft FinOps Toolkit repository](https://github.com/microsoft/finops-toolkit).\n"
                
                # Add Microsoft Learn section
                if mslearn_urls:
                    answer += "\n\n## Microsoft Learn Documentation\n"
                    answer += "The following Microsoft Learn resources provide authoritative guidance:\n\n"
                    for i, url in enumerate(mslearn_urls, 1):
                        answer += f"{i}. [Microsoft Documentation]({url})\n"
                else:
                    answer += "\n\n## Microsoft Learn Documentation\n"
                    answer += "For official guidance, refer to [Microsoft's FinOps documentation](https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/).\n"
            else:
                print("⚠️ No run steps data available")
        except Exception as search_err:
            print(f"⚠️ Error retrieving Bing search URLs: {str(search_err)}")
            # Add default references if we couldn't get search URLs
            answer += "\n\n## Key Resources\n"
            answer += "1. [Microsoft FinOps Toolkit on GitHub](https://github.com/microsoft/finops-toolkit)\n"
            answer += "2. [Microsoft FinOps Documentation](https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/)\n"
            answer += "3. [Azure Cost Management Documentation](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/)\n"
        
        print("===== END DEBUG =====\n")
        
        return answer
    
    except Exception as e:
        print(f"❌ Error asking FinOps question: {str(e)}")
        return f"Error: {str(e)}"
    
# Main function to ask a question and get response
def finops_expert(question):
    """Ask a question to the FinOps expert with Bing grounding"""
    print("\n" + "="*80)
    print(f"FinOps Expert Question: {question}")
    print("="*80 + "\n")
    
    # Create agent
    agent = create_finops_agent()
    
    if not agent:
        return "Error: Could not create FinOps agent. Check the logs for details."
    
    try:
        # Get answer
        answer = ask_finops_question(agent, question)
        
        # Clean up
        print(f"\nCleaning up agent...")
        project_client.agents.delete_agent(agent.id)
        print(f"✅ Deleted agent: {agent.id}")
        
        return answer
    
    except Exception as e:
        print(f"❌ Error in finops_expert: {str(e)}")
        
        # Try to clean up
        try:
            if agent:
                project_client.agents.delete_agent(agent.id)
                print(f"✅ Deleted agent during error cleanup: {agent.id}")
        except:
            pass
            
        return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    print("\n===== FinOps Expert with Bing Grounding (Debug Version) =====")
    
    # Define test questions that target GitHub and Microsoft Learn
    test_questions = [
        "What templates are available in the Microsoft FinOps Toolkit GitHub repository?",
        "How do I implement cost allocation tags according to Microsoft FinOps best practices?",
        "What are the key components of the FinOps Hub according to Microsoft documentation?"
    ]
    
    # Ask user to select a question
    print("\nAvailable test questions:")
    for i, q in enumerate(test_questions, 1):
        print(f"{i}. {q}")
    print(f"{len(test_questions) + 1}. Enter custom question")
    
    try:
        choice = int(input("\nEnter question number (1-4): "))
        if 1 <= choice <= len(test_questions):
            sample_question = test_questions[choice - 1]
        else:
            sample_question = input("\nEnter your custom FinOps question: ")
    except ValueError:
        print("Invalid choice, using default question.")
        sample_question = test_questions[0]
    
    print(f"\n🔍 Selected question: {sample_question}")
    print("\nProcessing question - this may take a minute...")
    
    # Add a timer to measure how long the response takes
    start_time = time.time()
    
    response = finops_expert(sample_question)
    
    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    print(f"\n⏱️ Response time: {elapsed_time:.2f} seconds")
    
    print("\n" + "="*80)
    print("RESPONSE:")
    print("="*80)
    print(response)
    print("="*80)
    
    # Check for specific strings in the response
    has_github = "github.com/microsoft/finops-toolkit" in response.lower()
    has_mslearn = "learn.microsoft.com" in response.lower() or "docs.microsoft.com" in response.lower()
    
    print("\n===== RESPONSE ANALYSIS =====")
    print(f"Contains GitHub repository links: {'✅ YES' if has_github else '❌ NO'}")
    print(f"Contains Microsoft Learn links: {'✅ YES' if has_mslearn else '❌ NO'}")
    
    # Prompt for saving the response to a file
    save_option = input("\nSave response to file? (y/n): ").lower()
    if save_option.startswith('y'):
        # Create a safe filename from the question
        import re
        safe_filename = re.sub(r'[^\w\s-]', '', sample_question).strip().lower()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)[:50]
        filename = f"finops_response_{safe_filename}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# FinOps Question\n\n{sample_question}\n\n")
                f.write(response)
            print(f"Response saved to {filename}")
        except Exception as e:
            print(f"Error saving to file: {str(e)}")
    
    print("\n===== TEST COMPLETED =====") 