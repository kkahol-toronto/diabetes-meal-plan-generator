# API Configuration Constants
APP_TITLE = "Diabetes Diet Manager API"
APP_VERSION = "1.0.0"

# Authentication Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours for better user experience

# OpenAI API Default Parameters
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 60

# OpenAI API Parameters for specific use cases
CREATIVE_TEMPERATURE = 0.8
PRECISE_TEMPERATURE = 0.3
MEAL_PLAN_MAX_TOKENS = 4000
RECIPE_MAX_TOKENS = 1500
CHAT_MAX_TOKENS = 800
PROTEIN_SUGGESTION_MAX_TOKENS = 500
MEAL_SUGGESTION_MAX_TOKENS = 600
ANALYSIS_MAX_TOKENS = 1000
PATIENT_MEDICAL_ADVICE_MAX_TOKENS = 4000  # For comprehensive medical assessments
SHORT_TIMEOUT = 30
LONG_MAX_TOKENS = 20000

# Nutritional Constants
DEFAULT_CALORIE_TARGET = "2000"
SNACK_CALORIE_LIMIT = 200

# Fallback Meal Options
BREAKFAST_OPTIONS = [
    "Oatmeal with berries and cinnamon",
    "Greek yogurt with nuts and seeds",
    "Whole grain toast with avocado",
    "Smoothie with spinach and banana",
    "Chia seed pudding with fruit",
    "Quinoa breakfast bowl with vegetables",
    "Almond butter on whole grain toast"
]

LUNCH_OPTIONS = [
    "Quinoa salad with mixed vegetables",
    "Lentil soup with whole grain bread",
    "Chickpea curry with brown rice",
    "Vegetable stir-fry with tofu",
    "Bean and vegetable wrap",
    "Hummus with vegetable sticks",
    "Stuffed bell peppers with quinoa"
]

DINNER_OPTIONS = [
    "Baked sweet potato with black beans",
    "Vegetable curry with brown rice",
    "Grilled vegetables with quinoa",
    "Lentil dal with steamed vegetables",
    "Stuffed zucchini with vegetables",
    "Roasted vegetables with chickpeas",
    "Vegetable soup with whole grain bread"
]

SNACK_OPTIONS = [
    "Mixed nuts and seeds",
    "Apple slices with almond butter",
    "Carrot sticks with hummus",
    "Berries with Greek yogurt",
    "Cucumber slices with tahini",
    "Roasted chickpeas",
    "Homemade trail mix"
]

# Non-vegetarian meal additions
NON_VEG_LUNCH_ADDITIONS = [
    "Grilled chicken salad with quinoa",
    "Turkey and vegetable wrap",
    "Salmon with roasted vegetables"
]

NON_VEG_DINNER_ADDITIONS = [
    "Baked salmon with sweet potato",
    "Grilled chicken with quinoa and vegetables",
    "Turkey meatballs with vegetable pasta"
]

# Recipe Templates
RECIPE_TEMPLATES = {
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
            "1 cup leafy greens (spinach or kale)",
            "1/2 cup beans or lentils",
            "2 cloves garlic, minced",
            "1 tsp dried herbs (thyme, oregano)",
            "Salt and pepper to taste"
        ],
        "instructions": [
            "Sauté onions and garlic until fragrant",
            "Add other vegetables and cook for 5 minutes",
            "Add broth and bring to a boil",
            "Reduce heat and simmer for 15-20 minutes",
            "Add beans and leafy greens",
            "Season with herbs, salt, and pepper",
            "Simmer for 5 more minutes and serve"
        ],
        "nutritional_info": {
            "calories": 180,
            "protein": 8,
            "carbs": 30,
            "fat": 2
        }
    }
}

# Default Profile Values
DEFAULT_PATIENT_PROFILE = {
    "name": "Test Patient",
    "age": 45,
    "gender": "Other",
    "condition": "Type 2 Diabetes",
    "medicalConditions": ["Type 2 Diabetes"],
    "currentMedications": [],
    "dietType": ["Balanced"],
    "dietaryRestrictions": [],
    "allergies": [],
    "calorieTarget": DEFAULT_CALORIE_TARGET,
    "timezone": "UTC"
}

# API Response Messages
API_SUCCESS_MESSAGES = {
    "meal_plan_generated": "Meal plan generated successfully",
    "recipe_generated": "Recipe generated successfully",
    "profile_updated": "Profile updated successfully",
    "consumption_logged": "Consumption logged successfully"
}

API_ERROR_MESSAGES = {
    "invalid_profile": "Invalid profile data provided",
    "user_not_found": "User not found",
    "meal_plan_failed": "Failed to generate meal plan",
    "recipe_failed": "Failed to generate recipe",
    "consumption_failed": "Failed to log consumption"
}

# PDF Export Configuration
PDF_TITLE = "Health Data Export"
PDF_PAGE_SIZE = "letter"

# Time-based Constants  
MORNING_CUTOFF_HOUR = 11
AFTERNOON_CUTOFF_HOUR = 16
EVENING_CUTOFF_HOUR = 20

# Meal Time Mappings
MEAL_TIMES = {
    "breakfast": {"start": 6, "end": 11},
    "lunch": {"start": 11, "end": 16}, 
    "dinner": {"start": 16, "end": 22},
    "snack": {"start": 9, "end": 21}
}

# Analytics Constants
MIN_CONSISTENCY_DAYS = 3
MAX_CONSISTENCY_STREAK = 30
NUTRITION_SCORE_WEIGHTS = {
    "calories": 0.3,
    "protein": 0.25,
    "carbs": 0.25,
    "fat": 0.2
}

# Dietary Restrictions Keywords
VEGETARIAN_KEYWORDS = ["vegetarian", "vegan", "plant-based"]
EGG_KEYWORDS = ["egg", "eggs"]
DAIRY_KEYWORDS = ["dairy", "milk", "cheese", "yogurt"]
GLUTEN_KEYWORDS = ["gluten", "wheat", "bread"]

# Exponential Backoff Configuration
MAX_BACKOFF_SECONDS = 60
BASE_BACKOFF_MULTIPLIER = 2 