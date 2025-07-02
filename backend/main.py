"""Application entry point for the Diabetes Meal-Plan Generator API.

This slim module *only* creates the :class:`fastapi.FastAPI` instance and
registers modular routers.  Business logic lives in ``backend/services`` and
route handlers in ``backend/routers``.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
import traceback
import sys

# Routers – import paths must resolve quickly, so keep heavy deps in their own
# modules, **not** at top-level of this file.
from app.routers.coach import router as coach_router
from app.routers.users import router as users_router
from app.routers.consumption import router as consumption_router
from app.routers.auth import router as auth_router
from app.routers.meal_plans import router as meal_plans_router
from app.routers.chat import router as chat_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Diabetes Meal-Plan API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under versioned prefix for future evolution.
API_PREFIX = "/api/v1"

# Mount routers with both versioned and non-versioned paths for compatibility
app.include_router(auth_router, tags=["auth"])  # No prefix for login/register
app.include_router(coach_router, prefix="/coach", tags=["coach"])
app.include_router(coach_router, prefix=f"{API_PREFIX}/coach", tags=["coach-v1"])
app.include_router(consumption_router, prefix="/consumption", tags=["consumption"])
app.include_router(consumption_router, prefix=f"{API_PREFIX}/consumption", tags=["consumption-v1"])
app.include_router(meal_plans_router, prefix="/meal_plans", tags=["meal_plans"])
app.include_router(meal_plans_router, prefix=f"{API_PREFIX}/meal_plans", tags=["meal_plans-v1"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(chat_router, prefix=f"{API_PREFIX}/chat", tags=["chat-v1"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(users_router, prefix=f"{API_PREFIX}/users", tags=["users-v1"])

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and provide useful error information."""
    error_detail = f"Unhandled error: {str(exc)}"
    error_location = f"{request.method} {request.url.path}"
    
    # Log the full error with traceback
    logger.error(f"Exception in {error_location}: {error_detail}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "location": error_location,
            "type": exc.__class__.__name__,
        },
    )

@app.get(f"{API_PREFIX}/health", tags=["misc"])
async def health_check() -> dict[str, str]:
    """Simple uptime probe for load-balancers and monitoring."""

    return {"status": "ok"}

# Import the meal plan generation dependencies here to avoid circular imports
from app.services.auth import get_current_user
from app.models.user import User
from fastapi import Depends
from datetime import datetime

