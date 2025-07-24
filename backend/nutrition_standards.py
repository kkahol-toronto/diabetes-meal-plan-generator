"""
Nutritional Standards Database
Contains RDA (Recommended Daily Allowance) values by age, gender, and medical conditions
Includes diabetes-specific adjustments for optimal blood glucose management
"""

from typing import Dict, Any, List
from datetime import datetime

# Comprehensive RDA Standards based on USDA/NIH guidelines
RDA_STANDARDS = {
    "adults_male": {
        "calories": {"18-30": 2400, "31-50": 2200, "51-70": 2000, "70+": 1800},
        "protein": {"18-30": 56, "31-50": 56, "51-70": 56, "70+": 56},  # grams
        "carbohydrates": {"18-30": 300, "31-50": 300, "51-70": 300, "70+": 300},  # grams
        "fat": {"18-30": 80, "31-50": 73, "51-70": 67, "70+": 60},  # grams
        "fiber": {"18-30": 38, "31-50": 38, "51-70": 30, "70+": 30},  # grams
        "sodium": {"18-30": 2300, "31-50": 2300, "51-70": 2300, "70+": 2300},  # mg - MAX
        "sugar": {"18-30": 50, "31-50": 50, "51-70": 50, "70+": 50},  # grams - MAX
        "saturated_fat": {"18-30": 22, "31-50": 20, "51-70": 18, "70+": 16},  # grams - MAX
        "cholesterol": {"18-30": 300, "31-50": 300, "51-70": 300, "70+": 300},  # mg - MAX
        
        # Micronutrients
        "vitamin_d": {"18-30": 600, "31-50": 600, "51-70": 800, "70+": 800},  # IU
        "vitamin_c": {"18-30": 90, "31-50": 90, "51-70": 90, "70+": 90},  # mg
        "calcium": {"18-30": 1000, "31-50": 1000, "51-70": 1200, "70+": 1200},  # mg
        "iron": {"18-30": 8, "31-50": 8, "51-70": 8, "70+": 8},  # mg
        "potassium": {"18-30": 3500, "31-50": 3500, "51-70": 3500, "70+": 3500},  # mg
        "magnesium": {"18-30": 400, "31-50": 420, "51-70": 420, "70+": 420},  # mg
        "zinc": {"18-30": 11, "31-50": 11, "51-70": 11, "70+": 11},  # mg
        "omega_3": {"18-30": 1.6, "31-50": 1.6, "51-70": 1.6, "70+": 1.6},  # grams
    },
    "adults_female": {
        "calories": {"18-30": 2000, "31-50": 1800, "51-70": 1600, "70+": 1600},
        "protein": {"18-30": 46, "31-50": 46, "51-70": 46, "70+": 46},
        "carbohydrates": {"18-30": 225, "31-50": 225, "51-70": 225, "70+": 225},
        "fat": {"18-30": 67, "31-50": 60, "51-70": 53, "70+": 53},
        "fiber": {"18-30": 25, "31-50": 25, "51-70": 21, "70+": 21},
        "sodium": {"18-30": 2300, "31-50": 2300, "51-70": 2300, "70+": 2300},
        "sugar": {"18-30": 40, "31-50": 40, "51-70": 40, "70+": 40},
        "saturated_fat": {"18-30": 18, "31-50": 16, "51-70": 14, "70+": 12},
        "cholesterol": {"18-30": 300, "31-50": 300, "51-70": 300, "70+": 300},
        
        # Micronutrients
        "vitamin_d": {"18-30": 600, "31-50": 600, "51-70": 800, "70+": 800},
        "vitamin_c": {"18-30": 75, "31-50": 75, "51-70": 75, "70+": 75},
        "calcium": {"18-30": 1000, "31-50": 1000, "51-70": 1200, "70+": 1200},
        "iron": {"18-30": 18, "31-50": 18, "51-70": 8, "70+": 8},
        "potassium": {"18-30": 2600, "31-50": 2600, "51-70": 2600, "70+": 2600},
        "magnesium": {"18-30": 310, "31-50": 320, "51-70": 320, "70+": 320},
        "zinc": {"18-30": 8, "31-50": 8, "51-70": 8, "70+": 8},
        "omega_3": {"18-30": 1.1, "31-50": 1.1, "51-70": 1.1, "70+": 1.1},
    },
    
    # Diabetes-specific adjustments
    "diabetes_adjustments": {
        "carbohydrates_max_percent": 0.45,  # Max 45% of calories from carbs
        "fiber_minimum": 25,  # Minimum fiber regardless of age/gender
        "sodium_max": 1500,  # Stricter sodium limit for diabetes (mg)
        "sugar_max": 25,  # Much stricter sugar limit (grams)
        "protein_min_percent": 0.15,  # Minimum 15% of calories from protein
        "fat_max_percent": 0.35,  # Maximum 35% of calories from fat
        "saturated_fat_max_percent": 0.07,  # Max 7% of calories from saturated fat
        "omega_3_min": 2.0,  # Higher omega-3 requirement for inflammation
    },
    
    # Pre-diabetes adjustments (less strict than diabetes)
    "prediabetes_adjustments": {
        "carbohydrates_max_percent": 0.50,
        "fiber_minimum": 20,
        "sodium_max": 2000,
        "sugar_max": 35,
        "protein_min_percent": 0.12,
        "fat_max_percent": 0.35,
        "saturated_fat_max_percent": 0.10,
        "omega_3_min": 1.5,
    }
}

