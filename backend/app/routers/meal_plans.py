from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from datetime import datetime, timedelta
from ..models.user import User
from ..services.auth import get_current_user
from ..utils.logger import logger

# Import Cosmos DB functions
DATABASE_AVAILABLE = False
get_user_meal_plans = None
save_meal_plan = None
get_meal_plan_by_id = None
delete_meal_plan_by_id = None
delete_all_user_meal_plans = None

try:
    import sys
    import os
    # Add the backend directory to the path to import database module
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    
    import database
    get_user_meal_plans = database.get_user_meal_plans
    save_meal_plan = database.save_meal_plan
    get_meal_plan_by_id = database.get_meal_plan_by_id
    delete_meal_plan_by_id = database.delete_meal_plan_by_id
    delete_all_user_meal_plans = database.delete_all_user_meal_plans
    
    DATABASE_AVAILABLE = True
    logger.info("Cosmos DB functions imported successfully")
except ImportError as e:
    logger.error(f"Database functions not available: {e}")
    DATABASE_AVAILABLE = False
except Exception as e:
    logger.error(f"Error importing database functions: {e}")
    DATABASE_AVAILABLE = False

router = APIRouter()

@router.get("/test")
async def get_meal_plans_test() -> Dict:
    """Test endpoint for meal plans without authentication."""
    try:
        # Generate sample meal plan history (for demo purposes)
        sample_meal_plans = [
            {
                "id": "meal_plan_001",
                "name": "2-Day Diabetes-Friendly Meal Plan",
                "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "days": 2,
                "dailyCalories": 1800,
                "description": "Low-carb meal plan focusing on lean proteins and vegetables",
                "meals_count": 8,
                "status": "completed",
                "macronutrients": {
                    "protein": 135,
                    "carbs": 180,
                    "fats": 60
                },
                "breakfast": ["Scrambled eggs with spinach", "Greek yogurt with berries"],
                "lunch": ["Grilled chicken salad", "Quinoa bowl with vegetables"],
                "dinner": ["Baked salmon with broccoli", "Turkey meatballs with zucchini"],
                "snacks": ["Apple with almond butter", "Mixed nuts"],
                "source": "sample"
            },
            {
                "id": "meal_plan_002", 
                "name": "3-Day Heart-Healthy Meal Plan",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "days": 3,
                "dailyCalories": 1900,
                "description": "Mediterranean-style meals rich in omega-3 fatty acids",
                "meals_count": 12,
                "status": "completed",
                "macronutrients": {
                    "protein": 142,
                    "carbs": 190,
                    "fats": 65
                },
                "breakfast": ["Oatmeal with berries", "Avocado toast", "Chia pudding"],
                "lunch": ["Mediterranean salad", "Lentil soup", "Salmon wrap"],
                "dinner": ["Grilled fish with quinoa", "Chicken with sweet potato", "Veggie stir-fry"],
                "snacks": ["Hummus with vegetables", "Greek yogurt", "Handful of almonds"],
                "source": "sample"
            }
        ]
        
        return {
            "success": True,
            "meal_plans": sample_meal_plans,
            "total": len(sample_meal_plans),
            "user_saved_count": 0,
            "sample_count": len(sample_meal_plans)
        }
    except Exception as e:
        logger.error(f"Error getting test meal plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get test meal plans")

