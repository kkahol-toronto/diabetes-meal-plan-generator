import os
import random
import string
from twilio.rest import Client
from config import twilio_client

def send_registration_code(phone: str, code: str):
    """Send registration code via SMS using Twilio"""
    try:
        message = twilio_client.messages.create(
            body=f"Your registration code for Diabetes Diet Manager is: {code}",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=phone
        )
        print(f"Twilio message sent successfully: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return None

def sanitize_vegetarian_meal(meal_text: str, is_vegetarian: bool, no_eggs: bool) -> str:
    """
    Ensure meal is vegetarian and egg-free with strong enforcement.
    Also validates against corrupted or nonsensical meal data.
    """
    if not meal_text:
        return "Vegetarian meal option"
    
    meal_lower = meal_text.lower().strip()
    
    # Check for corrupted or nonsensical meal patterns
    def is_corrupted_meal(text: str) -> bool:
        """Check if meal text is corrupted or nonsensical"""
        import re
        suspicious_patterns = [
            r'^\d+\/\d+\s+\w+\s+fruit',  # "1/2 Lindt fruit" pattern
            r'^[0-9]+\/[0-9]+',          # Starts with fractions
            r'lindt',                     # Brand names that don't make sense as meals
            r'^[0-9]+\s+(g|ml|oz|cups?|tbsp|tsp)\s*$',  # Just quantities
            r'^[\d\s\/\-\.]+$',          # Only numbers and punctuation
            r'^[a-z]{1,2}$',             # Single letters or very short nonsense
            r'^\s*$',                    # Empty or whitespace only
        ]
        return any(re.search(pattern, text.lower()) for pattern in suspicious_patterns)
    
    # If corrupted, return a safe default
    if is_corrupted_meal(meal_text):
        print(f"[sanitize_vegetarian_meal] Detected corrupted meal text: '{meal_text}' - replacing with safe option")
        return "Healthy balanced meal option"
    
    # Check for non-vegetarian ingredients
    non_veg_keywords = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'lamb', 'meat', 'seafood', 'shrimp', 'bacon', 'ham', 'duck', 'goose', 'veal', 'venison', 'rabbit', 'sausage', 'pepperoni', 'salami', 'prosciutto', 'chorizo', 'ground beef', 'ground turkey', 'chicken breast', 'chicken thigh', 'steak', 'roast beef', 'pork chop', 'fish fillet', 'crab', 'lobster', 'scallops', 'mussels', 'clams', 'oysters', 'cod', 'tilapia', 'halibut', 'sardines', 'anchovies', 'mackerel']
    
    # ENHANCED: Comprehensive egg detection including all egg-containing dishes and ingredients
    egg_keywords = [
        # Direct egg references
        'egg', 'eggs', 'egg white', 'egg yolk', 'whole egg', 'beaten egg', 'raw egg',
        # Egg-based dishes
        'omelet', 'omelette', 'scrambled', 'poached', 'fried egg', 'boiled egg', 'hard-boiled', 'soft-boiled',
        'egg sandwich', 'breakfast sandwich', 'egg muffin', 'egg wrap', 'egg salad', 'deviled egg',
        'eggs benedict', 'scotch egg', 'pickled egg', 'egg drop soup', 'egg roll',
        # Egg-containing foods and preparations  
        'mayonnaise', 'mayo', 'hollandaise', 'custard', 'meringue', 'eggnog', 'zabaglione',
        'french toast', 'pancake', 'waffle', 'crepe', 'quiche', 'frittata', 'strata', 'souffle',
        'carbonara', 'caesar dressing', 'caesar salad', 'aioli', 'tartar sauce', 'thousand island',
        # Baked goods that typically contain eggs
        'muffin', 'cake', 'cupcake', 'cookie', 'brownie', 'pastry', 'donut', 'danish', 'croissant',
        'brioche', 'challah', 'bagel', 'english muffin', 'scone', 'biscuit',
        # Other egg-containing items
        'pasta carbonara', 'egg noodles', 'fresh pasta', 'homemade pasta', 'batter', 'tempura',
        'fried chicken', 'breaded', 'coated', 'dumplings', 'gnocchi', 'egg bread'
    ]
    
    if is_vegetarian and any(keyword in meal_lower for keyword in non_veg_keywords):
        print(f"[sanitize_vegetarian_meal] Replacing non-vegetarian meal: '{meal_text}'")
        return "Vegetarian lentil curry with brown rice and steamed vegetables"
    
    if no_eggs and any(keyword in meal_lower for keyword in egg_keywords):
        print(f"[sanitize_vegetarian_meal] CRITICAL: Replacing egg-containing meal: '{meal_text}' - found egg ingredient")
        # Return a safe, guaranteed egg-free option
        return "Vegetarian quinoa bowl with roasted vegetables and tahini dressing"
    
    return meal_text

def generate_safe_vegetarian_fallback(user_email: str, remaining_calories: int, is_vegetarian: bool, no_eggs: bool):
    """
    Generate safe vegetarian fallback meal plan with intelligent snack recommendations.
    """
    from datetime import datetime
    
    today = datetime.utcnow().date()
    
    # Diverse vegetarian options
    vegetarian_options = {
        "breakfast": [
            "Steel-cut oats with almond milk and fresh berries",
            "Quinoa breakfast bowl with coconut yogurt and mango",
            "Chia seed pudding with vanilla and strawberries",
            "Smoothie bowl with spinach, banana, and granola"
        ],
        "lunch": [
            "Mediterranean chickpea salad with cucumber and herbs",
            "Quinoa Buddha bowl with roasted vegetables and tahini",
            "Lentil soup with whole grain bread and mixed greens",
            "Vegetable curry with brown rice and cilantro"
        ],
        "dinner": [
            "Thai-inspired tofu curry with jasmine rice",
            "Stuffed bell peppers with quinoa and vegetables",
            "Lentil dal with naan bread and steamed broccoli",
            "Vegetable stir-fry with tofu and brown rice"
        ],
        "snack": [
            "Apple slices with almond butter",
            "Roasted chickpeas with paprika and lime",
            "Hummus with cucumber slices and whole grain crackers",
            "Mixed nuts and dried fruit (if no nut allergy)"
        ]
    }
    
    # Select diverse options
    selected_meals = {}
    for meal_type, options in vegetarian_options.items():
        if meal_type == "snack":
            # Apply intelligent snack logic based on remaining calories
            if remaining_calories <= 100:
                selected_meals[meal_type] = "No additional snacks needed - you've reached your calorie goal for today"
            elif remaining_calories <= 200:
                selected_meals[meal_type] = "Optional light snack only if genuinely hungry (e.g., cucumber slices, herbal tea)"
            elif remaining_calories <= 300:
                selected_meals[meal_type] = "Light snack if needed (e.g., 1 small apple, handful of berries)"
            else:
                selected_meals[meal_type] = random.choice(options)
        else:
            selected_meals[meal_type] = random.choice(options)
    
    return {
        "id": f"safe_vegetarian_{user_email}_{today.isoformat()}",
        "date": today.isoformat(),
        "type": "safe_vegetarian_fallback",
        "meals": selected_meals,
        "dailyCalories": 2000,
        "remaining_calories": remaining_calories,
        "created_at": datetime.utcnow().isoformat(),
        "notes": f"Safe vegetarian fallback meal plan. Remaining calories: {remaining_calories}"
    } 