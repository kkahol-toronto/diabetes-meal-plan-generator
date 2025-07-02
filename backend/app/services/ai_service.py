from typing import Dict
import re
from datetime import datetime

async def get_ai_suggestion(prompt: str) -> Dict:
    """
    Generate AI-powered diabetes management suggestions based on the given prompt.
    Provides professional, comprehensive responses for diabetes care.
    """
    
    # Analyze the prompt to understand the context
    context = analyze_prompt_context(prompt)
    
    # Generate professional diabetes-focused response
    if "dinner" in prompt.lower() or "evening" in prompt.lower():
        return generate_dinner_recommendation(context)
    elif "breakfast" in prompt.lower() or "morning" in prompt.lower():
        return generate_breakfast_recommendation(context)
    elif "lunch" in prompt.lower() or "afternoon" in prompt.lower():
        return generate_lunch_recommendation(context)
    elif "snack" in prompt.lower():
        return generate_snack_recommendation(context)
    elif "diabetes management" in prompt.lower() or "blood sugar" in prompt.lower():
        return generate_diabetes_management_advice(context)
    else:
        return generate_general_nutrition_advice(context)

def analyze_prompt_context(prompt: str) -> Dict:
    """
    Analyze the user's prompt to extract context for personalized recommendations.
    """
    context = {
        "meal_type": "general",
        "time_sensitive": False,
        "health_focus": False,
        "urgency": "normal"
    }
    
    # Detect meal type
    if any(word in prompt.lower() for word in ["dinner", "evening", "night"]):
        context["meal_type"] = "dinner"
        context["time_sensitive"] = True
    elif any(word in prompt.lower() for word in ["breakfast", "morning"]):
        context["meal_type"] = "breakfast"
    elif any(word in prompt.lower() for word in ["lunch", "afternoon"]):
        context["meal_type"] = "lunch"
    elif "snack" in prompt.lower():
        context["meal_type"] = "snack"
    
    # Detect health focus
    if any(word in prompt.lower() for word in ["diabetes", "blood sugar", "glucose", "manage", "control"]):
        context["health_focus"] = True
    
    return context

def generate_dinner_recommendation(context: Dict) -> Dict:
    """
    Generate professional dinner recommendations for diabetes management.
    """
    return {
        "suggestion": """For optimal diabetes management this evening, I recommend a well-balanced dinner that prioritizes blood glucose stability:

**Primary Recommendation:** Herb-Crusted Salmon with Roasted Vegetables and Quinoa

**Clinical Rationale:**
• Omega-3 fatty acids from salmon support cardiovascular health and reduce inflammation
• Complex carbohydrates from quinoa provide sustained energy without glucose spikes
• High fiber content aids in glucose absorption regulation
• Lean protein supports muscle maintenance and satiety

**Portion Guidelines:**
• 4-6 oz salmon fillet (palm-sized portion)
• ½ cup cooked quinoa
• 2 cups mixed non-starchy vegetables (broccoli, bell peppers, zucchini)
• 1 tsp olive oil for cooking

**Post-Meal Strategy:**
Consider a 10-15 minute walk after eating to enhance glucose uptake and improve insulin sensitivity.""",
        
        "ingredients": [
            "4-6 oz salmon fillet",
            "½ cup quinoa (dry)",
            "1 cup broccoli florets", 
            "½ cup bell peppers",
            "½ cup zucchini",
            "1 tsp extra virgin olive oil",
            "Fresh herbs (dill, parsley)",
            "Lemon juice",
            "Garlic (1 clove)"
        ],
        
        "preparation": """**Professional Preparation Method:**
1. Preheat oven to 400°F (200°C)
2. Season salmon with herbs, lemon, and minimal salt
3. Roast vegetables with light olive oil coating for 20-25 minutes
4. Cook quinoa according to package instructions (1:2 ratio with low-sodium broth)
5. Bake salmon for 12-15 minutes until flaky
6. Serve immediately while warm for optimal nutrient retention""",
        
        "nutritional_info": {
            "calories": 485,
            "protein": "42g",
            "carbs": "35g",
            "fat": "18g",
            "fiber": "8g",
            "sodium": "320mg",
            "glycemic_load": "Low (12)"
        },
        
        "health_benefits": """**Diabetes Management Benefits:**
• **Glycemic Control:** Low glycemic index prevents blood sugar spikes
• **Cardiovascular Support:** Omega-3s reduce inflammation and support heart health
• **Weight Management:** High protein and fiber promote satiety and prevent overeating
• **Nutrient Density:** Provides essential vitamins, minerals, and antioxidants
• **Metabolic Support:** Balanced macronutrients optimize insulin response

**Professional Monitoring Advice:**
Monitor blood glucose 2 hours post-meal to assess individual response and adjust portions as needed.""",

        "diabetes_tips": [
            "Test blood glucose before and 2 hours after eating to track response",
            "Eat slowly and mindfully to improve satiety signals",
            "Stay hydrated with water throughout the meal",
            "Consider timing - aim to finish dinner 3 hours before bedtime"
        ]
    }