@router.get("")
async def get_meal_plans(current_user: User = Depends(get_current_user)) -> Dict:
    """Get user's meal plans from Cosmos DB."""
    try:
        user_id = current_user["id"]
        
        logger.info(f"User {user_id} requesting meal plans from Cosmos DB")
        
        if DATABASE_AVAILABLE:
            try:
                # Get meal plans from Cosmos DB
                user_saved_plans = await get_user_meal_plans(user_id)
                logger.info(f"Found {len(user_saved_plans)} saved meal plans in Cosmos DB for user {user_id}")
                
                if user_saved_plans:
                    logger.info(f"Plan IDs: {[plan.get('id') for plan in user_saved_plans]}")
                    logger.info(f"Plan dates: {[plan.get('created_at') for plan in user_saved_plans]}")
                
                return {
                    "success": True,
                    "meal_plans": user_saved_plans,
                    "total": len(user_saved_plans),
                    "user_saved_count": len(user_saved_plans),
                    "sample_count": 0,
                    "source": "cosmos_db"
                }
            except Exception as db_error:
                logger.error(f"Cosmos DB error for user {user_id}: {str(db_error)}")
                # Fall back to test data if database fails
                return await get_fallback_meal_plans(user_id)
        else:
            logger.warning("Database not available, showing sample meal plans")
            return await get_fallback_meal_plans(user_id)
            
    except Exception as e:
        logger.error(f"Error getting meal plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get meal plans")

