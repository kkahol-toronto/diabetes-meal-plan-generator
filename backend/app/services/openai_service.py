import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional

from config import client

async def robust_openai_call(
    messages: List[Dict[str, str]], 
    max_tokens: int = 2000, 
    temperature: float = 0.7,
    response_format: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    timeout: int = 60,
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
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60 seconds
                print(f"[{context}] Rate limit detected, waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            
            # Check if this is a timeout error
            if "timeout" in error_msg.lower():
                print(f"[{context}] Timeout detected on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 60))  # Exponential backoff, max 60 seconds
                    continue
            
            # For other errors, wait a bit before retrying
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60 seconds
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

def robust_json_parse(json_string: str, context: str = "json_parse") -> Dict[str, Any]:
    """
    Parse JSON string with better error handling and fallback mechanisms.
    
    Args:
        json_string: The JSON string to parse
        context: Context string for logging
        
    Returns:
        Dict containing parsed JSON or error information
    """
    try:
        # First, try to parse as-is
        return {"success": True, "data": json.loads(json_string)}
    except json.JSONDecodeError as e:
        print(f"[{context}] Initial JSON parse failed: {e}")
        
        # Try to extract JSON from the string (in case there's extra text)
        try:
            # Find the first { and last }
            start_idx = json_string.find('{')
            end_idx = json_string.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                extracted_json = json_string[start_idx:end_idx]
                return {"success": True, "data": json.loads(extracted_json)}
        except:
            pass
            
        # Try to clean up common JSON issues
        try:
            # Remove common markdown formatting
            cleaned = json_string.replace('```json', '').replace('```', '')
            cleaned = cleaned.strip()
            
            # Fix common trailing comma issues
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)
            
            return {"success": True, "data": json.loads(cleaned)}
        except:
            pass
            
        # Return error if all parsing attempts failed
        return {
            "success": False,
            "error": f"JSON parsing failed: {str(e)}",
            "raw_content": json_string[:500] + "..." if len(json_string) > 500 else json_string
        }

def generate_fallback_meal_plan(user_profile: dict, days: int = 7) -> dict:
    """
    Generate a fallback meal plan when OpenAI API fails.
    This provides a safe, diabetes-friendly meal plan based on user profile.
    """
    print("[FALLBACK] Generating fallback meal plan...")
    
    # Get dietary restrictions for safe fallback
    dietary_restrictions = user_profile.get('dietaryRestrictions', [])
    allergies = user_profile.get('allergies', [])
    diet_type = user_profile.get('dietType', [])
    
    # Check if user is vegetarian
    is_vegetarian = any('vegetarian' in str(restriction).lower() for restriction in dietary_restrictions + diet_type)
    
    # Check for allergies
    has_egg_allergy = any('egg' in str(allergy).lower() for allergy in allergies)
    has_dairy_allergy = any('dairy' in str(allergy).lower() or 'milk' in str(allergy).lower() for allergy in allergies)
    has_gluten_allergy = any('gluten' in str(allergy).lower() or 'wheat' in str(allergy).lower() for allergy in allergies)
    
    # Safe breakfast options
    breakfast_options = [
        "Oatmeal with berries and cinnamon",
        "Greek yogurt with nuts and seeds",
        "Whole grain toast with avocado",
        "Smoothie with spinach and banana",
        "Chia seed pudding with fruit",
        "Quinoa breakfast bowl with vegetables",
        "Almond butter on whole grain toast"
    ]
    
    # Safe lunch options
    lunch_options = [
        "Quinoa salad with mixed vegetables",
        "Lentil soup with whole grain bread",
        "Chickpea curry with brown rice",
        "Vegetable stir-fry with tofu",
        "Bean and vegetable wrap",
        "Hummus with vegetable sticks",
        "Stuffed bell peppers with quinoa"
    ]
    
    # Safe dinner options
    dinner_options = [
        "Baked sweet potato with black beans",
        "Vegetable curry with brown rice",
        "Grilled vegetables with quinoa",
        "Lentil dal with steamed vegetables",
        "Stuffed zucchini with vegetables",
        "Roasted vegetables with chickpeas",
        "Vegetable soup with whole grain bread"
    ]
    
    # Safe snack options
    snack_options = [
        "Mixed nuts and seeds",
        "Apple slices with almond butter",
        "Carrot sticks with hummus",
        "Berries with Greek yogurt",
        "Cucumber slices with tahini",
        "Roasted chickpeas",
        "Homemade trail mix"
    ]
    
    # Adjust for non-vegetarian users
    if not is_vegetarian:
        lunch_options.extend([
            "Grilled chicken salad with olive oil dressing",
            "Baked salmon with steamed vegetables",
            "Turkey and vegetable wrap"
        ])
        dinner_options.extend([
            "Grilled chicken with roasted vegetables",
            "Baked fish with quinoa and vegetables",
            "Lean beef stir-fry with brown rice"
        ])
    
    # Adjust for allergies
    if has_egg_allergy:
        breakfast_options = [opt for opt in breakfast_options if 'egg' not in opt.lower()]
    
    if has_dairy_allergy:
        breakfast_options = [opt for opt in breakfast_options if 'yogurt' not in opt.lower()]
        snack_options = [opt for opt in snack_options if 'yogurt' not in opt.lower()]
    
    if has_gluten_allergy:
        breakfast_options = [opt for opt in breakfast_options if 'toast' not in opt.lower() and 'bread' not in opt.lower()]
        lunch_options = [opt for opt in lunch_options if 'bread' not in opt.lower() and 'wrap' not in opt.lower()]
        dinner_options = [opt for opt in dinner_options if 'bread' not in opt.lower()]
    
    # Ensure we have enough options
    while len(breakfast_options) < days:
        breakfast_options.extend(breakfast_options)
    while len(lunch_options) < days:
        lunch_options.extend(lunch_options)
    while len(dinner_options) < days:
        dinner_options.extend(dinner_options)
    while len(snack_options) < days:
        snack_options.extend(snack_options)
    
    # Generate meal plan
    meal_plan = {
        "breakfast": breakfast_options[:days],
        "lunch": lunch_options[:days],
        "dinner": dinner_options[:days],
        "snacks": snack_options[:days],
        "dailyCalories": int(user_profile.get('calorieTarget', 2000)),
        "macronutrients": {
            "protein": 100,
            "carbs": 250,
            "fats": 70
        }
    }
    
    print(f"[FALLBACK] Generated fallback meal plan with {days} days")
    return meal_plan

def generate_fallback_recipes(meal_names: List[str]) -> List[dict]:
    """
    Generate fallback recipes when OpenAI API fails.
    This provides basic recipes for common meals.
    """
    print(f"[FALLBACK] Generating fallback recipes for {len(meal_names)} meals...")
    
    # Common diabetes-friendly recipes
    recipe_templates = {
        "oatmeal": {
            "name": "Diabetes-Friendly Oatmeal",
            "ingredients": [
                "1/2 cup rolled oats",
                "1 cup water or unsweetened almond milk",
                "1/4 cup fresh berries",
                "1 tbsp chopped nuts",
                "1/2 tsp cinnamon",
                "1 tsp vanilla extract"
            ],
            "instructions": [
                "Bring water or almond milk to a boil",
                "Add oats and reduce heat to medium",
                "Cook for 5-7 minutes, stirring occasionally",
                "Add cinnamon and vanilla",
                "Top with berries and nuts",
                "Serve warm"
            ],
            "nutritional_info": {
                "calories": 250,
                "protein": 8,
                "carbs": 42,
                "fat": 6
            }
        },
        "quinoa salad": {
            "name": "Diabetes-Friendly Quinoa Salad",
            "ingredients": [
                "1 cup cooked quinoa",
                "1 cup mixed vegetables (cucumber, tomatoes, bell peppers)",
                "2 tbsp olive oil",
                "1 tbsp lemon juice",
                "1/4 cup fresh herbs (parsley, mint)",
                "Salt and pepper to taste"
            ],
            "instructions": [
                "Cook quinoa according to package instructions",
                "Let quinoa cool completely",
                "Dice vegetables into small pieces",
                "Mix quinoa with vegetables",
                "Whisk together olive oil and lemon juice",
                "Add dressing to salad and toss",
                "Season with salt, pepper, and herbs"
            ],
            "nutritional_info": {
                "calories": 320,
                "protein": 12,
                "carbs": 45,
                "fat": 12
            }
        },
        "vegetable soup": {
            "name": "Diabetes-Friendly Vegetable Soup",
            "ingredients": [
                "2 cups mixed vegetables (carrots, celery, onions)",
                "4 cups low-sodium vegetable broth",
                "1 can diced tomatoes",
                "1 cup leafy greens (spinach or kale)",
                "1 tsp herbs (thyme, basil)",
                "Salt and pepper to taste"
            ],
            "instructions": [
                "Heat oil in large pot over medium heat",
                "Add onions and cook until soft",
                "Add other vegetables and cook for 5 minutes",
                "Add broth and diced tomatoes",
                "Bring to boil, then simmer for 20 minutes",
                "Add leafy greens and herbs",
                "Season with salt and pepper"
            ],
            "nutritional_info": {
                "calories": 150,
                "protein": 5,
                "carbs": 25,
                "fat": 3
            }
        }
    }
    
    fallback_recipes = []
    
    for meal_name in meal_names:
        meal_lower = meal_name.lower()
        
        # Try to match with existing templates
        if "oatmeal" in meal_lower:
            recipe = recipe_templates["oatmeal"].copy()
            recipe["name"] = meal_name
        elif "quinoa" in meal_lower or "salad" in meal_lower:
            recipe = recipe_templates["quinoa salad"].copy()
            recipe["name"] = meal_name
        elif "soup" in meal_lower:
            recipe = recipe_templates["vegetable soup"].copy()
            recipe["name"] = meal_name
        else:
            # Generic fallback recipe
            recipe = {
                "name": meal_name,
                "ingredients": [
                    "2 cups mixed vegetables",
                    "1 cup whole grains (quinoa, brown rice, or oats)",
                    "1 tbsp healthy oil (olive or avocado)",
                    "Herbs and spices to taste"
                ],
                "instructions": [
                    "Prepare whole grains according to package instructions",
                    "Cook vegetables until tender",
                    "Combine ingredients",
                    "Season with herbs and spices",
                    "Serve warm"
                ],
                "nutritional_info": {
                    "calories": 280,
                    "protein": 10,
                    "carbs": 40,
                    "fat": 8
                }
            }
        
        fallback_recipes.append(recipe)
    
    print(f"[FALLBACK] Generated {len(fallback_recipes)} fallback recipes")
    return fallback_recipes 