def generate_breakfast_recommendation(context: Dict) -> Dict:
    """
    Generate professional breakfast recommendations for diabetes management.
    """
    return {
        "suggestion": """For optimal morning glucose control and sustained energy, I recommend a diabetes-friendly breakfast that balances macronutrients:

**Primary Recommendation:** Greek Yogurt Parfait with Berries and Nuts

**Clinical Benefits:**
• High-quality protein supports muscle maintenance and glucose stability
• Probiotics promote gut health and may improve insulin sensitivity
• Antioxidants from berries combat oxidative stress
• Healthy fats from nuts slow carbohydrate absorption

**Composition:**
• ¾ cup plain Greek yogurt (low-fat, unsweetened)
• ½ cup mixed berries (blueberries, strawberries)
• 1 oz mixed nuts (almonds, walnuts)
• 1 tsp ground flaxseed
• Cinnamon for natural sweetness

**Morning Diabetes Management:**
Start your day with this balanced meal to establish stable glucose patterns and prevent mid-morning energy crashes.""",
        
        "ingredients": [
            "¾ cup plain Greek yogurt (unsweetened)",
            "½ cup fresh mixed berries",
            "1 oz mixed nuts (almonds, walnuts)",
            "1 tsp ground flaxseed",
            "¼ tsp cinnamon",
            "Optional: 1 tsp natural vanilla extract"
        ],
        
        "preparation": """**Assembly Instructions:**
1. Layer Greek yogurt in a bowl or glass
2. Add half the berries, then sprinkle nuts
3. Add remaining berries and flaxseed
4. Dust with cinnamon for natural sweetness
5. Serve immediately to maintain texture and freshness""",
        
        "nutritional_info": {
            "calories": 320,
            "protein": "22g",
            "carbs": "18g", 
            "fat": "15g",
            "fiber": "6g",
            "sodium": "85mg",
            "glycemic_load": "Low (8)"
        },
        
        "health_benefits": """**Morning Metabolic Advantages:**
• **Stable Glucose:** Protein and fat slow carbohydrate absorption
• **Sustained Energy:** Prevents mid-morning glucose crashes
• **Digestive Health:** Probiotics support gut microbiome balance
• **Heart Health:** Omega-3s and antioxidants support cardiovascular function
• **Weight Management:** High protein promotes satiety until lunch

**Professional Timing Advice:**
Consume within 1-2 hours of waking to establish healthy circadian glucose rhythms.""",

        "diabetes_tips": [
            "Check fasting glucose before breakfast for baseline",
            "Eat breakfast consistently at the same time daily",
            "Pair with a glass of water to support hydration",
            "Monitor energy levels throughout the morning"
        ]
    }

