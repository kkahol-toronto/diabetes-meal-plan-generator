from fastapi import APIRouter, HTTPException, Depends, status, Request as FastAPIRequest, Body
from fastapi.responses import FileResponse
from typing import Dict, Any, List
import os
import json
import traceback
from datetime import datetime, timedelta
import uuid

# Import models
from models import User

# Import utilities
from utils import robust_json_parse

# Import constants
from constants import (
    DEFAULT_CALORIE_TARGET, MEAL_PLAN_MAX_TOKENS, RECIPE_MAX_TOKENS,
    CREATIVE_TEMPERATURE, PRECISE_TEMPERATURE, DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT,
    BREAKFAST_OPTIONS, LUNCH_OPTIONS, DINNER_OPTIONS, SNACK_OPTIONS,
    NON_VEG_LUNCH_ADDITIONS, NON_VEG_DINNER_ADDITIONS, RECIPE_TEMPLATES
)

# Import database functions
from database import (
    get_user_by_email, user_container, interactions_container,
    save_meal_plan, get_user_meal_plans, get_meal_plan_by_id,
    view_meal_plans, delete_all_user_meal_plans, delete_meal_plan_by_id
)

# Import auth dependency
from routers.auth import get_current_user

# Import OpenAI client (assuming it's available globally or will be imported)
import openai
from openai import AzureOpenAI

router = APIRouter()

# Initialize Azure OpenAI client for APIM Gateway
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),  # This will be used as Ocp-Apim-Subscription-Key
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    default_headers={
        "Ocp-Apim-Subscription-Key": os.getenv("AZURE_OPENAI_KEY")
    }
)

def consolidate_ingredients(recipes):
    """Consolidate ingredients from multiple recipes, combining quantities."""
    ingredient_map = {}
    
    for recipe in recipes:
        recipe_name = recipe.get('name', 'Unknown Recipe')
        ingredients = recipe.get('ingredients', [])
        
        for ingredient in ingredients:
            # Extract ingredient name (remove quantity and units)
            clean_ingredient = ingredient.strip()
            
            # Simple consolidation - just track which recipes use this ingredient
            if clean_ingredient in ingredient_map:
                ingredient_map[clean_ingredient]['from_recipes'].append(recipe_name)
            else:
                ingredient_map[clean_ingredient] = {
                    'ingredient': clean_ingredient,
                    'from_recipes': [recipe_name]
                }
    
    return list(ingredient_map.values())


@router.post("/generate-meal-plan")
async def generate_meal_plan(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        user_profile = data.get("user_profile")
        previous_meal_plan = data.get("previous_meal_plan")
        days = data.get("days", 7)  # Default to 7 days if not provided

        if not user_profile:
            raise HTTPException(status_code=400, detail="User profile is required")
        
        # Validate days parameter
        if not isinstance(days, int) or days < 1 or days > 7:
            raise HTTPException(status_code=400, detail="Days must be an integer between 1 and 7")

        # Get the user's document
        user_doc = await get_user_by_email(current_user["email"])
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Update the user's profile with the calorie and macro goals
        if "profile" not in user_doc:
            user_doc["profile"] = {}
        
        # Update the profile with the goals from the meal plan
        user_doc["profile"]["calorieTarget"] = user_profile.get("calorieTarget", DEFAULT_CALORIE_TARGET)
        user_doc["profile"]["macroGoals"] = {
            "protein": user_profile.get("macroGoals", {}).get("protein", 100),
            "carbs": user_profile.get("macroGoals", {}).get("carbs", 250),
            "fat": user_profile.get("macroGoals", {}).get("fat", 66)
        }

        # Save the updated profile
        user_container.replace_item(item=user_doc["id"], body=user_doc)

        # Continue with meal plan generation...

        # Check required environment variables
        required_env_vars = [
            "AZURE_OPENAI_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise HTTPException(
                status_code=500,
                detail=f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        print('user_profile received:', user_profile)
        print("/generate-meal-plan endpoint called")
        print(f"Current user: {current_user}")
        print(f"User profile received: {user_profile}")
        print("Model:", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))
        print("Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
        print("API Version:", os.getenv("AZURE_OPENAI_API_VERSION"))

        # If previous_meal_plan is provided, use it for 70/30 overlap
        def get_overlap_meals(prev_meals, new_meals):
            """Mix 70% meals from previous plan with 30% new meals"""
            if not prev_meals or not new_meals:
                return new_meals
            
            # Calculate how many meals to keep from previous
            total_meals = len(new_meals)
            overlap_count = int(total_meals * 0.7)
            new_count = total_meals - overlap_count
            
            # Take first overlap_count meals from previous, rest from new
            mixed_meals = prev_meals[:overlap_count] + new_meals[:new_count]
            
            # Pad with new meals if we don't have enough
            while len(mixed_meals) < total_meals:
                mixed_meals.extend(new_meals[:total_meals - len(mixed_meals)])
            
            return mixed_meals[:total_meals]

        # Build the meal plan prompt
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        allergies = user_profile.get("allergies", [])
        food_preferences = user_profile.get("foodPreferences", [])
        medical_conditions = user_profile.get("medicalConditions", [])
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text += f"Dietary restrictions: {', '.join(dietary_restrictions)}. "
        if allergies:
            restrictions_text += f"Allergies: {', '.join(allergies)}. "
        if food_preferences:
            restrictions_text += f"Food preferences: {', '.join(food_preferences)}. "
        if medical_conditions:
            restrictions_text += f"Medical conditions to consider: {', '.join(medical_conditions)}. "

        calorie_target = user_profile.get("calorieTarget", DEFAULT_CALORIE_TARGET)
        macro_goals = user_profile.get("macroGoals", {})
        protein_goal = macro_goals.get("protein", 100)
        carb_goal = macro_goals.get("carbs", 250)
        fat_goal = macro_goals.get("fat", 66)

        prompt = f"""Create a {days}-day diabetes-friendly meal plan for a person with the following profile:

Age: {user_profile.get('age', 'Not specified')}
Gender: {user_profile.get('gender', 'Not specified')}
Medical conditions: {', '.join(medical_conditions) if medical_conditions else 'None specified'}
{restrictions_text}

Nutritional targets:
- Daily calories: {calorie_target}
- Protein: {protein_goal}g
- Carbohydrates: {carb_goal}g  
- Fat: {fat_goal}g

Requirements:
1. Focus on low glycemic index foods
2. Include complex carbohydrates over simple sugars
3. Emphasize lean proteins and healthy fats
4. Include plenty of fiber-rich vegetables
5. Avoid processed foods and high-sodium items
6. Each meal should be diabetes-friendly with balanced macronutrients

Please provide the meal plan in the following JSON format:
{{
  "dailyCalories": {calorie_target},
  "macronutrients": {{
    "protein": {protein_goal},
    "carbs": {carb_goal},
    "fat": {fat_goal}
  }},
  "days": [
    {{
      "day": 1,
      "date": "2024-01-01",
      "breakfast": ["meal name 1"],
      "lunch": ["meal name 2"], 
      "dinner": ["meal name 3"],
      "snacks": ["snack name 1"]
    }}
  ]
}}

Make sure all meals are appropriate for diabetes management and provide variety across the {days} days."""

        try:
            # Make the API call to Azure OpenAI
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a registered dietitian specializing in diabetes meal planning. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MEAL_PLAN_MAX_TOKENS,
                temperature=CREATIVE_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            meal_plan_content = response.choices[0].message.content
            print(f"Raw meal plan response: {meal_plan_content}")
            
            # Parse the JSON response
            parsed_response = robust_json_parse(meal_plan_content, "meal_plan_generation")
            if not parsed_response["success"]:
                raise Exception(f"Failed to parse meal plan JSON: {parsed_response['error']}")
            
            meal_plan = parsed_response["data"]
            
            # Transform the OpenAI response from "days" array format to database-expected format
            if "days" in meal_plan and isinstance(meal_plan["days"], list):
                print("Transforming meal plan from days array format to database format")
                
                # Extract meals from all days and flatten into arrays
                breakfast_meals = []
                lunch_meals = []
                dinner_meals = []
                snack_meals = []
                
                for day in meal_plan["days"]:
                    if "breakfast" in day:
                        breakfast_meals.extend(day["breakfast"] if isinstance(day["breakfast"], list) else [day["breakfast"]])
                    if "lunch" in day:
                        lunch_meals.extend(day["lunch"] if isinstance(day["lunch"], list) else [day["lunch"]])
                    if "dinner" in day:
                        dinner_meals.extend(day["dinner"] if isinstance(day["dinner"], list) else [day["dinner"]])
                    if "snacks" in day:
                        snack_meals.extend(day["snacks"] if isinstance(day["snacks"], list) else [day["snacks"]])
                
                # Create the database-expected format (old format with arrays)
                meal_plan["breakfast"] = breakfast_meals
                meal_plan["lunch"] = lunch_meals
                meal_plan["dinner"] = dinner_meals
                meal_plan["snacks"] = snack_meals
                
                # Remove the days array as it's not needed for database storage
                del meal_plan["days"]
                
                print(f"Transformed meal plan: {len(breakfast_meals)} breakfast, {len(lunch_meals)} lunch, {len(dinner_meals)} dinner, {len(snack_meals)} snack items")
            
            # If we have a previous meal plan, apply 70/30 overlap
            if previous_meal_plan:
                print("Applying 70/30 overlap with previous meal plan")
                for meal_type in ["breakfast", "lunch", "dinner", "snacks"]:
                    if meal_type in previous_meal_plan and meal_type in meal_plan:
                        prev_meals = previous_meal_plan[meal_type]
                        new_meals = meal_plan[meal_type]
                        if isinstance(prev_meals, list) and isinstance(new_meals, list):
                            meal_plan[meal_type] = get_overlap_meals(prev_meals, new_meals)
            
            # Add metadata
            meal_plan["generated_at"] = datetime.utcnow().isoformat()
            meal_plan["user_id"] = current_user["email"]
            meal_plan["profile_snapshot"] = user_profile
            
            # Meal plan generation complete - no automatic save
            # User must explicitly save via the "Save Meal Plan + PDF" button
            print("[/generate-meal-plan] Meal plan generated successfully - ready for user to save")
            
            # Convert to plain dict for response
            try:
                meal_plan_dict = dict(meal_plan) if hasattr(meal_plan, 'items') else meal_plan
                print("[/generate-meal-plan] Converted returned meal_plan to plain dict")
            except Exception as e:
                print(f"[/generate-meal-plan] Failed to convert returned meal_plan to plain dict: {e}")
                meal_plan_dict = meal_plan
            
            return {"meal_plan": meal_plan_dict}
            
        except openai.APIError as e:
            print(f"OpenAI API error in /generate-meal-plan: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate meal plan due to AI service error"
            )
        except openai.APITimeoutError as e:
            print(f"OpenAI timeout error in /generate-meal-plan: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Meal plan generation timed out. Please try again."
            )
        except openai.RateLimitError as e:
            print(f"OpenAI rate limit error in /generate-meal-plan: {str(e)}")
            raise HTTPException(
                status_code=429,
                detail="Service is temporarily busy. Please try again in a moment."
            )

    except HTTPException as he:
        print(f"HTTP Exception in /generate-meal-plan: {str(he.detail)}")
        raise he
    except Exception as e:
        print(f"Unexpected error in /generate-meal-plan: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/generate-recipes")
async def generate_recipes(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        meal_plan = data.get('meal_plan', {})
        print("/generate-recipes endpoint called")
        print("Received meal_plan:", meal_plan)
        
        # Extract all meals from the meal plan (including duplicates)
        all_meals = []
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
            if meal_type in meal_plan and isinstance(meal_plan[meal_type], list):
                all_meals.extend(meal_plan[meal_type])
        
        # Create unique recipes but track all meal instances
        unique_meals = []
        seen = set()
        meal_instances = {}
        
        for meal in all_meals:
            if meal not in seen:
                unique_meals.append(meal)
                seen.add(meal)
                meal_instances[meal] = 1
            else:
                meal_instances[meal] += 1
        
        print(f"Total meals in plan: {len(all_meals)}")
        print(f"Unique meals to generate recipes for: {unique_meals}")
        print(f"Meal instances: {meal_instances}")
        
        # Format the prompt for recipe generation
        prompt = f"""Generate detailed recipes for the following meals from a diabetes-friendly meal plan:

Meals: {', '.join(unique_meals)}

For each meal, provide:
1. A list of ingredients with quantities
2. Step-by-step preparation instructions
3. Nutritional information (calories, protein, carbs, fat)

Format the response as a JSON array of recipe objects with the following structure:
[
  {{
    "name": "Recipe Name",
    "ingredients": ["1 cup ingredient1", "2 tbsp ingredient2"],
    "instructions": ["Step 1", "Step 2", "Step 3"],
    "nutritional_info": {{
      "calories": 300,
      "protein": 25,
      "carbs": 30,
      "fat": 10
    }},
    "prep_time": "15 minutes",
    "cook_time": "20 minutes",
    "servings": 2
  }}
]

Make sure all recipes are diabetes-friendly with low glycemic index ingredients."""

        try:
            # Make API call to Azure OpenAI
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a registered dietitian specializing in diabetes-friendly recipes. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=RECIPE_MAX_TOKENS,
                temperature=CREATIVE_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            recipes_content = response.choices[0].message.content
            print(f"Raw recipes response: {recipes_content}")
            
            # Parse the JSON response
            parsed_response = robust_json_parse(recipes_content, "recipe_generation")
            if not parsed_response["success"]:
                # Try to extract JSON array from the response
                try:
                    import re
                    json_match = re.search(r'\[.*\]', recipes_content, re.DOTALL)
                    if json_match:
                        recipes = json.loads(json_match.group())
                    else:
                        raise Exception("No valid JSON array found in response")
                except:
                    raise Exception(f"Failed to parse recipes JSON: {parsed_response['error']}")
            else:
                recipes_data = parsed_response["data"]
                # Handle both array and object responses
                if isinstance(recipes_data, dict) and "recipes" in recipes_data:
                    recipes = recipes_data["recipes"]
                elif isinstance(recipes_data, list):
                    recipes = recipes_data
                else:
                    recipes = [recipes_data] if isinstance(recipes_data, dict) else []
            
            return {"recipes": recipes}
            
        except openai.APIError as e:
            print(f"OpenAI API error in /generate-recipes: {str(e)}")
            # Fallback to template recipes
            fallback_recipes = []
            for meal in unique_meals[:3]:  # Limit to first 3 meals
                template_key = meal.lower().replace(" ", "_")
                if template_key in RECIPE_TEMPLATES:
                    fallback_recipes.append(RECIPE_TEMPLATES[template_key])
            
            if fallback_recipes:
                return {"recipes": fallback_recipes}
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate recipes due to AI service error"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /generate-recipes: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Both OpenAI recipe generation and fallback failed. Error: {str(e)}"
        )


@router.post("/generate-recipe")
async def generate_recipe(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        data = await request.json()
        meal_name = data.get('meal_name', '')
        user_profile = data.get('user_profile', {})
        
        print("/generate-recipe endpoint called")
        print(f"Generating recipe for: {meal_name}")
        
        if not meal_name:
            raise HTTPException(status_code=400, detail="Meal name is required")
        
        # Build dietary context
        dietary_restrictions = user_profile.get("dietaryRestrictions", [])
        allergies = user_profile.get("allergies", [])
        medical_conditions = user_profile.get("medicalConditions", [])
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text += f"Dietary restrictions: {', '.join(dietary_restrictions)}. "
        if allergies:
            restrictions_text += f"Allergies to avoid: {', '.join(allergies)}. "
        if medical_conditions:
            restrictions_text += f"Medical considerations: {', '.join(medical_conditions)}. "
        
        prompt = f"""Generate a detailed diabetes-friendly recipe for: {meal_name}

User context: {restrictions_text}

Requirements:
1. Use low glycemic index ingredients
2. Focus on complex carbohydrates and lean proteins
3. Include healthy fats and high-fiber ingredients
4. Minimize processed ingredients and added sugars
5. Suitable for diabetes management

Provide the recipe in the following JSON format:
{{
  "name": "{meal_name}",
  "ingredients": ["1 cup ingredient1", "2 tbsp ingredient2"],
  "instructions": ["Step 1", "Step 2", "Step 3"],
  "nutritional_info": {{
    "calories": 300,
    "protein": 25,
    "carbs": 30,
    "fat": 10,
    "fiber": 8,
    "sugar": 5
  }},
  "prep_time": "15 minutes",
  "cook_time": "20 minutes",
  "servings": 2,
  "diabetes_notes": "Tips for diabetes management"
}}"""

        try:
            # Make API call
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a registered dietitian specializing in diabetes-friendly recipes. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=RECIPE_MAX_TOKENS,
                temperature=PRECISE_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            recipe_content = response.choices[0].message.content
            print(f"Raw recipe response: {recipe_content}")
            
            # Parse JSON response
            parsed_response = robust_json_parse(recipe_content, "single_recipe_generation")
            if not parsed_response["success"]:
                raise Exception(f"Failed to parse recipe JSON: {parsed_response['error']}")
            
            recipe = parsed_response["data"]
            return {"recipe": recipe}
            
        except openai.APIError as e:
            print(f"OpenAI API error in /generate-recipe: {str(e)}")
            # Try fallback template
            template_key = meal_name.lower().replace(" ", "_")
            if template_key in RECIPE_TEMPLATES:
                return {"recipe": RECIPE_TEMPLATES[template_key]}
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate recipe due to AI service error"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /generate-recipe: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recipe: {str(e)}"
        )


@router.post("/generate-shopping-list")
async def generate_shopping_list(
    recipes: List[dict],
    current_user: User = Depends(get_current_user)
):
    try:
        print("/generate-shopping-list endpoint called")
        print("Received recipes:")
        print(recipes)
        
        # First, consolidate ingredients programmatically
        consolidated_ingredients = consolidate_ingredients(recipes)
        print("Consolidated ingredients:")
        for item in consolidated_ingredients:
            print(f"  - {item['ingredient']} (from: {', '.join(item['from_recipes'])})")
        
        # Create a simplified ingredient list for the AI
        ingredient_list = [item["ingredient"] for item in consolidated_ingredients]
        prompt = f"""Generate a shopping list based on the following PRE-CONSOLIDATED ingredients:
                    {json.dumps(ingredient_list, indent=2)}

                    NOTE: These ingredients have ALREADY been consolidated and quantities combined. Your task is to:
                    1. Categorize each item into appropriate grocery store sections (Produce, Dairy, Meat, Pantry, etc.)
                    2. Apply Canadian grocery store quantity formatting rules
                    3. DO NOT further consolidate - the consolidation is already done
                    4. Use SIMPLE ingredient names only (e.g., "Onions" not "Onions, chopped")
                    5. DO NOT include cooking instructions, preparation methods, or references like "[See above]"

                    ––––– UNIT RULES –––––
                    • Express quantities in units a Canadian grocery shopper can actually buy ("purchasable quantity").
                    – **Fresh herbs** (cilantro/coriander, parsley, mint, dill, etc.): use whole bunches.  
                        *Assume 1 bunch ≈ 30 g; round ⭡ to the nearest whole bunch.*
                    – **Loose fruit & veg** commonly weighed at checkout (apples, oranges, onions, potatoes, carrots, etc.): use pounds (lb).  
                        *Round ⭡ to nearest 0.25 lb (e.g., 0.75 lb, 1 lb, 1.25 lb).*
                    – **Packaged items** (bread, rice, pasta, canned goods, etc.): use package sizes available in Canadian stores.
                    – **Dairy & meat**: use realistic package sizes (e.g., "1 L milk", "500g ground turkey").

                    Return as JSON:
                    {{
                      "shopping_list": {{
                        "Produce": ["2 lb onions", "1 bunch fresh cilantro"],
                        "Dairy": ["1 L milk", "500g Greek yogurt"],
                        "Meat & Seafood": ["500g chicken breast"],
                        "Pantry": ["1 can (398ml) diced tomatoes"],
                        "Frozen": ["1 bag (1kg) frozen berries"]
                      }}
                    }}"""

        try:
            # Make API call
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": "You are a helpful grocery shopping assistant for Canadian shoppers. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=PRECISE_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            shopping_content = response.choices[0].message.content
            print(f"Raw shopping list response: {shopping_content}")
            
            # Parse JSON response
            parsed_response = robust_json_parse(shopping_content, "shopping_list_generation")
            if not parsed_response["success"]:
                raise Exception(f"Failed to parse shopping list JSON: {parsed_response['error']}")
            
            shopping_list = parsed_response["data"]
            return shopping_list
            
        except openai.APIError as e:
            print(f"OpenAI API error in /generate-shopping-list: {str(e)}")
            # Create simple fallback shopping list
            fallback_list = {
                "shopping_list": {
                    "Produce": [item["ingredient"] for item in consolidated_ingredients[:5]],
                    "Pantry": [item["ingredient"] for item in consolidated_ingredients[5:10]],
                    "Other": [item["ingredient"] for item in consolidated_ingredients[10:]]
                }
            }
            return fallback_list
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /generate-shopping-list: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate shopping list: {str(e)}"
        )


@router.post("/generate_plan")
async def generate_plan(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Save a generated meal plan to history"""
    try:
        data = await request.json()
        meal_plan = data.get("meal_plan")
        
        if not meal_plan:
            raise HTTPException(status_code=400, detail="Meal plan data is required")
        
        # Add metadata
        meal_plan["user_id"] = current_user["email"]
        meal_plan["generated_at"] = datetime.utcnow().isoformat()
        
        # Save to database
        await save_meal_plan(meal_plan, current_user["email"])
        
        return {"message": "Meal plan saved successfully", "plan_id": meal_plan.get("id")}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /generate_plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save meal plan: {str(e)}"
        )


@router.get("/meal_plans")
async def get_meal_plans(
    current_user: User = Depends(get_current_user)
):
    """Get all meal plans for the current user"""
    try:
        meal_plans = await get_user_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plans: {str(e)}"
        )


@router.get("/meal_plans/{plan_id}")
async def get_meal_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific meal plan by ID"""
    try:
        # Query Cosmos DB for the specific meal plan
        query = f"SELECT * FROM c WHERE (c.type = 'meal_plan' OR c.type = 'full_meal_plan') AND c.id = '{plan_id}' AND c.user_id = '{current_user['email']}'"
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
            
        return {"meal_plan": items[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plan: {str(e)}"
        )


@router.delete("/meal_plans/all")
async def delete_all_meal_plans_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes all meal plans for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token. Please log in again.")

        deleted_count = await delete_all_user_meal_plans(user_id)

        if deleted_count == 0:
            return {"message": "No meal plans were found to delete. Your history is already empty."}
        else:
            return {"message": f"Successfully deleted all {deleted_count} meal plan(s) for user {user_id}."}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in DELETE /meal_plans/all: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete all meal plans: {str(e)}")


@router.delete("/meal_plans/{plan_id}")
async def delete_meal_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes a specific meal plan by ID for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
             raise HTTPException(status_code=400, detail="User ID not found in token.")
        deleted = await delete_meal_plan_by_id(plan_id, user_id)
        if not deleted:
             raise HTTPException(status_code=404, detail="Meal plan not found or does not belong to user.")
        return {"message": f"Meal plan '{plan_id}' deleted successfully"}
    except Exception as e:
        print(f"Error in DELETE /meal_plans/{{plan_id}}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete meal plan: {str(e)}")


@router.post("/meal_plans/bulk_delete")
async def bulk_delete_meal_plans(
    plan_ids: List[str] = Body(..., embed=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes multiple meal plans by their IDs for the current user."""
    try:
        user_id = current_user.get("email")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token.")
        
        if not plan_ids:
            raise HTTPException(status_code=400, detail="No plan IDs provided.")
        
        deleted_count = 0
        failed_ids = []
        
        for plan_id in plan_ids:
            try:
                deleted = await delete_meal_plan_by_id(plan_id, user_id)
                if deleted:
                    deleted_count += 1
                else:
                    failed_ids.append(plan_id)
            except Exception as e:
                print(f"Error deleting plan {plan_id}: {e}")
                failed_ids.append(plan_id)
        
        response = {"deleted_count": deleted_count}
        if failed_ids:
            response["failed_ids"] = failed_ids
            response["message"] = f"Successfully deleted {deleted_count} meal plans. Failed to delete {len(failed_ids)} plans."
        else:
            response["message"] = f"Successfully deleted all {deleted_count} meal plans."
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in bulk delete meal plans: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete meal plans: {str(e)}")


@router.get("/view-meal-plans")
async def view_meal_plans_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get meal plans with additional view metadata"""
    try:
        meal_plans = await view_meal_plans(current_user["email"])
        return {"meal_plans": meal_plans}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meal plans: {str(e)}"
        )


@router.post("/save-consolidated-pdf")
async def save_consolidated_pdf_endpoint(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Generates and saves a consolidated PDF, returns PDF info for storage reference."""
    try:
        data = await request.json()
        meal_plan = data.get("meal_plan", {})
        recipes = data.get("recipes", [])
        shopping_list = data.get("shopping_list", {})
        
        if not meal_plan:
            raise HTTPException(status_code=400, detail="Meal plan is required")
        
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io
        import os
        from datetime import datetime
        
        # Create PDF content
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Diabetes-Friendly Meal Plan", title_style))
        story.append(Spacer(1, 12))
        
        # Meal Plan Section
        story.append(Paragraph("Weekly Meal Plan", styles['Heading2']))
        
        if meal_plan.get("days"):
            for day in meal_plan["days"]:
                day_num = day.get("day", "")
                date = day.get("date", "")
                story.append(Paragraph(f"Day {day_num} - {date}", styles['Heading3']))
                
                # Create meals table
                meal_data = []
                for meal_type in ["breakfast", "lunch", "dinner", "snacks"]:
                    if meal_type in day:
                        meals = day[meal_type] if isinstance(day[meal_type], list) else [day[meal_type]]
                        meal_data.append([meal_type.title(), ", ".join(meals)])
                
                if meal_data:
                    meal_table = Table(meal_data, colWidths=[1.5*inch, 4*inch])
                    meal_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(meal_table)
                    story.append(Spacer(1, 12))
        
        # Add page break before recipes
        story.append(PageBreak())
        
        # Recipes Section
        if recipes:
            story.append(Paragraph("Recipes", styles['Heading2']))
            
            for recipe in recipes:
                story.append(Paragraph(recipe.get("name", "Recipe"), styles['Heading3']))
                
                # Ingredients
                story.append(Paragraph("Ingredients:", styles['Heading4']))
                for ingredient in recipe.get("ingredients", []):
                    story.append(Paragraph(f"• {ingredient}", styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Instructions
                story.append(Paragraph("Instructions:", styles['Heading4']))
                for i, instruction in enumerate(recipe.get("instructions", []), 1):
                    story.append(Paragraph(f"{i}. {instruction}", styles['Normal']))
                
                # Nutritional info
                if recipe.get("nutritional_info"):
                    story.append(Paragraph("Nutritional Information:", styles['Heading4']))
                    nutrition = recipe["nutritional_info"]
                    nutrition_text = f"Calories: {nutrition.get('calories', 'N/A')}, Protein: {nutrition.get('protein', 'N/A')}g, Carbs: {nutrition.get('carbs', 'N/A')}g, Fat: {nutrition.get('fat', 'N/A')}g"
                    story.append(Paragraph(nutrition_text, styles['Normal']))
                
                story.append(Spacer(1, 12))
        
        # Shopping List Section
        if shopping_list.get("shopping_list"):
            story.append(PageBreak())
            story.append(Paragraph("Shopping List", styles['Heading2']))
            
            for category, items in shopping_list["shopping_list"].items():
                story.append(Paragraph(category, styles['Heading3']))
                for item in items:
                    story.append(Paragraph(f"• {item}", styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"meal_plan_{current_user['email'].replace('@', '_').replace('.', '_')}_{timestamp}.pdf"
        
        # Save PDF to a storage directory (create directory if it doesn't exist)
        storage_dir = os.path.join(os.getcwd(), "storage", "pdfs")
        os.makedirs(storage_dir, exist_ok=True)
        
        file_path = os.path.join(storage_dir, filename)
        with open(file_path, "wb") as f:
            f.write(pdf_content)
        
        # Return PDF information in the format expected by frontend
        pdf_info = {
            "filename": filename,
            "file_path": file_path,
            "generated_at": datetime.utcnow().isoformat(),
            "file_size": len(pdf_content)
        }
        
        return {
            "message": "PDF generated and saved successfully",
            "pdf_info": pdf_info  # Frontend expects this nested structure
        }
        
    except ImportError as e:
        print(f"Missing PDF library: {e}")
        raise HTTPException(
            status_code=500,
            detail="PDF generation library not available. Please install reportlab."
        )
    except Exception as e:
        print("Error in /save-consolidated-pdf:")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/download-saved-pdf/{filename}")
async def download_saved_pdf(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download a previously saved consolidated PDF"""
    try:
        # Verify filename contains user identifier for security
        user_identifier = current_user['email'].replace('@', '_').replace('.', '_')
        if user_identifier not in filename:
            raise HTTPException(status_code=403, detail="Access denied to this file")
        
        # Construct file path
        storage_dir = os.path.join(os.getcwd(), "storage", "pdfs")
        file_path = os.path.join(storage_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading saved PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download PDF: {str(e)}"
        )


@router.post("/save-full-meal-plan")
async def save_full_meal_plan(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user)
):
    """Saves the full meal plan data including recipes, shopping list, and PDF reference."""
    try:
        data = await request.json()
        print(f"[save_full_meal_plan] Received data keys: {list(data.keys())}")
        
        # Handle different data structures from frontend
        meal_plan = {}
        recipes = []
        shopping_list = {}
        consolidated_pdf = None
        
        # Check if data has nested structure (from MealPlanRequest component)
        if 'meal_plan' in data:
            # Data from the consolidated save with nested structure
            meal_plan = data.get("meal_plan", {})
            recipes = data.get("recipes", [])
            shopping_list = data.get("shopping_list", {})
            consolidated_pdf = data.get("consolidated_pdf")
        else:
            # Data is the meal plan itself (from frontend fullMealPlan object)
            meal_plan = data
            recipes = data.get("recipes", [])
            shopping_list = data.get("shopping_list", {})
            consolidated_pdf = data.get("consolidated_pdf")
        
        if not meal_plan:
            raise HTTPException(status_code=400, detail="Meal plan is required")
        
        print(f"[save_full_meal_plan] Processing meal plan with PDF: {bool(consolidated_pdf)}")
        if consolidated_pdf:
            print(f"[save_full_meal_plan] PDF filename: {consolidated_pdf.get('filename', 'N/A')}")
        
        # Check for existing meal plan to prevent duplicates
        # Look for very recent meal plans (within last 30 seconds) with same calorie target
        recent_cutoff = (datetime.utcnow() - timedelta(seconds=30)).isoformat()
        duplicate_query = f"""
        SELECT * FROM c 
        WHERE c.user_id = '{current_user["email"]}' 
        AND (c.type = 'meal_plan' OR c.type = 'full_meal_plan')
        AND c.created_at > '{recent_cutoff}'
        ORDER BY c.created_at DESC
        """
        
        recent_plans = list(interactions_container.query_items(
            query=duplicate_query, 
            enable_cross_partition_query=True
        ))
        
        meal_plan_calories = meal_plan.get('dailyCalories')
        if recent_plans and meal_plan_calories:
            for recent_plan in recent_plans:
                recent_calories = recent_plan.get('dailyCalories') or recent_plan.get('meal_plan', {}).get('dailyCalories')
                if recent_calories == meal_plan_calories:
                    print(f"[save_full_meal_plan] Detected duplicate meal plan with {meal_plan_calories} calories, skipping save")
                    return {
                        "message": "Meal plan already exists (duplicate prevented)",
                        "record_id": recent_plan.get("id"),
                        "duplicate_prevented": True
                    }
        
        # Create comprehensive record with proper structure
        full_record = {
            "id": str(uuid.uuid4()),  # Generate unique ID
            "type": "full_meal_plan",
            "user_id": current_user["email"],
            "created_at": datetime.utcnow().isoformat(),
            # Store meal plan data at root level for compatibility
            "breakfast": meal_plan.get("breakfast", []),
            "lunch": meal_plan.get("lunch", []),
            "dinner": meal_plan.get("dinner", []),
            "snacks": meal_plan.get("snacks", []),
            "dailyCalories": meal_plan.get("dailyCalories", 0),
            "macronutrients": meal_plan.get("macronutrients", {}),
            # Store full nested structure for complex data
            "meal_plan": meal_plan,
            "recipes": recipes,
            "shopping_list": shopping_list,
            "status": "complete"
        }
        
        # Add PDF info if available (both formats for compatibility)
        if consolidated_pdf:
            full_record["consolidated_pdf"] = consolidated_pdf
            full_record["pdf_filename"] = consolidated_pdf.get("filename", "")
            print(f"[save_full_meal_plan] Added PDF info: {consolidated_pdf.get('filename', 'N/A')}")
        
        # Save to database
        result = interactions_container.create_item(body=full_record)
        print(f"[save_full_meal_plan] Successfully saved meal plan with ID: {full_record['id']}")
        
        return {
            "message": "Full meal plan saved successfully",
            "record_id": full_record["id"],
            "has_pdf": bool(consolidated_pdf),
            "duplicate_prevented": False
        }
        
    except Exception as e:
        print(f"Error in /save-full-meal-plan: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save full meal plan: {str(e)}"
        )


@router.get("/debug/meal_plans")
async def debug_meal_plans(current_user: User = Depends(get_current_user)):
    """Debug endpoint to view raw meal plan data"""
    try:
        # Get raw meal plan data from database
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.user_id = '{current_user['email']}'"
        items = list(interactions_container.query_items(query=query, enable_cross_partition_query=True))
        
        return {"meal_plans": items}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debug query failed: {str(e)}"
        ) 

@router.get("/generate-pdf/{meal_plan_id}")
async def generate_pdf_for_meal_plan(
    meal_plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate and download a consolidated PDF for any meal plan from history"""
    try:
        print(f"[generate_pdf_for_meal_plan] Generating PDF for meal plan: {meal_plan_id}")
        
        # Get the meal plan from database using cross-partition query
        try:
            query = f"SELECT * FROM c WHERE c.id = '{meal_plan_id}' AND c.user_id = '{current_user['email']}'"
            meal_plans = list(interactions_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not meal_plans:
                print(f"[generate_pdf_for_meal_plan] No meal plan found with ID: {meal_plan_id} for user: {current_user['email']}")
                raise HTTPException(status_code=404, detail="Meal plan not found")
                
            meal_plan_doc = meal_plans[0]
            print(f"[generate_pdf_for_meal_plan] Found meal plan for user: {meal_plan_doc.get('user_id')}")
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"[generate_pdf_for_meal_plan] Error querying meal plan: {str(e)}")
            raise HTTPException(status_code=404, detail="Meal plan not found")
        
        # Verify ownership
        if meal_plan_doc.get("user_id") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Extract meal plan data based on document type
        if meal_plan_doc.get("type") == "full_meal_plan":
            # For full_meal_plan, extract from nested structure
            meal_plan_data = meal_plan_doc.get("meal_plan", {})
            recipes = meal_plan_doc.get("recipes", [])
            shopping_list = meal_plan_doc.get("shopping_list", [])
        else:
            # For regular meal_plan, use root level data
            meal_plan_data = {
                "breakfast": meal_plan_doc.get("breakfast", []),
                "lunch": meal_plan_doc.get("lunch", []),
                "dinner": meal_plan_doc.get("dinner", []),  
                "snacks": meal_plan_doc.get("snacks", []),
                "dailyCalories": meal_plan_doc.get("dailyCalories", 0),
                "macronutrients": meal_plan_doc.get("macronutrients", {})
            }
            recipes = meal_plan_doc.get("recipes", [])
            shopping_list = meal_plan_doc.get("shopping_list", [])
        
        print(f"[generate_pdf_for_meal_plan] Extracted meal plan data: {bool(meal_plan_data)}")
        
        # Generate PDF using reportlab
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from io import BytesIO
        import os
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Add cover page if available  
        try:
            cover_path = os.path.join("assets", "coverpage.png")
            if os.path.exists(cover_path):
                elements.append(Image(cover_path, width=10*inch, height=6*inch))
                elements.append(Spacer(1, 48))
        except Exception as cover_err:
            print(f"Could not add cover page: {cover_err}")
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Consolidated Meal Plan", title_style))
        elements.append(Spacer(1, 12))
        
        # Meal Plan Section
        elements.append(Paragraph("Weekly Meal Plan", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Create meal plan table with better formatting
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        breakfast_items = meal_plan_data.get("breakfast", [])
        lunch_items = meal_plan_data.get("lunch", [])
        dinner_items = meal_plan_data.get("dinner", [])
        snack_items = meal_plan_data.get("snacks", [])
        
        print(f"[generate_pdf_for_meal_plan] Meal arrays - breakfast: {len(breakfast_items)}, lunch: {len(lunch_items)}, dinner: {len(dinner_items)}, snacks: {len(snack_items)}")
        
        # Determine actual number of days based on meal plan data
        max_days = max(
            len(breakfast_items),
            len(lunch_items), 
            len(dinner_items),
            len(snack_items)
        ) if any([breakfast_items, lunch_items, dinner_items, snack_items]) else 7
        
        # Limit to maximum of 7 days and use appropriate day names
        actual_days = min(max_days, 7)
        days = all_days[:actual_days]
        
        data_table = [["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]]
        
        for i, day in enumerate(days):
            breakfast = breakfast_items[i] if i < len(breakfast_items) else "Not specified"
            lunch = lunch_items[i] if i < len(lunch_items) else "Not specified"
            dinner = dinner_items[i] if i < len(dinner_items) else "Not specified"
            snack = snack_items[i] if i < len(snack_items) else "Not specified"
            
            # Create Paragraph objects for better text wrapping
            breakfast_para = Paragraph(str(breakfast), styles['Normal'])
            lunch_para = Paragraph(str(lunch), styles['Normal'])
            dinner_para = Paragraph(str(dinner), styles['Normal'])
            snack_para = Paragraph(str(snack), styles['Normal'])
            
            data_table.append([
                day,
                breakfast_para,
                lunch_para,
                dinner_para,
                snack_para
            ])
        
        # Create and style the table with optimized spacing for landscape
        table = Table(data_table, colWidths=[0.9*inch, 2.3*inch, 2.3*inch, 2.3*inch, 2.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),  # Left align meal text for better readability
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top align for better text layout
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),    # Slightly smaller header font
            ('FONTSIZE', (0, 1), (-1, -1), 8),    # Optimized content font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8), # Reduced header padding
            ('TOPPADDING', (0, 1), (-1, -1), 4),   # Reduced content padding
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        # Wrap table in KeepTogether to prevent page breaks
        meal_plan_section = KeepTogether([
            Paragraph("Weekly Meal Plan", styles['Heading2']),
            Spacer(1, 12),
            table
        ])
        
        # Remove the previous heading and table additions, replace with KeepTogether section
        elements.pop()  # Remove the last "Weekly Meal Plan" heading
        elements.pop()  # Remove the spacer after heading
        elements.append(meal_plan_section)
        elements.append(Spacer(1, 20))
        
        # Nutritional Summary
        calories = meal_plan_data.get("dailyCalories", 0)
        macros = meal_plan_data.get("macronutrients", {})
        
        elements.append(Paragraph("Nutritional Summary", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        nutrition_data = [
            ["Metric", "Value"],
            ["Daily Calories", f"{calories or 'N/A'} kcal"],
            ["Protein", f"{macros.get('protein', 'N/A')}g"],
            ["Carbohydrates", f"{macros.get('carbs', 'N/A')}g"],
            ["Fats", f"{macros.get('fats', 'N/A')}g"]
        ]
        
        nutrition_table = Table(nutrition_data, colWidths=[2.2*inch, 2.2*inch])
        nutrition_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),      # Slightly smaller header
            ('FONTSIZE', (0, 1), (-1, -1), 10),     # Content font size
            ('TOPPADDING', (0, 0), (-1, -1), 6),    # Consistent padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Wrap nutritional summary in KeepTogether for better organization
        nutrition_section = KeepTogether([
            Paragraph("Nutritional Summary", styles['Heading2']),
            Spacer(1, 12),
            nutrition_table
        ])
        
        # Remove the previous heading, replace with KeepTogether section
        elements.pop()  # Remove the "Nutritional Summary" heading
        elements.pop()  # Remove the spacer after heading
        elements.append(nutrition_section)
        
        # Add recipes section if available - show ALL recipes with better organization
        if recipes and len(recipes) > 0:
            recipe_elements = [
                Paragraph("Recipes", styles['Heading2']),
                Spacer(1, 12)
            ]
            
            for i, recipe in enumerate(recipes):  # Show all recipes, not just 10
                if isinstance(recipe, dict):
                    recipe_name = recipe.get('name', 'Unknown Recipe')
                    recipe_elements.append(Paragraph(f"{i+1}. {recipe_name}", styles['Heading3']))
                    
                    # Add ingredients section
                    ingredients = recipe.get('ingredients', [])
                    if ingredients:
                        recipe_elements.append(Paragraph("Ingredients:", styles['Heading4']))
                        for ingredient in ingredients:  # Show all ingredients
                            recipe_elements.append(Paragraph(f"• {ingredient}", styles['Normal']))
                    
                    # Add instructions if available
                    instructions = recipe.get('instructions', [])
                    if instructions:
                        recipe_elements.append(Paragraph("Instructions:", styles['Heading4']))
                        for j, instruction in enumerate(instructions, 1):
                            recipe_elements.append(Paragraph(f"{j}. {instruction}", styles['Normal']))
                    
                    # Add nutritional info if available
                    nutrition = recipe.get('nutritional_info', {})
                    if nutrition:
                        recipe_elements.append(Paragraph("Nutritional Information:", styles['Heading4']))
                        nutrition_text = f"Calories: {nutrition.get('calories', 'N/A')}, Protein: {nutrition.get('protein', 'N/A')}g, Carbs: {nutrition.get('carbs', 'N/A')}g, Fat: {nutrition.get('fat', 'N/A')}g"
                        recipe_elements.append(Paragraph(nutrition_text, styles['Normal']))
                    
                    recipe_elements.append(Spacer(1, 16))
            
            elements.append(Spacer(1, 20))
            elements.extend(recipe_elements)
        
        # Add shopping list section if available with better organization
        if shopping_list and len(shopping_list) > 0:
            shopping_elements = [
                Paragraph("Shopping List", styles['Heading2']),
                Spacer(1, 12)
            ]
            
            # Handle different shopping list formats
            if isinstance(shopping_list, dict):
                # If shopping_list is a dict with categories
                for category, items in shopping_list.items():
                    if isinstance(items, list) and items:
                        shopping_elements.append(Paragraph(f"• {category.title()}", styles['Heading3']))
                        for item in items:
                            if isinstance(item, dict):
                                # Handle item objects with name and amount
                                name = item.get('name', str(item))
                                amount = item.get('amount', '')
                                item_text = f"  - {name}" + (f" ({amount})" if amount else "")
                            else:
                                # Handle simple string items
                                item_text = f"  - {str(item)}"
                            shopping_elements.append(Paragraph(item_text, styles['Normal']))
                        shopping_elements.append(Spacer(1, 8))
            elif isinstance(shopping_list, list):
                # If shopping_list is a flat list
                categories = {}
                # Group items by category if available
                for item in shopping_list:
                    if isinstance(item, dict):
                        category = item.get('category', 'Other Items')
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(item)
                    else:
                        if 'Other Items' not in categories:
                            categories['Other Items'] = []
                        categories['Other Items'].append(item)
                
                # Display categorized items
                for category, items in categories.items():
                    shopping_elements.append(Paragraph(f"• {category}", styles['Heading3']))
                    for item in items:
                        if isinstance(item, dict):
                            name = item.get('name', str(item))
                            amount = item.get('amount', '')
                            item_text = f"  - {name}" + (f" ({amount})" if amount else "")
                        else:
                            item_text = f"  - {str(item)}"
                        shopping_elements.append(Paragraph(item_text, styles['Normal']))
                    shopping_elements.append(Spacer(1, 8))
            
            elements.append(Spacer(1, 20))
            elements.extend(shopping_elements)
        
        # Build PDF
        try:
            print(f"[generate_pdf_for_meal_plan] Building PDF with {len(elements)} elements")
            doc.build(elements)
            buffer.seek(0)
            print(f"[generate_pdf_for_meal_plan] PDF successfully built, buffer size: {len(buffer.getvalue())} bytes")
        except Exception as pdf_build_error:
            print(f"[generate_pdf_for_meal_plan] Error building PDF: {str(pdf_build_error)}")
            import traceback
            traceback.print_exc()
            raise
        
        # Return PDF as download
        from fastapi.responses import StreamingResponse
        
        # Generate filename  
        from datetime import datetime
        username = current_user["email"].split("@")[0]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}_meal_plan.pdf"
        
        return StreamingResponse(
            BytesIO(buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /generate-pdf/{meal_plan_id}:")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        ) 