def get_age_group(age: int) -> str:
    """Determine age group category for RDA lookup"""
    if age < 31:
        return "18-30"
    elif age < 51:
        return "31-50"
    elif age < 71:
        return "51-70"
    else:
        return "70+"

def get_rda_for_patient(age: int, gender: str, condition: str, activity_level: str = "moderate") -> Dict[str, float]:
    """
    Calculate comprehensive RDA values for a specific patient
    
    Args:
        age: Patient age
        gender: 'male' or 'female'
        condition: Medical condition (e.g., 'Type 1 Diabetes', 'Type 2 Diabetes', 'Pre-diabetes')
        activity_level: 'sedentary', 'moderate', 'active' (affects calorie needs)
    
    Returns:
        Dictionary of nutrient RDA values
    """
    age_group = get_age_group(age)
    gender_key = f"adults_{gender.lower()}"
    
    if gender_key not in RDA_STANDARDS:
        gender_key = "adults_female"  # Default fallback
    
    base_rda = RDA_STANDARDS[gender_key]
    
    # Start with base RDA values
    rda = {}
    for nutrient, age_values in base_rda.items():
        rda[nutrient] = age_values[age_group]
    
    # Adjust calories based on activity level
    activity_multipliers = {
        "sedentary": 0.9,
        "moderate": 1.0,
        "active": 1.2,
        "very_active": 1.4
    }
    if activity_level in activity_multipliers:
        rda["calories"] *= activity_multipliers[activity_level]
    
    # Apply condition-specific adjustments
    condition_lower = condition.lower()
    
    if "diabetes" in condition_lower:
        adjustments = RDA_STANDARDS["diabetes_adjustments"]
        
        # Carbohydrate limits based on calories
        max_carbs_from_calories = (rda["calories"] * adjustments["carbohydrates_max_percent"]) / 4
        rda["carbohydrates"] = min(rda["carbohydrates"], max_carbs_from_calories)
        
        # Minimum fiber
        rda["fiber"] = max(rda["fiber"], adjustments["fiber_minimum"])
        
        # Stricter limits
        rda["sodium"] = adjustments["sodium_max"]
        rda["sugar"] = adjustments["sugar_max"]
        
        # Protein minimum
        min_protein_from_calories = (rda["calories"] * adjustments["protein_min_percent"]) / 4
        rda["protein"] = max(rda["protein"], min_protein_from_calories)
        
        # Fat limits
        max_fat_from_calories = (rda["calories"] * adjustments["fat_max_percent"]) / 9
        rda["fat"] = min(rda["fat"], max_fat_from_calories)
        
        # Saturated fat limit
        max_sat_fat_from_calories = (rda["calories"] * adjustments["saturated_fat_max_percent"]) / 9
        rda["saturated_fat"] = min(rda["saturated_fat"], max_sat_fat_from_calories)
        
        # Higher omega-3 for anti-inflammatory benefits
        rda["omega_3"] = max(rda["omega_3"], adjustments["omega_3_min"])
        
    elif "pre-diabetes" in condition_lower or "prediabetes" in condition_lower:
        adjustments = RDA_STANDARDS["prediabetes_adjustments"]
        
        # Apply milder adjustments for pre-diabetes
        max_carbs_from_calories = (rda["calories"] * adjustments["carbohydrates_max_percent"]) / 4
        rda["carbohydrates"] = min(rda["carbohydrates"], max_carbs_from_calories)
        
        rda["fiber"] = max(rda["fiber"], adjustments["fiber_minimum"])
        rda["sodium"] = adjustments["sodium_max"]
        rda["sugar"] = adjustments["sugar_max"]
        
        min_protein_from_calories = (rda["calories"] * adjustments["protein_min_percent"]) / 4
        rda["protein"] = max(rda["protein"], min_protein_from_calories)
        
        max_fat_from_calories = (rda["calories"] * adjustments["fat_max_percent"]) / 9
        rda["fat"] = min(rda["fat"], max_fat_from_calories)
        
        max_sat_fat_from_calories = (rda["calories"] * adjustments["saturated_fat_max_percent"]) / 9
        rda["saturated_fat"] = min(rda["saturated_fat"], max_sat_fat_from_calories)
        
        rda["omega_3"] = max(rda["omega_3"], adjustments["omega_3_min"])
    
    return rda

