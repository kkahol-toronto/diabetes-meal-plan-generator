"""
Comprehensive Demo Data Generator for Diabetes Meal Plan System
Creates multiple test users with varied profiles and realistic consumption data
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

# Configuration
BACKEND_URL = "http://localhost:8000"
DEMO_USERS = [
    {
        "email": "alice.johnson@demo.com",
        "password": "demo123",
        "name": "Alice Johnson",
        "age": 45,
        "diabetes_type": "Type 2",
        "conditions": ["Type 2 Diabetes", "Hypertension"],
        "profile_type": "well_controlled"
    },
    {
        "email": "bob.smith@demo.com", 
        "password": "demo123",
        "name": "Bob Smith",
        "age": 58,
        "diabetes_type": "Type 2",
        "conditions": ["Type 2 Diabetes", "High Cholesterol", "Obesity"],
        "profile_type": "needs_improvement"
    },
    {
        "email": "carol.davis@demo.com",
        "password": "demo123", 
        "name": "Carol Davis",
        "age": 34,
        "diabetes_type": "Type 1",
        "conditions": ["Type 1 Diabetes", "Celiac Disease"],
        "profile_type": "strict_diet"
    },
    {
        "email": "david.wilson@demo.com",
        "password": "demo123",
        "name": "David Wilson", 
        "age": 52,
        "diabetes_type": "Type 2",
        "conditions": ["Type 2 Diabetes", "PCOS", "Hypertension"],
        "profile_type": "multiple_conditions"
    },
    {
        "email": "emma.brown@demo.com",
        "password": "demo123",
        "name": "Emma Brown",
        "age": 29,
        "diabetes_type": "Gestational",
        "conditions": ["Gestational Diabetes"],
        "profile_type": "pregnancy"
    }
]

# Sample foods categorized by diabetes suitability
FOODS_DATABASE = {
    "excellent": [
        {"name": "Grilled Salmon with Broccoli", "calories": 380, "protein": 42, "carbs": 12, "fat": 18, "fiber": 6, "sugar": 4},
        {"name": "Quinoa Bowl with Vegetables", "calories": 420, "protein": 15, "carbs": 45, "fat": 16, "fiber": 8, "sugar": 6},
        {"name": "Greek Yogurt with Berries", "calories": 180, "protein": 15, "carbs": 20, "fat": 5, "fiber": 3, "sugar": 15},
        {"name": "Avocado and Spinach Salad", "calories": 320, "protein": 8, "carbs": 15, "fat": 28, "fiber": 12, "sugar": 3}
    ],
    "good": [
        {"name": "Grilled Chicken Breast", "calories": 350, "protein": 45, "carbs": 8, "fat": 12, "fiber": 2, "sugar": 3},
        {"name": "Brown Rice with Vegetables", "calories": 280, "protein": 8, "carbs": 52, "fat": 4, "fiber": 4, "sugar": 2},
        {"name": "Turkey and Hummus Wrap", "calories": 320, "protein": 25, "carbs": 35, "fat": 10, "fiber": 5, "sugar": 4},
        {"name": "Lentil Soup", "calories": 240, "protein": 18, "carbs": 40, "fat": 2, "fiber": 16, "sugar": 8}
    ],
    "moderate": [
        {"name": "Whole Grain Pasta with Sauce", "calories": 380, "protein": 14, "carbs": 72, "fat": 4, "fiber": 6, "sugar": 12},
        {"name": "Baked Sweet Potato", "calories": 200, "protein": 4, "carbs": 46, "fat": 0, "fiber": 7, "sugar": 13},
        {"name": "Banana and Peanut Butter", "calories": 350, "protein": 12, "carbs": 35, "fat": 18, "fiber": 6, "sugar": 20},
        {"name": "Oatmeal with Fruit", "calories": 280, "protein": 8, "carbs": 54, "fat": 4, "fiber": 8, "sugar": 16}
    ],
    "poor": [
        {"name": "Pizza Slice", "calories": 450, "protein": 20, "carbs": 45, "fat": 22, "fiber": 3, "sugar": 8},
        {"name": "Chocolate Chip Cookies", "calories": 320, "protein": 4, "carbs": 42, "fat": 16, "fiber": 2, "sugar": 24},
        {"name": "French Fries", "calories": 380, "protein": 5, "carbs": 48, "fat": 19, "fiber": 4, "sugar": 2},
        {"name": "Soda and Sandwich", "calories": 520, "protein": 18, "carbs": 68, "fat": 18, "fiber": 3, "sugar": 35}
    ]
}

def create_demo_user(user_data):
    """Create a single demo user with complete profile"""
    try:
        # Create patient record
        patient_data = {
            "id": user_data["email"].replace("@", "_").replace(".", "_"),
            "name": user_data["name"],
            "phone": "555-0123",
            "condition": user_data["diabetes_type"],
            "medical_conditions": user_data["conditions"],
            "medications": get_medications_for_conditions(user_data["conditions"]),
            "allergies": get_random_allergies(),
            "dietary_restrictions": get_dietary_restrictions(user_data["profile_type"]),
            "registration_code": user_data["email"].replace("@", "_").replace(".", "_").upper(),
            "type": "patient",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create user account
        user_account = {
            "id": user_data["email"],
            "username": user_data["email"], 
            "email": user_data["email"],
            "disabled": False,
            "patient_id": patient_data["id"],
            "type": "user",
            "profile": create_user_profile(user_data)
        }
        
        # Register user
        register_response = requests.post(f"{BACKEND_URL}/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
            "patient_code": patient_data["registration_code"],
            "profile": user_account["profile"]
        })
        
        if register_response.status_code == 200:
            print(f"✅ Created user: {user_data['name']} ({user_data['email']})")
            return True
        else:
            print(f"❌ Failed to create user {user_data['name']}: {register_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user {user_data['name']}: {str(e)}")
        return False

def create_user_profile(user_data):
    """Create a detailed user profile"""
    base_profile = {
        "name": user_data["name"],
        "age": user_data["age"],
        "gender": random.choice(["Male", "Female"]),
        "height": random.randint(155, 185),
        "weight": random.randint(60, 120),
        "medicalConditions": user_data["conditions"],
        "currentMedications": get_medications_for_conditions(user_data["conditions"]),
        "allergies": get_random_allergies(),
        "dietaryRestrictions": get_dietary_restrictions(user_data["profile_type"]),
        "foodPreferences": get_food_preferences(user_data["profile_type"]),
        "calorieTarget": str(get_calorie_target(user_data)),
        "primaryGoals": get_primary_goals(user_data),
        "readinessToChange": random.choice(["Ready to take action", "Already making changes"]),
    }
    
    # Calculate BMI
    bmi = base_profile["weight"] / ((base_profile["height"] / 100) ** 2)
    base_profile["bmi"] = round(bmi, 1)
    
    # Add vital signs
    base_profile["systolicBP"] = random.randint(110, 160)
    base_profile["diastolicBP"] = random.randint(70, 100)
    
    # Macro goals
    calories = int(base_profile["calorieTarget"])
    base_profile["macroGoals"] = {
        "protein": round(calories * 0.2 / 4),  # 20% protein
        "carbs": round(calories * 0.45 / 4),   # 45% carbs  
        "fat": round(calories * 0.35 / 9)      # 35% fat
    }
    
    return base_profile

def get_medications_for_conditions(conditions):
    """Get appropriate medications for medical conditions"""
    medications = []
    for condition in conditions:
        if "Type 2 Diabetes" in condition:
            medications.extend(["Metformin", "Glipizide"])
        elif "Type 1 Diabetes" in condition:
            medications.extend(["Insulin", "Glucose Monitor"])
        elif "Hypertension" in condition:
            medications.append("Lisinopril")
        elif "High Cholesterol" in condition:
            medications.append("Atorvastatin")
        elif "PCOS" in condition:
            medications.append("Spironolactone")
    return list(set(medications))

def get_random_allergies():
    """Get random allergies"""
    all_allergies = ["None", "Shellfish", "Tree Nuts", "Peanuts", "Dairy", "Gluten"]
    return random.sample(all_allergies, random.randint(1, 2))

def get_dietary_restrictions(profile_type):
    """Get dietary restrictions based on profile type"""
    restrictions = {
        "well_controlled": ["Low Glycemic Index"],
        "needs_improvement": ["Low Sodium", "Low Sugar"],
        "strict_diet": ["Gluten-Free", "Low Glycemic Index"],
        "multiple_conditions": ["Low Sodium", "Low Glycemic Index", "Heart Healthy"],
        "pregnancy": ["Pregnancy Safe", "Low Mercury"]
    }
    return restrictions.get(profile_type, ["Low Glycemic Index"])

def get_food_preferences(profile_type):
    """Get food preferences based on profile type"""
    preferences = {
        "well_controlled": ["Mediterranean", "Lean Proteins"],
        "needs_improvement": ["Low Fat", "High Fiber"],
        "strict_diet": ["Gluten-Free", "Plant-based"],
        "multiple_conditions": ["Heart Healthy", "Anti-inflammatory"],
        "pregnancy": ["Nutrient Dense", "Pregnancy Safe"]
    }
    return preferences.get(profile_type, ["Balanced"])

def get_calorie_target(user_data):
    """Calculate appropriate calorie target"""
    base_calories = {
        "well_controlled": 1800,
        "needs_improvement": 1600, 
        "strict_diet": 1900,
        "multiple_conditions": 1700,
        "pregnancy": 2200
    }
    return base_calories.get(user_data["profile_type"], 1800)

def get_primary_goals(user_data):
    """Get primary health goals"""
    goals = {
        "well_controlled": ["Maintain blood sugar", "Stay active"],
        "needs_improvement": ["Lose weight", "Lower blood sugar", "Improve diet"],
        "strict_diet": ["Manage celiac disease", "Stable blood sugar"],
        "multiple_conditions": ["Manage diabetes", "Lower blood pressure", "Reduce cholesterol"],
        "pregnancy": ["Healthy pregnancy", "Manage gestational diabetes"]
    }
    return goals.get(user_data["profile_type"], ["Manage diabetes"])

def generate_consumption_data(email, password, profile_type, days=14):
    """Generate realistic consumption data for a user"""
    try:
        # Login to get token
        login_response = requests.post(f"{BACKEND_URL}/auth/login", data={
            "username": email,
            "password": password
        })
        
        if login_response.status_code != 200:
            print(f"❌ Failed to login for {email}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Generate consumption data for each day
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            daily_foods = select_daily_foods(profile_type)
            
            for meal_time, food_info in daily_foods.items():
                # Create consumption record
                consumption_data = {
                    "food_name": food_info["name"],
                    "nutritional_info": {
                        "calories": food_info["calories"],
                        "protein": food_info["protein"], 
                        "carbohydrates": food_info["carbs"],
                        "fat": food_info["fat"],
                        "fiber": food_info["fiber"],
                        "sugar": food_info["sugar"],
                        "sodium": random.randint(200, 800)
                    },
                    "medical_rating": generate_medical_rating(food_info),
                    "meal_type": meal_time,
                    "consumption_time": (date + timedelta(hours=get_meal_hour(meal_time))).isoformat()
                }
                
                # Log the food
                response = requests.post(f"{BACKEND_URL}/consumption/log", 
                                       json=consumption_data, headers=headers)
                
                if response.status_code == 200:
                    print(f"✅ Logged {food_info['name']} for {email} on {date.strftime('%Y-%m-%d')}")
                else:
                    print(f"❌ Failed to log food for {email}: {response.text}")
                    
                time.sleep(0.1)  # Small delay to avoid overwhelming the server
                
        return True
        
    except Exception as e:
        print(f"❌ Error generating consumption data for {email}: {str(e)}")
        return False

def select_daily_foods(profile_type):
    """Select appropriate foods for a day based on profile type"""
    # Different eating patterns based on profile type
    patterns = {
        "well_controlled": {"excellent": 0.6, "good": 0.3, "moderate": 0.1, "poor": 0.0},
        "needs_improvement": {"excellent": 0.3, "good": 0.4, "moderate": 0.2, "poor": 0.1},
        "strict_diet": {"excellent": 0.7, "good": 0.3, "moderate": 0.0, "poor": 0.0},
        "multiple_conditions": {"excellent": 0.5, "good": 0.4, "moderate": 0.1, "poor": 0.0},
        "pregnancy": {"excellent": 0.6, "good": 0.35, "moderate": 0.05, "poor": 0.0}
    }
    
    pattern = patterns.get(profile_type, patterns["well_controlled"])
    
    meals = {}
    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        # Select food category based on pattern probabilities
        rand = random.random()
        cumulative = 0
        selected_category = "good"
        
        for category, prob in pattern.items():
            cumulative += prob
            if rand <= cumulative:
                selected_category = category
                break
                
        # Select random food from category
        meals[meal] = random.choice(FOODS_DATABASE[selected_category])
        
    return meals

def get_meal_hour(meal_type):
    """Get typical hour for meal type"""
    hours = {
        "breakfast": random.randint(7, 9),
        "lunch": random.randint(12, 14), 
        "dinner": random.randint(18, 20),
        "snack": random.randint(15, 16)
    }
    return hours.get(meal_type, 12)

def generate_medical_rating(food_info):
    """Generate medical rating based on nutritional content"""
    # Simple algorithm to rate foods for diabetes
    score = 85
    
    # Penalize high sugar
    if food_info["sugar"] > 20:
        score -= 20
    elif food_info["sugar"] > 15:
        score -= 10
        
    # Reward fiber
    if food_info["fiber"] > 8:
        score += 10
    elif food_info["fiber"] > 5:
        score += 5
        
    # Penalize high calories without protein
    if food_info["calories"] > 400 and food_info["protein"] < 15:
        score -= 15
        
    score = max(40, min(95, score))  # Keep between 40-95
    
    # Convert score to suitability ratings
    if score >= 80:
        suitability = "excellent"
    elif score >= 70:
        suitability = "high" 
    elif score >= 60:
        suitability = "good"
    else:
        suitability = "moderate"
        
    return {
        "diabetes_suitability": suitability,
        "hypertension_suitability": suitability,
        "heart_disease_suitability": suitability, 
        "cholesterol_suitability": suitability,
        "overall_health_score": score
    }

def generate_meal_plans_for_users():
    """Generate meal plans for all demo users"""
    print("\n🍽️ Generating meal plans for demo users...")
    
    for user in DEMO_USERS:
        try:
            # Login
            login_response = requests.post(f"{BACKEND_URL}/auth/login", data={
                "username": user["email"],
                "password": user["password"]
            })
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Generate meal plan
                meal_plan_response = requests.post(f"{BACKEND_URL}/generate-meal-plan", 
                                                 json={}, headers=headers)
                
                if meal_plan_response.status_code == 200:
                    print(f"✅ Generated meal plan for {user['name']}")
                else:
                    print(f"❌ Failed to generate meal plan for {user['name']}")
                    
        except Exception as e:
            print(f"❌ Error generating meal plan for {user['name']}: {str(e)}")

def main():
    """Main demo data generation function"""
    print("🚀 Starting Comprehensive Demo Data Generation...")
    print("=" * 60)
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend server...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/docs")
            if response.status_code == 200:
                print("✅ Backend server is ready!")
                break
        except:
            pass
        time.sleep(2)
        print(f"   Waiting... ({i+1}/{max_retries})")
    else:
        print("❌ Backend server not responding. Please start it first!")
        return
    
    print("\n👥 Creating demo users...")
    successful_users = []
    
    for user in DEMO_USERS:
        if create_demo_user(user):
            successful_users.append(user)
            time.sleep(1)  # Small delay between user creation
    
    print(f"\n📊 Generating consumption data for {len(successful_users)} users...")
    
    for user in successful_users:
        print(f"\n   Generating data for {user['name']}...")
        if generate_consumption_data(user["email"], user["password"], user["profile_type"]):
            print(f"   ✅ Completed data generation for {user['name']}")
        time.sleep(2)  # Delay between users
    
    # Generate meal plans
    generate_meal_plans_for_users()
    
    print("\n" + "=" * 60)
    print("🎉 Demo Data Generation Complete!")
    print("\n📋 Demo User Accounts Created:")
    print("-" * 40)
    
    for user in successful_users:
        print(f"Name: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Password: {user['password']}")
        print(f"Type: {user['diabetes_type']} - {user['profile_type']}")
        print("-" * 40)
    
    print("\n🎯 Ready for Demo! Your analytics dashboard should now show:")
    print("   ✅ Multiple patients with consumption data")
    print("   ✅ Behavior clustering analysis")
    print("   ✅ Nutrient adequacy metrics")
    print("   ✅ Engagement patterns")
    print("   ✅ Compliance analysis")
    print("\n🌐 Login at: http://localhost:3000")

if __name__ == "__main__":
    main() 