def generate_lunch_recommendation(context: Dict) -> Dict:
    """
    Generate professional lunch recommendations for diabetes management.
    """
    return {
        "suggestion": """For midday glucose optimization and afternoon energy stability, I recommend a nutrient-dense lunch that prevents post-meal spikes:

**Primary Recommendation:** Mediterranean Chickpea Salad with Grilled Chicken

**Clinical Rationale:**
• Plant-based protein and fiber from chickpeas support glucose regulation
• Lean protein maintains muscle mass and provides satiety
• Mediterranean diet pattern reduces diabetes complications
• Anti-inflammatory ingredients support overall metabolic health

**Balanced Composition:**
• 3 oz grilled chicken breast (seasoned with herbs)
• ½ cup chickpeas (rinsed and drained)
• 2 cups mixed greens and vegetables
• 2 tbsp olive oil-based dressing
• ¼ avocado for healthy monounsaturated fats

**Afternoon Strategy:**
This meal provides sustained energy without causing afternoon fatigue or glucose fluctuations.""",
        
        "ingredients": [
            "3 oz grilled chicken breast",
            "½ cup canned chickpeas (low-sodium)",
            "2 cups mixed salad greens",
            "½ cucumber, diced",
            "1 medium tomato, chopped",
            "¼ red onion, thinly sliced",
            "¼ avocado, sliced",
            "2 tbsp olive oil",
            "1 tbsp lemon juice",
            "Fresh herbs (oregano, basil)"
        ],
        
        "preparation": """**Professional Assembly:**
1. Season and grill chicken breast until internal temperature reaches 165°F
2. Rinse chickpeas and pat dry
3. Combine all vegetables in a large bowl
4. Whisk olive oil, lemon juice, and herbs for dressing
5. Top salad with sliced chicken and chickpeas
6. Drizzle with dressing just before serving""",
        
        "nutritional_info": {
            "calories": 420,
            "protein": "32g",
            "carbs": "25g",
            "fat": "22g",
            "fiber": "9g",
            "sodium": "180mg",
            "glycemic_load": "Low (10)"
        },
        
        "health_benefits": """**Midday Metabolic Benefits:**
• **Glucose Stability:** High fiber and protein prevent afternoon spikes
• **Sustained Energy:** Complex carbohydrates provide steady fuel
• **Inflammation Reduction:** Mediterranean ingredients combat oxidative stress
• **Digestive Health:** Fiber supports beneficial gut bacteria
• **Cardiovascular Protection:** Omega-3s and antioxidants support heart health

**Professional Hydration Note:**
Pair with water or unsweetened tea to support optimal digestion and glucose metabolism.""",

        "diabetes_tips": [
            "Eat lunch at consistent times to maintain glucose patterns",
            "Include a brief walk after eating if schedule permits",
            "Monitor portion sizes using the plate method",
            "Stay hydrated throughout the afternoon"
        ]
    }

def generate_snack_recommendation(context: Dict) -> Dict:
    """
    Generate professional snack recommendations for diabetes management.
    """
    return {
        "suggestion": """For optimal between-meal glucose management, I recommend balanced snacks that provide sustained energy without causing spikes:

**Primary Recommendation:** Apple Slices with Almond Butter

**Clinical Benefits:**
• Fiber from apple slows glucose absorption
• Healthy fats and protein from almond butter provide satiety
• Natural sweetness satisfies cravings without added sugars
• Portable and convenient for busy schedules

**Portion Control:**
• 1 medium apple, sliced
• 1 tablespoon natural almond butter (unsweetened)
• Optional: sprinkle of cinnamon for additional flavor

**Timing Strategy:**
Ideal for mid-morning or mid-afternoon when blood glucose may naturally dip between main meals.""",
        
        "ingredients": [
            "1 medium apple (with skin)",
            "1 tbsp natural almond butter",
            "Pinch of cinnamon (optional)",
            "Water for hydration"
        ],
        
        "preparation": """**Simple Assembly:**
1. Wash apple thoroughly and slice into wedges
2. Measure almond butter portion carefully
3. Arrange apple slices with almond butter for dipping
4. Sprinkle with cinnamon if desired
5. Consume mindfully and slowly""",
        
        "nutritional_info": {
            "calories": 180,
            "protein": "4g",
            "carbs": "20g",
            "fat": "8g",
            "fiber": "5g",
            "sodium": "2mg",
            "glycemic_load": "Low (6)"
        },
        
        "health_benefits": """**Strategic Snacking Benefits:**
• **Glucose Moderation:** Prevents between-meal blood sugar drops
• **Appetite Control:** Reduces likelihood of overeating at next meal
• **Nutrient Density:** Provides essential vitamins and minerals
• **Energy Stability:** Maintains consistent energy levels
• **Convenience:** Easy to prepare and transport

**Professional Portion Note:**
Use measuring tools to ensure appropriate portions and consistent carbohydrate intake.""",

        "diabetes_tips": [
            "Time snacks 2-3 hours after meals",
            "Monitor blood glucose response to adjust portions",
            "Keep emergency snacks available for low glucose episodes",
            "Focus on whole foods rather than processed options"
        ]
    }

