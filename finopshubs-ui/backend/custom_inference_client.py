# Create a custom implementation of InferenceClient
from azure.core.credentials import AzureKeyCredential
import requests
import json

class InferenceClient:
    def __init__(self, endpoint, api_key):
        self.endpoint = endpoint
        self.api_key = api_key
        self.credential = AzureKeyCredential(api_key)
    
    def get_chat_completions(self, deployment_name, messages, max_tokens=None, temperature=None):
        url = f"{self.endpoint}/deployments/{deployment_name}/chat/completions?api-version=2023-05-15"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        body = {
            "messages": messages
        }
        
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        
        if temperature is not None:
            body["temperature"] = temperature
        
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        # Create a response object that mimics the Azure SDK's response
        class ChatCompletionsResponse:
            def __init__(self, data):
                self.choices = []
                for choice in data.get("choices", []):
                    self.choices.append(Choice(choice))
        
        class Choice:
            def __init__(self, data):
                self.message = Message(data.get("message", {}))
                
        class Message:
            def __init__(self, data):
                self.content = data.get("content", "")
        
        return ChatCompletionsResponse(response.json())