def calculate_nutrient_compliance(actual_intake: Dict[str, float], rda_targets: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate compliance percentages and identify deficiencies/excesses
    
    Args:
        actual_intake: Dictionary of actual nutrient intake values
        rda_targets: Dictionary of RDA target values
    
    Returns:
        Dictionary with compliance data for each nutrient
    """
    compliance_data = {}
    
    # Nutrients where higher is better
    higher_is_better = [
        "protein", "fiber", "vitamin_d", "vitamin_c", "calcium", 
        "iron", "potassium", "magnesium", "zinc", "omega_3"
    ]
    
    # Nutrients where lower is better (limits)
    lower_is_better = [
        "sodium", "sugar", "saturated_fat", "cholesterol"
    ]
    
    # Nutrients with optimal ranges
    optimal_range = ["calories", "carbohydrates", "fat"]
    
    for nutrient in rda_targets:
        if nutrient not in actual_intake:
            continue
            
        actual = actual_intake[nutrient]
        target = rda_targets[nutrient]
        
        compliance_info = {
            "actual": actual,
            "target": target,
            "compliance_percentage": 0,
            "status": "unknown",
            "severity": "none",
            "recommendation": ""
        }
        
        if nutrient in higher_is_better:
            # Higher values are better (minimum requirements)
            compliance_pct = min(100, (actual / target) * 100) if target > 0 else 0
            compliance_info["compliance_percentage"] = compliance_pct
            
            if compliance_pct >= 80:
                compliance_info["status"] = "adequate"
                compliance_info["severity"] = "none"
            elif compliance_pct >= 60:
                compliance_info["status"] = "below_target"
                compliance_info["severity"] = "mild"
                compliance_info["recommendation"] = f"Increase {nutrient} intake by {target - actual:.1f}g"
            else:
                compliance_info["status"] = "deficient"
                compliance_info["severity"] = "moderate" if compliance_pct >= 40 else "severe"
                compliance_info["recommendation"] = f"Significantly increase {nutrient} intake"
                
        elif nutrient in lower_is_better:
            # Lower values are better (maximum limits)
            if actual <= target:
                compliance_pct = 100
                compliance_info["status"] = "within_limit"
            else:
                excess_ratio = actual / target
                compliance_pct = max(0, 100 - ((excess_ratio - 1) * 100))
                if excess_ratio <= 1.2:
                    compliance_info["status"] = "slightly_elevated"
                    compliance_info["severity"] = "mild"
                elif excess_ratio <= 1.5:
                    compliance_info["status"] = "elevated"
                    compliance_info["severity"] = "moderate"
                else:
                    compliance_info["status"] = "excessive"
                    compliance_info["severity"] = "severe"
                compliance_info["recommendation"] = f"Reduce {nutrient} intake by {actual - target:.1f}"
                
            compliance_info["compliance_percentage"] = compliance_pct
            
        elif nutrient in optimal_range:
            # Optimal range (target ±20%)
            lower_bound = target * 0.8
            upper_bound = target * 1.2
            
            if lower_bound <= actual <= upper_bound:
                compliance_info["compliance_percentage"] = 100
                compliance_info["status"] = "optimal"
            elif actual < lower_bound:
                compliance_pct = (actual / lower_bound) * 100
                compliance_info["compliance_percentage"] = compliance_pct
                compliance_info["status"] = "below_optimal"
                compliance_info["severity"] = "mild" if compliance_pct >= 60 else "moderate"
                compliance_info["recommendation"] = f"Increase {nutrient} intake"
            else:  # actual > upper_bound
                excess_ratio = actual / upper_bound
                compliance_pct = max(0, 100 - ((excess_ratio - 1) * 50))
                compliance_info["compliance_percentage"] = compliance_pct
                compliance_info["status"] = "above_optimal"
                compliance_info["severity"] = "mild" if excess_ratio <= 1.5 else "moderate"
                compliance_info["recommendation"] = f"Reduce {nutrient} intake"
        
        compliance_data[nutrient] = compliance_info
    
    return compliance_data

def get_nutrient_recommendations(compliance_data: Dict[str, Dict[str, Any]], condition: str) -> List[Dict[str, str]]:
    """
    Generate personalized nutrition recommendations based on compliance analysis
    
    Args:
        compliance_data: Output from calculate_nutrient_compliance
        condition: Patient's medical condition
    
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Identify critical deficiencies
    critical_deficiencies = [
        nutrient for nutrient, data in compliance_data.items()
        if data["severity"] in ["moderate", "severe"] and data["status"] in ["deficient", "below_target"]
    ]
    
    # Identify critical excesses
    critical_excesses = [
        nutrient for nutrient, data in compliance_data.items()
        if data["severity"] in ["moderate", "severe"] and data["status"] in ["elevated", "excessive"]
    ]
    
    # Generate specific recommendations
    if "fiber" in critical_deficiencies:
        recommendations.append({
            "priority": "high",
            "category": "deficiency",
            "nutrient": "fiber",
            "recommendation": "Increase fiber intake with whole grains, legumes, vegetables, and fruits",
            "rationale": "Essential for blood sugar control and digestive health"
        })
    
    if "protein" in critical_deficiencies:
        recommendations.append({
            "priority": "high",
            "category": "deficiency", 
            "nutrient": "protein",
            "recommendation": "Include lean protein sources: fish, poultry, legumes, tofu",
            "rationale": "Protein helps stabilize blood sugar and maintain muscle mass"
        })
    
    if "sodium" in critical_excesses:
        recommendations.append({
            "priority": "high",
            "category": "excess",
            "nutrient": "sodium", 
            "recommendation": "Reduce processed foods, restaurant meals, and added salt",
            "rationale": "High sodium increases blood pressure and cardiovascular risk"
        })
    
    if "sugar" in critical_excesses:
        recommendations.append({
            "priority": "high",
            "category": "excess",
            "nutrient": "sugar",
            "recommendation": "Limit sugary drinks, desserts, and processed foods",
            "rationale": "Excess sugar causes blood glucose spikes"
        })
    
    # Condition-specific recommendations
    if "diabetes" in condition.lower():
        recommendations.append({
            "priority": "medium",
            "category": "general",
            "nutrient": "carbohydrates",
            "recommendation": "Focus on complex carbohydrates with low glycemic index",
            "rationale": "Helps maintain stable blood glucose levels"
        })
        
        if compliance_data.get("omega_3", {}).get("status") in ["deficient", "below_target"]:
            recommendations.append({
                "priority": "medium",
                "category": "deficiency",
                "nutrient": "omega_3",
                "recommendation": "Include fatty fish (salmon, sardines) 2-3 times per week",
                "rationale": "Omega-3 fatty acids reduce inflammation and support heart health"
            })
    
    return recommendations

# Nutrient mapping for common food database fields
NUTRIENT_FIELD_MAPPING = {
    "calories": ["calories", "energy", "kcal"],
    "protein": ["protein"],
    "carbohydrates": ["carbohydrates", "carbs", "total_carbohydrate"],
    "fat": ["fat", "total_fat"],
    "fiber": ["fiber", "dietary_fiber"],
    "sodium": ["sodium"],
    "sugar": ["sugar", "total_sugars", "added_sugars"],
    "saturated_fat": ["saturated_fat", "saturated_fatty_acids"],
    "cholesterol": ["cholesterol"],
    "vitamin_d": ["vitamin_d"],
    "vitamin_c": ["vitamin_c"],
    "calcium": ["calcium"],
    "iron": ["iron"],
    "potassium": ["potassium"],
    "magnesium": ["magnesium"],
    "zinc": ["zinc"],
    "omega_3": ["omega_3", "omega3", "ala", "epa", "dha"]
}

def extract_nutrients_from_food_data(food_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract standardized nutrient values from various food database formats
    
    Args:
        food_data: Dictionary containing nutritional information
    
    Returns:
        Dictionary with standardized nutrient names and values
    """
    extracted_nutrients = {}
    
    for standard_name, possible_fields in NUTRIENT_FIELD_MAPPING.items():
        value = 0.0
        
        for field_name in possible_fields:
            # Check various possible field names (case insensitive)
            for key in food_data.keys():
                if key.lower().replace('_', '').replace('-', '') == field_name.lower().replace('_', '').replace('-', ''):
                    try:
                        value = float(food_data[key])
                        break
                    except (ValueError, TypeError):
                        continue
            if value > 0:
                break
        
        extracted_nutrients[standard_name] = value
    
    return extracted_nutrients 