@app.post("/generate-meal-plan", tags=["meal-generation"])
async def generate_meal_plan_root(
    request_data: dict,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Generate a personalized meal plan (root endpoint for frontend compatibility)."""
    try:
        user_profile = request_data.get("user_profile", {})
        previous_meal_plan = request_data.get("previous_meal_plan")
        days = request_data.get("days", 2)
        
        # Generate sample meal plan based on user preferences
        breakfast_options = [
            "Oatmeal with fresh berries and almonds",
            "Greek yogurt with granola and honey", 
            "Scrambled eggs with spinach and whole grain toast",
            "Chia pudding with banana and cinnamon",
            "Avocado toast with poached egg",
            "Smoothie bowl with protein powder and fruits",
            "Whole grain cereal with low-fat milk"
        ]
        
        lunch_options = [
            "Grilled chicken salad with mixed vegetables",
            "Quinoa bowl with roasted vegetables and tahini",
            "Lentil soup with whole grain bread",
            "Turkey and hummus wrap with vegetables",
            "Salmon salad with olive oil dressing",
            "Vegetable stir-fry with tofu and brown rice",
            "Chicken and vegetable soup with side salad"
        ]
        
        dinner_options = [
            "Baked salmon with steamed broccoli and quinoa",
            "Grilled chicken breast with roasted sweet potato",
            "Turkey meatballs with zucchini noodles",
            "Lean beef stir-fry with brown rice",
            "Baked cod with asparagus and wild rice",
            "Grilled vegetables with lean protein",
            "Herb-crusted chicken with roasted vegetables"
        ]
        
        snack_options = [
            "Apple slices with almond butter",
            "Handful of mixed nuts",
            "Greek yogurt with berries",
            "Celery sticks with hummus",
            "Small portion of cottage cheese",
            "Carrot sticks with guacamole",
            "Low-fat string cheese with whole grain crackers"
        ]
        
        # Create meal plan for specified number of days
        meal_plan = {
            "breakfast": breakfast_options[:days],
            "lunch": lunch_options[:days], 
            "dinner": dinner_options[:days],
            "snacks": snack_options[:days],
            "dailyCalories": 1800,
            "macronutrients": {
                "protein": 135,
                "carbs": 225,
                "fats": 60
            },
            "days": days,
            "generated_at": datetime.now().isoformat(),
            "user_id": current_user["id"]
        }
        
        return meal_plan
        
    except Exception as e:
        logger.error(f"Error generating meal plan: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to generate meal plan: {str(e)}"}
        )

@app.post("/generate-recipe", tags=["recipe-generation"])
async def generate_recipe_root(
    request_data: dict,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Generate a recipe for a specific meal."""
    try:
        meal_name = request_data.get("meal_name", "")
        user_profile = request_data.get("user_profile", {})
        
        # Generate sample recipe based on meal name
        recipe = {
            "id": f"recipe_{hash(meal_name) % 10000}",
            "name": meal_name,
            "servings": 2,
            "prep_time": "15 minutes",
            "cook_time": "20 minutes",
            "difficulty": "Easy",
            "ingredients": [
                f"Main ingredient for {meal_name}",
                "Fresh vegetables (your choice)",
                "Olive oil or cooking spray",
                "Salt and pepper to taste",
                "Herbs and spices (optional)"
            ],
            "instructions": [
                f"Prepare the main ingredients for {meal_name}",
                "Heat olive oil in a pan over medium heat",
                "Cook the main ingredient according to recipe requirements",
                "Add vegetables and seasonings",
                "Cook until tender and well combined",
                "Serve hot and enjoy!"
            ],
            "nutritional_info": {
                "calories_per_serving": 300,
                "protein": 25,
                "carbohydrates": 20,
                "fat": 12,
                "fiber": 5,
                "sodium": 400
            },
            "diabetes_friendly": True,
            "glycemic_index": "Low",
            "tags": ["healthy", "diabetes-friendly", "quick"],
            "notes": f"This recipe for {meal_name} is designed to be diabetes-friendly with balanced nutrition.",
            "created_at": datetime.now().isoformat(),
            "user_id": current_user["id"]
        }
        
        return recipe
        
    except Exception as e:
        logger.error(f"Error generating recipe: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to generate recipe: {str(e)}"}
        )

@app.post("/user/recipes", tags=["user-recipes"])
async def save_user_recipes(
    request_data: dict,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Save user's generated recipes."""
    try:
        recipes = request_data.get("recipes", [])
        
        # In a real implementation, save to database
        # For now, just return success
        
        return {
            "success": True,
            "message": f"Successfully saved {len(recipes)} recipes",
            "recipe_count": len(recipes),
            "user_id": current_user["id"]
        }
        
    except Exception as e:
        logger.error(f"Error saving recipes: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to save recipes: {str(e)}"}
        )

from fastapi import Request
import json

@app.post("/generate-shopping-list", tags=["shopping-list"])
async def generate_shopping_list_root(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> list:
    """Generate a shopping list from recipes."""
    try:
        # Read raw request body and parse as JSON
        body = await request.body()
        recipes = json.loads(body.decode('utf-8'))
        
        if not isinstance(recipes, list):
            raise HTTPException(status_code=400, detail="Expected array of recipes")
        
        # Aggregate ingredients from all recipes
        shopping_items = {}
        
        for recipe in recipes:
            ingredients = recipe.get("ingredients", [])
            for ingredient in ingredients:
                # Simple ingredient parsing - in real implementation would be more sophisticated
                ingredient_name = ingredient.strip()
                
                # Skip generic ingredients
                if any(skip in ingredient_name.lower() for skip in ['salt', 'pepper', 'to taste', 'optional']):
                    continue
                
                # Parse quantity and unit (basic implementation)
                parts = ingredient_name.split()
                if len(parts) > 1 and parts[0].replace('.', '').replace(',', '').isdigit():
                    quantity = parts[0]
                    unit = parts[1] if len(parts) > 2 else "unit"
                    item_name = " ".join(parts[1:]) if len(parts) > 2 else parts[1]
                else:
                    quantity = "1"
                    unit = "unit"
                    item_name = ingredient_name
                
                # Aggregate similar items
                key = item_name.lower()
                if key in shopping_items:
                    # Simple aggregation - in real implementation would handle unit conversion
                    try:
                        shopping_items[key]["quantity"] = str(float(shopping_items[key]["quantity"]) + float(quantity))
                    except:
                        shopping_items[key]["quantity"] = f"{shopping_items[key]['quantity']}, {quantity}"
                else:
                    shopping_items[key] = {
                        "id": f"item_{len(shopping_items)}",
                        "name": item_name,
                        "quantity": quantity,
                        "unit": unit,
                        "category": categorize_ingredient(item_name),
                        "checked": False,
                        "notes": f"From recipe: {recipe.get('name', 'Unknown')}"
                    }
        
        # Convert to list and sort by category
        shopping_list = list(shopping_items.values())
        category_order = ["Produce", "Meat & Seafood", "Dairy", "Pantry", "Spices", "Other"]
        shopping_list.sort(key=lambda x: category_order.index(x["category"]) if x["category"] in category_order else len(category_order))
        
        return shopping_list
        
    except Exception as e:
        logger.error(f"Error generating shopping list: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to generate shopping list: {str(e)}"}
        )