def generate_diabetes_management_advice(context: Dict) -> Dict:
    """
    Generate comprehensive diabetes management advice.
    """
    return {
        "suggestion": """**Comprehensive Diabetes Management Strategy**

Effective diabetes management requires a multifaceted approach focusing on nutrition, physical activity, monitoring, and lifestyle modifications:

**Nutritional Foundations:**
• Follow the plate method: ½ non-starchy vegetables, ¼ lean protein, ¼ complex carbohydrates
• Maintain consistent meal timing to stabilize glucose patterns
• Choose low glycemic index foods to minimize blood sugar spikes
• Stay hydrated with water as your primary beverage

**Monitoring Excellence:**
• Check blood glucose as recommended by your healthcare team
• Keep a food and glucose log to identify patterns
• Track symptoms and energy levels
• Regular A1C testing every 3-6 months

**Physical Activity Integration:**
• Aim for 150 minutes of moderate activity weekly
• Include resistance training 2-3 times per week
• Consider post-meal walks to improve glucose uptake
• Monitor blood sugar before and after exercise

**Professional Collaboration:**
Work closely with your diabetes care team including endocrinologist, certified diabetes educator, and registered dietitian for personalized care.""",
        
        "ingredients": ["Professional healthcare team guidance", "Blood glucose monitoring supplies", "Healthy whole foods", "Exercise equipment"],
        
        "preparation": """**Implementation Strategy:**
1. Schedule regular healthcare appointments
2. Establish consistent daily routines
3. Prepare healthy meals in advance
4. Set up monitoring systems and reminders
5. Create support networks with family and friends""",
        
        "nutritional_info": {
            "target_a1c": "<7%",
            "daily_carbs": "45-60g per meal",
            "protein": "0.8-1g per kg body weight",
            "fiber": "25-35g daily",
            "sodium": "<2300mg daily",
            "monitoring": "As prescribed by healthcare provider"
        },
        
        "health_benefits": """**Long-term Health Outcomes:**
• **Glucose Control:** Reduced risk of diabetes complications
• **Cardiovascular Health:** Lower risk of heart disease and stroke
• **Weight Management:** Sustainable healthy weight maintenance
• **Energy Optimization:** Improved daily energy and mood stability
• **Quality of Life:** Enhanced overall well-being and independence

**Evidence-Based Results:**
Comprehensive diabetes management can reduce the risk of complications by up to 60% when following evidence-based protocols.""",

        "diabetes_tips": [
            "Never adjust medications without healthcare provider consultation",
            "Carry glucose tablets for emergency low blood sugar episodes",
            "Wear medical identification jewelry",
            "Stay current with diabetes education and research"
        ]
    }

def generate_general_nutrition_advice(context: Dict) -> Dict:
    """
    Generate general nutrition advice with diabetes considerations.
    """
    return {
        "suggestion": """**Professional Nutrition Guidance for Diabetes Wellness**

Based on your inquiry, I recommend focusing on evidence-based nutrition principles that support optimal glucose management and overall health:

**Core Principles:**
• Emphasize nutrient-dense, whole foods over processed alternatives
• Balance macronutrients at each meal to optimize glucose response
• Prioritize consistent meal timing for metabolic stability
• Choose foods with low to moderate glycemic impact

**Practical Implementation:**
• Fill half your plate with non-starchy vegetables
• Include lean protein sources at every meal
• Select complex carbohydrates with fiber
• Incorporate healthy fats in appropriate portions

**Quality Focus:**
Choose fresh, minimally processed ingredients whenever possible to maximize nutrient density and minimize added sugars, sodium, and unhealthy fats.""",
        
        "ingredients": [
            "Variety of colorful vegetables",
            "Lean protein sources",
            "Whole grain carbohydrates",
            "Healthy fats (nuts, seeds, olive oil)",
            "Fresh fruits in moderation"
        ],
        
        "preparation": """**Meal Planning Strategy:**
1. Plan meals and snacks in advance
2. Prepare ingredients when time allows
3. Use healthy cooking methods (grilling, baking, steaming)
4. Season with herbs and spices instead of excess salt
5. Stay hydrated throughout the day""",
        
        "nutritional_info": {
            "calories": "Individualized based on needs",
            "protein": "15-20% of total calories",
            "carbs": "45-65% of total calories",
            "fat": "20-35% of total calories",
            "fiber": "25-35g daily",
            "sodium": "<2300mg daily"
        },
        
        "health_benefits": """**Holistic Health Benefits:**
• **Metabolic Optimization:** Improved insulin sensitivity and glucose control
• **Cardiovascular Support:** Reduced risk of heart disease
• **Weight Management:** Sustainable healthy weight maintenance
• **Energy Stability:** Consistent energy levels throughout the day
• **Immune Function:** Enhanced immune system support through proper nutrition

**Professional Recommendation:**
Consider consulting with a registered dietitian who specializes in diabetes care for personalized meal planning and ongoing support.""",

        "diabetes_tips": [
            "Read nutrition labels carefully for hidden sugars",
            "Practice portion control using measuring tools",
            "Stay consistent with meal timing",
            "Focus on how foods make you feel after eating"
        ]
    } 