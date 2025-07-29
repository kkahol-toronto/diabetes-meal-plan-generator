"""
OpenAI Service Module
Handles Azure OpenAI API interactions with robust error handling and retry logic.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

from constants import (
    DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT,
    MAX_BACKOFF_SECONDS, BASE_BACKOFF_MULTIPLIER
)

# Load environment variables
load_dotenv(override=True)

# Configure OpenAI for APIM Gateway
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),  # This will be used as Ocp-Apim-Subscription-Key
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    default_headers={
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_OPENAI_KEY")
    }
)

async def robust_openai_call(
    messages: List[Dict[str, str]], 
    max_tokens: int = DEFAULT_MAX_TOKENS, 
    temperature: float = DEFAULT_TEMPERATURE,
    response_format: Optional[Dict[str, str]] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT,
    context: str = "openai_call"
) -> Dict[str, Any]:
    """
    Robust OpenAI API call with retry logic, timeout handling, and comprehensive error handling.
    
    Args:
        messages: List of message dictionaries for the chat completion
        max_tokens: Maximum tokens for the response
        temperature: Temperature for response generation
        response_format: Optional response format (e.g., {"type": "json_object"})
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for each API call
        context: Context string for logging purposes
        
    Returns:
        Dict containing the API response or error information
    """
    
    for attempt in range(max_retries):
        try:
            print(f"[{context}] Attempt {attempt + 1}/{max_retries} - Calling OpenAI API...")
            
            # Prepare the API call parameters
            api_params = {
                "model": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": timeout
            }
            
            # Add response format if specified
            if response_format:
                api_params["response_format"] = response_format
                
            # Make the API call
            response = client.chat.completions.create(**api_params)
            
            # Validate the response
            if not response.choices or not response.choices[0].message:
                raise ValueError("Empty response from OpenAI API")
                
            raw_content = response.choices[0].message.content
            if not raw_content or not raw_content.strip():
                raise ValueError("Empty content in OpenAI response")
                
            print(f"[{context}] API call successful on attempt {attempt + 1}")
            
            return {
                "success": True,
                "content": raw_content.strip(),
                "usage": response.usage.model_dump() if response.usage else None,
                "attempt": attempt + 1
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[{context}] Attempt {attempt + 1} failed: {error_msg}")
            
            # Check if this is a rate limit error
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                wait_time = min(BASE_BACKOFF_MULTIPLIER ** attempt, MAX_BACKOFF_SECONDS)  # Exponential backoff
                print(f"[{context}] Rate limit detected, waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            
            # Check if this is a timeout error
            if "timeout" in error_msg.lower():
                print(f"[{context}] Timeout detected on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(min(BASE_BACKOFF_MULTIPLIER ** attempt, MAX_BACKOFF_SECONDS))  # Exponential backoff
                    continue
            
            # For other errors, wait a bit before retrying
            if attempt < max_retries - 1:
                wait_time = min(BASE_BACKOFF_MULTIPLIER ** attempt, MAX_BACKOFF_SECONDS)  # Exponential backoff
                print(f"[{context}] Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                # Final attempt failed
                print(f"[{context}] All {max_retries} attempts failed. Last error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "attempts": max_retries
                }
                
    # This should never be reached, but just in case
    return {
        "success": False,
        "error": "Maximum retries exceeded",
        "attempts": max_retries
    }

def get_openai_client():
    """
    Get the configured Azure OpenAI client instance.
    
    Returns:
        AzureOpenAI: Configured client instance
    """
    return client