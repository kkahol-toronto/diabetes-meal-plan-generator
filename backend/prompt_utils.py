import json
import os
from typing import Dict, Any

# Load prompts from JSON file
def load_prompts() -> Dict[str, Any]:
    """Load prompts from prompts.json file"""
    prompts_file = os.path.join(os.path.dirname(__file__), 'prompts.json')
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: prompts.json not found at {prompts_file}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing prompts.json: {e}")
        return {}

# Get formatted prompt
def get_prompt(prompt_key: str, **kwargs) -> Dict[str, str]:
    """
    Get a formatted prompt from the prompts.json file
    
    Args:
        prompt_key: The key of the prompt in prompts.json
        **kwargs: Variables to format into the prompt templates
        
    Returns:
        Dict with 'system' and 'user' keys containing formatted prompts
    """
    prompts = load_prompts()
    
    if prompt_key not in prompts:
        raise KeyError(f"Prompt key '{prompt_key}' not found in prompts.json")
    
    prompt_data = prompts[prompt_key]
    
    # Format system and user templates with provided kwargs
    system_prompt = prompt_data.get('system', '').format(**kwargs)
    user_prompt = prompt_data.get('user_template', '').format(**kwargs)
    
    return {
        'system': system_prompt,
        'user': user_prompt
    }

# Get just the system prompt
def get_system_prompt(prompt_key: str, **kwargs) -> str:
    """Get just the formatted system prompt"""
    prompts = load_prompts()
    
    if prompt_key not in prompts:
        raise KeyError(f"Prompt key '{prompt_key}' not found in prompts.json")
    
    system_template = prompts[prompt_key].get('system', '')
    return system_template.format(**kwargs)

# Get just the user prompt
def get_user_prompt(prompt_key: str, **kwargs) -> str:
    """Get just the formatted user prompt"""
    prompts = load_prompts()
    
    if prompt_key not in prompts:
        raise KeyError(f"Prompt key '{prompt_key}' not found in prompts.json")
    
    user_template = prompts[prompt_key].get('user_template', '')
    return user_template.format(**kwargs) 