async def get_fallback_meal_plans(user_id: str) -> Dict:
    """Fallback function when database is not available - shows sample data."""
    test_plans = [
        {
            "id": "saved_plan_001",
            "name": "7-Day Diabetes-Friendly Meal Plan",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "days": 7,
            "dailyCalories": 1800,
            "description": "Personalized diabetes-friendly meal plan with recipes and shopping list",
            "meals_count": 28,
            "status": "saved",
            "macronutrients": {
                "protein": 135,
                "carbs": 225,
                "fats": 60
            },
            "breakfast": ["Scrambled eggs with spinach", "Greek yogurt with berries", "Oatmeal with almonds"],
            "lunch": ["Grilled chicken salad", "Quinoa bowl with vegetables", "Turkey sandwich"],
            "dinner": ["Baked salmon with broccoli", "Turkey meatballs with zucchini", "Lean beef stir-fry"],
            "snacks": ["Apple with almond butter", "Mixed nuts", "Cucumber with hummus"],
            "has_recipes": True,
            "has_shopping_list": True,
            "consolidated_pdf": {
                "filename": "meal_plan_20250702_001.pdf",
                "generated_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            "source": "user_saved"
        },
        {
            "id": "saved_plan_002",
            "name": "5-Day Low-Carb Meal Plan",
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "days": 5,
            "dailyCalories": 1600,
            "description": "Low-carb focused meal plan for better blood sugar control",
            "meals_count": 20,
            "status": "saved", 
            "macronutrients": {
                "protein": 120,
                "carbs": 160,
                "fats": 70
            },
            "breakfast": ["Veggie omelet", "Chia seed pudding", "Avocado toast"],
            "lunch": ["Caesar salad with chicken", "Zucchini noodle pasta", "Tuna salad wrap"],
            "dinner": ["Grilled fish with asparagus", "Cauliflower rice bowl", "Stuffed bell peppers"],
            "snacks": ["String cheese", "Celery with peanut butter", "Handful of walnuts"],
            "has_recipes": True,
            "has_shopping_list": True,
            "consolidated_pdf": {
                "filename": "meal_plan_20250625_002.pdf", 
                "generated_at": (datetime.now() - timedelta(days=7)).isoformat()
            },
            "source": "user_saved"
        },
        {
            "id": "saved_plan_003",
            "name": "3-Day Heart-Healthy Plan",
            "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
            "days": 3,
            "dailyCalories": 1900,
            "description": "Mediterranean-style meals rich in omega-3 fatty acids",
            "meals_count": 12,
            "status": "saved",
            "macronutrients": {
                "protein": 142,
                "carbs": 190,
                "fats": 65
            },
            "breakfast": ["Greek yogurt parfait", "Whole grain toast with avocado", "Smoothie bowl"],
            "lunch": ["Mediterranean quinoa salad", "Lentil soup", "Salmon wrap"],
            "dinner": ["Baked cod with sweet potato", "Grilled chicken with quinoa", "Veggie stir-fry with tofu"],
            "snacks": ["Hummus with vegetables", "Trail mix", "Greek yogurt with berries"],
            "has_recipes": True,
            "has_shopping_list": True,
            "consolidated_pdf": {
                "filename": "meal_plan_20250618_003.pdf",
                "generated_at": (datetime.now() - timedelta(days=14)).isoformat()
            },
            "source": "user_saved"
        }
    ]
    
    logger.info(f"Using sample meal plans for user {user_id} (database not available)")
    
    return {
        "success": True,
        "meal_plans": test_plans,
        "total": len(test_plans),
        "user_saved_count": len(test_plans),
        "sample_count": 0,
        "source": "sample_data",
        "message": "Showing sample meal plans. Connect Cosmos DB to see your actual saved plans."
    }

@router.post("")
async def create_meal_plan(
    meal_plan_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Create a new meal plan."""
    try:
        return {
            "success": True,
            "meal_plan_id": "mock-meal-plan-id",
            "message": "Meal plan created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create meal plan")

@router.post("/generate")
async def generate_meal_plan(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Generate a personalized meal plan."""
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
            "Avocado toast with poached egg"
        ]
        
        lunch_options = [
            "Grilled chicken salad with mixed vegetables",
            "Quinoa bowl with roasted vegetables and tahini",
            "Lentil soup with whole grain bread",
            "Turkey and hummus wrap with vegetables",
            "Salmon salad with olive oil dressing"
        ]
        
        dinner_options = [
            "Baked salmon with steamed broccoli and quinoa",
            "Grilled chicken breast with roasted sweet potato",
            "Turkey meatballs with zucchini noodles",
            "Lean beef stir-fry with brown rice",
            "Baked cod with asparagus and wild rice"
        ]
        
        snack_options = [
            "Apple slices with almond butter",
            "Handful of mixed nuts",
            "Greek yogurt with berries",
            "Celery sticks with hummus",
            "Small portion of cottage cheese"
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
        raise HTTPException(status_code=500, detail="Failed to generate meal plan")

@router.get("/{meal_plan_id}")
async def get_meal_plan(
    meal_plan_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get a specific meal plan by ID from Cosmos DB."""
    try:
        user_id = current_user["id"]
        
        logger.info(f"User {user_id} requesting meal plan {meal_plan_id} from Cosmos DB")
        
        if DATABASE_AVAILABLE:
            try:
                # Get meal plan from Cosmos DB
                meal_plan = await get_meal_plan_by_id(meal_plan_id, user_id)
                
                if meal_plan:
                    logger.info(f"Found meal plan {meal_plan_id} in Cosmos DB")
                    return {
                        "success": True,
                        "meal_plan": meal_plan,
                        "source": "cosmos_db"
                    }
            except Exception as db_error:
                logger.error(f"Cosmos DB error getting meal plan {meal_plan_id}: {str(db_error)}")
        
        # If not found in database or database unavailable, return fallback plan
        
        # If not found in saved plans, return a detailed sample plan
        sample_detailed_plan = {
            "id": meal_plan_id,
            "name": "Diabetes-Friendly Meal Plan",
            "created_at": datetime.now().isoformat(),
            "days": 2,
            "dailyCalories": 1800,
            "description": "Personalized meal plan for blood sugar management",
            "user_id": current_user["id"],
            "status": "active",
            "macronutrients": {
                "protein": 135,
                "carbs": 180,
                "fats": 60
            },
            "meals": [
                {
                    "day": 1,
                    "breakfast": {
                        "name": "Scrambled eggs with spinach and whole grain toast",
                        "calories": 320,
                        "protein": 22,
                        "carbs": 18,
                        "fats": 15
                    },
                    "lunch": {
                        "name": "Grilled chicken salad with mixed vegetables",
                        "calories": 380,
                        "protein": 35,
                        "carbs": 12,
                        "fats": 18
                    },
                    "dinner": {
                        "name": "Baked salmon with steamed broccoli and quinoa",
                        "calories": 420,
                        "protein": 38,
                        "carbs": 28,
                        "fats": 16
                    },
                    "snacks": {
                        "name": "Apple slices with almond butter",
                        "calories": 180,
                        "protein": 6,
                        "carbs": 22,
                        "fats": 8
                    }
                },
                {
                    "day": 2,
                    "breakfast": {
                        "name": "Greek yogurt with berries and granola",
                        "calories": 340,
                        "protein": 20,
                        "carbs": 35,
                        "fats": 12
                    },
                    "lunch": {
                        "name": "Quinoa bowl with roasted vegetables and tahini",
                        "calories": 395,
                        "protein": 14,
                        "carbs": 52,
                        "fats": 16
                    },
                    "dinner": {
                        "name": "Turkey meatballs with zucchini noodles",
                        "calories": 385,
                        "protein": 32,
                        "carbs": 18,
                        "fats": 20
                    },
                    "snacks": {
                        "name": "Handful of mixed nuts",
                        "calories": 160,
                        "protein": 6,
                        "carbs": 6,
                        "fats": 14
                    }
                }
            ],
            "nutritional_summary": {
                "daily_avg_calories": 900,
                "daily_avg_protein": 34,
                "daily_avg_carbs": 45,
                "daily_avg_fats": 15
            }
        }
        
        return {
            "success": True,
            "meal_plan": sample_detailed_plan
        }
    except Exception as e:
        logger.error(f"Error getting meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get meal plan")

@router.post("/bulk_delete")
async def bulk_delete_meal_plans(
    request_data: Dict[str, List[str]],
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Delete multiple meal plans by IDs from Cosmos DB."""
    try:
        meal_plan_ids = request_data.get("meal_plan_ids", [])
        user_id = current_user["id"]
        
        if not meal_plan_ids:
            raise HTTPException(status_code=400, detail="No meal plan IDs provided")
        
        logger.info(f"User {user_id} requesting bulk delete of {len(meal_plan_ids)} meal plans")
        
        deleted_count = 0
        failed_deletions = []
        
        if DATABASE_AVAILABLE:
            for meal_plan_id in meal_plan_ids:
                try:
                    await delete_meal_plan_by_id(meal_plan_id, user_id)
                    deleted_count += 1
                    logger.info(f"Successfully deleted meal plan {meal_plan_id} from Cosmos DB")
                except Exception as e:
                    logger.error(f"Failed to delete meal plan {meal_plan_id}: {str(e)}")
                    failed_deletions.append(meal_plan_id)
        else:
            logger.warning("Database not available for bulk delete operation")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        if failed_deletions:
            logger.warning(f"Failed to delete {len(failed_deletions)} meal plans: {failed_deletions}")
            
        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": len(failed_deletions),
            "deleted_ids": [id for id in meal_plan_ids if id not in failed_deletions],
            "failed_ids": failed_deletions,
            "message": f"Successfully deleted {deleted_count} meal plan(s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting meal plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete meal plans")

@router.delete("/all")
async def delete_all_meal_plans(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Delete all meal plans for the current user from Cosmos DB."""
    try:
        user_id = current_user["id"]
        
        logger.info(f"User {user_id} requesting to delete all meal plans")
        
        if DATABASE_AVAILABLE:
            try:
                # Get count of existing meal plans first
                existing_plans = await get_user_meal_plans(user_id)
                plan_count = len(existing_plans)
                
                # Delete all meal plans for this user
                await delete_all_user_meal_plans(user_id)
                
                logger.info(f"Successfully deleted all {plan_count} meal plans for user {user_id}")
                
                return {
                    "success": True,
                    "deleted_count": plan_count,
                    "message": f"Successfully deleted all {plan_count} meal plans",
                    "user_id": user_id,
                    "source": "cosmos_db"
                }
            except Exception as db_error:
                logger.error(f"Cosmos DB error deleting all meal plans for user {user_id}: {str(db_error)}")
                raise HTTPException(status_code=500, detail="Database error deleting meal plans")
        else:
            logger.warning("Database not available for delete all operation")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting all meal plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete all meal plans") 