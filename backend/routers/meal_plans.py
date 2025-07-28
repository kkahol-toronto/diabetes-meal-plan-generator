from fastapi import APIRouter, HTTPException, Depends, status, Request as FastAPIRequest, Body
from fastapi.responses import FileResponse
from typing import Dict, Any, List
import os
import json
import traceback
from datetime import datetime

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
            
            # Save to database
            await save_meal_plan(meal_plan, current_user["email"])
            
            print("[/generate-meal-plan] Meal plan generated and saved successfully")
            
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
        
        # Extract all unique meals from the meal plan
        all_meals = []
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
            if meal_type in meal_plan and isinstance(meal_plan[meal_type], list):
                all_meals.extend(meal_plan[meal_type])
        
        # Remove duplicates while preserving order
        unique_meals = []
        seen = set()
        for meal in all_meals:
            if meal not in seen:
                unique_meals.append(meal)
                seen.add(meal)
        
        print(f"Unique meals to generate recipes for: {unique_meals}")
        
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
        query = f"SELECT * FROM c WHERE c.type = 'meal_plan' AND c.id = '{plan_id}' AND c.user_id = '{current_user['id']}'"
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
        
        from reportlab.lib.pagesizes import letter
        from reportlab.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io
        import os
        
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
        
        # Return PDF information
        return {
            "message": "PDF generated and saved successfully",
            "filename": filename,
            "file_path": file_path,
            "file_size": len(pdf_content)
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
        
        # Extract components
        meal_plan = data.get("meal_plan", {})
        recipes = data.get("recipes", [])
        shopping_list = data.get("shopping_list", {})
        pdf_filename = data.get("pdf_filename", "")
        
        if not meal_plan:
            raise HTTPException(status_code=400, detail="Meal plan is required")
        
        # Create comprehensive record
        full_record = {
            "type": "full_meal_plan",
            "user_id": current_user["email"],
            "created_at": datetime.utcnow().isoformat(),
            "meal_plan": meal_plan,
            "recipes": recipes,
            "shopping_list": shopping_list,
            "pdf_filename": pdf_filename,
            "status": "complete"
        }
        
        # Save to database
        interactions_container.create_item(body=full_record)
        
        return {
            "message": "Full meal plan saved successfully",
            "record_id": full_record.get("id")
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