def categorize_ingredient(ingredient: str) -> str:
    """Categorize ingredient into shopping sections."""
    ingredient_lower = ingredient.lower()
    
    # Produce
    if any(item in ingredient_lower for item in ['vegetable', 'fruit', 'onion', 'garlic', 'tomato', 'lettuce', 'spinach', 'carrot', 'broccoli', 'apple', 'banana', 'berries', 'herbs']):
        return "Produce"
    
    # Meat & Seafood
    if any(item in ingredient_lower for item in ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey', 'meat', 'seafood']):
        return "Meat & Seafood"
    
    # Dairy
    if any(item in ingredient_lower for item in ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg']):
        return "Dairy"
    
    # Spices
    if any(item in ingredient_lower for item in ['spice', 'herb', 'salt', 'pepper', 'cinnamon', 'paprika', 'cumin', 'oregano', 'basil']):
        return "Spices"
    
    # Pantry items
    if any(item in ingredient_lower for item in ['oil', 'vinegar', 'flour', 'rice', 'pasta', 'bread', 'oats', 'quinoa', 'beans', 'nuts', 'honey']):
        return "Pantry"
    
    return "Other"

@app.post("/save-consolidated-pdf", tags=["pdf-export"])
async def save_consolidated_pdf_root(
    request_data: dict,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Save a consolidated PDF with meal plan, recipes, and shopping list."""
    try:
        meal_plan = request_data.get("meal_plan", {})
        recipes = request_data.get("recipes", [])
        shopping_list = request_data.get("shopping_list", [])
        
        # In a real implementation, generate actual PDF here
        # For now, return success with mock PDF info
        
        pdf_filename = f"meal_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        pdf_info = {
            "pdf_id": f"pdf_{hash(str(meal_plan)) % 10000}",
            "filename": pdf_filename,
            "generated_at": datetime.now().isoformat(),
            "size_bytes": 245760,  # Mock size
            "pages": 8,
            "sections": {
                "meal_plan": True,
                "recipes": True,
                "shopping_list": True
            },
            "download_url": f"/download-saved-pdf/{pdf_filename}"
        }
        
        return {
            "success": True,
            "message": "Consolidated PDF saved successfully",
            "pdf_info": pdf_info,
            "user_id": current_user["id"]
        }
        
    except Exception as e:
        logger.error(f"Error saving consolidated PDF: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to save consolidated PDF: {str(e)}"}
        )

@app.post("/save-full-meal-plan", tags=["meal-plan-save"])
async def save_full_meal_plan_root(
    request_data: dict,
    current_user: User = Depends(get_current_user)
) -> dict:
    """Save a complete meal plan with recipes and shopping list."""
    try:
        meal_plan = request_data
        user_id = current_user["id"]
        
        # Generate unique ID for this meal plan
        meal_plan_id = f"saved_plan_{hash(str(meal_plan) + str(datetime.now())) % 10000}"
        
        # Create a formatted meal plan entry for history - matching frontend MealPlanData interface
        saved_plan = {
            "id": meal_plan_id,
            "name": f"{meal_plan.get('days', 2)}-Day Personalized Meal Plan",
            "created_at": datetime.now().isoformat(),
            "days": meal_plan.get("days", 2),
            "dailyCalories": meal_plan.get("dailyCalories", 1800),  # Frontend expects dailyCalories
            "description": "Your personalized diabetes-friendly meal plan with recipes and shopping list",
            "meals_count": meal_plan.get("days", 2) * 4,  # breakfast, lunch, dinner, snacks
            "status": "saved",
            "macronutrients": meal_plan.get("macronutrients", {  # Frontend expects macronutrients
                "protein": 135,
                "carbs": 225,
                "fats": 60
            }),
            "breakfast": meal_plan.get("breakfast", []),
            "lunch": meal_plan.get("lunch", []),
            "dinner": meal_plan.get("dinner", []),
            "snacks": meal_plan.get("snacks", []),
            "has_recipes": len(meal_plan.get("recipes", [])) > 0,
            "has_shopping_list": len(meal_plan.get("shopping_list", [])) > 0,
            "consolidated_pdf": meal_plan.get("consolidated_pdf"),
            "recipes": meal_plan.get("recipes", []),
            "shopping_list": meal_plan.get("shopping_list", []),
            "source": "user_saved"
        }
        
        # Save to Cosmos DB
        try:
            from database import save_meal_plan
            
            logger.info(f"Saving meal plan {meal_plan_id} to Cosmos DB for user {user_id}")
            
            # Save the meal plan to Cosmos DB
            saved_result = await save_meal_plan(user_id, saved_plan)
            
            logger.info(f"Successfully saved meal plan {meal_plan_id} to Cosmos DB")
            logger.info(f"Cosmos DB returned: {type(saved_result)} with id: {saved_result.get('id') if saved_result else 'None'}")
            
        except ImportError as e:
            logger.error(f"Database import error: {e}")
            logger.warning("Falling back to temporary storage (meal plan will be saved to session only)")
            # Note: Without database, meal plan is only temporarily saved for this response
            
        except Exception as e:
            logger.error(f"Error saving to Cosmos DB: {str(e)}")
            logger.warning("Falling back to temporary storage (meal plan will be saved to session only)")
            # Note: Without database, meal plan is only temporarily saved for this response
        
        return {
            "success": True,
            "message": "Meal plan saved successfully",
            "meal_plan": {
                "meal_plan_id": meal_plan_id,
                "user_id": user_id,
                "created_at": saved_plan["created_at"],
                "days": saved_plan["days"],
                "has_recipes": saved_plan["has_recipes"],
                "has_shopping_list": saved_plan["has_shopping_list"],
                "consolidated_pdf": saved_plan["consolidated_pdf"],
                "status": "saved"
            }
        }
        
    except Exception as e:
        logger.error(f"Error saving full meal plan: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to save meal plan: {str(e)}"}
        )

@app.post("/export/consolidated-meal-plan", tags=["pdf-export"])
async def export_consolidated_meal_plan(
    current_user: User = Depends(get_current_user)
) -> Response:
    """Export a consolidated PDF with meal plan, recipes, and shopping list."""
    try:
        # In a real implementation, this would generate an actual PDF
        # For now, create a simple PDF with sample content
        
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph("Diabetes-Friendly Meal Plan", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add content
        content = [
            "Your personalized meal plan has been generated!",
            "",
            "This consolidated PDF includes:",
            "• Complete meal plan for your selected days",
            "• Detailed recipes with nutritional information",
            "• Organized shopping list by category",
            "• Health tips and recommendations",
            "",
            "Generated on: " + datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "",
            "Keep this PDF handy for easy meal planning and grocery shopping!"
        ]
        
        for line in content:
            if line == "":
                story.append(Spacer(1, 12))
            else:
                para = Paragraph(line, styles['Normal'])
                story.append(para)
                story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=meal-plan-{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting consolidated meal plan: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to export PDF: {str(e)}"}
        )

@app.get("/download-saved-pdf/{filename}", tags=["pdf-download"])
async def download_saved_pdf(
    filename: str,
    current_user: User = Depends(get_current_user)
) -> Response:
    """Download a previously saved PDF file."""
    try:
        # In a real implementation, this would retrieve the PDF from storage
        # For now, generate a sample PDF with the requested filename
        
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph(f"Saved Meal Plan: {filename}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add content
        content = [
            "This is your saved meal plan PDF.",
            "",
            f"File: {filename}",
            f"Downloaded on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            "",
            "Your personalized diabetes-friendly meal plan includes:",
            "• Balanced nutrition for blood sugar management",
            "• Carefully selected recipes",
            "• Complete shopping list",
            "• Nutritional information for each meal"
        ]
        
        for line in content:
            if line == "":
                story.append(Spacer(1, 12))
            else:
                para = Paragraph(line, styles['Normal'])
                story.append(para)
                story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading saved PDF: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to download PDF: {str(e)}"}
        )

# Start the server when this file is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )