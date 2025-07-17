#!/usr/bin/env python3
"""
Test script to verify OpenAI API connection with current settings
"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        print("Testing OpenAI API connection...")
        print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
        print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        
        # Validate environment variables
        api_key = os.getenv("AZURE_OPENAI_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        if not all([api_key, endpoint, api_version, deployment_name]):
            raise ValueError("Missing required environment variables")
        
        # Initialize client
        client = AzureOpenAI(
            api_key=api_key,  # type: ignore
            azure_endpoint=endpoint,  # type: ignore
            api_version=api_version,  # type: ignore
        )
        
        # Test API call
        print("\nMaking test API call...")
        response = client.chat.completions.create(
            model=deployment_name,  # type: ignore
            messages=[
                {"role": "user", "content": "Hello! Just testing the connection."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ SUCCESS: OpenAI API connection works!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: OpenAI API connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    exit(0 if success else 1) 