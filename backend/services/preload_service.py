"""
Preload service for caching frequently used data at startup.
Reduces response times by pre-loading common data.
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import json

class PreloadService:
    """Service to preload and cache frequently accessed data"""
    
    def __init__(self):
        self.preloaded_data = {}
        self.is_loaded = False
        self.load_start_time = None
        
    async def initialize(self):
        """Initialize preload service with common data"""
        self.load_start_time = datetime.utcnow()
        print("[PRELOAD] Starting data preload...")
        
        try:
            # Preload common meal templates
            await self._load_meal_templates()
            
            # Preload dietary restriction mappings
            await self._load_dietary_mappings()
            
            # Preload nutrition data
            await self._load_nutrition_data()
            
            self.is_loaded = True
            load_time = (datetime.utcnow() - self.load_start_time).total_seconds()
            print(f"[PRELOAD] ✅ Data preload completed in {load_time:.2f}s")
            
        except Exception as e:
            print(f"[PRELOAD] ❌ Error during preload: {e}")
            self.is_loaded = False
    
    async def _load_meal_templates(self):
        """Load common meal templates for quick access"""
        meal_templates = {
            'vegetarian': {
                'breakfast': [
                    "Steel-cut oats with almond milk and fresh berries",
                    "Greek yogurt parfait with granola and seasonal fruit",
                    "Avocado toast on whole grain bread with tomatoes",
                    "Smoothie bowl with spinach, banana, and chia seeds"
                ],
                'lunch': [
                    "Quinoa Buddha bowl with roasted vegetables and tahini",
                    "Lentil soup with whole grain bread",
                    "Chickpea salad wrap with mixed greens",
                    "Mediterranean vegetable and hummus plate"
                ],
                'dinner': [
                    "Lentil curry with brown rice and steamed broccoli",
                    "Stuffed bell peppers with quinoa and vegetables",
                    "Vegetable stir-fry with tofu and brown rice",
                    "Eggplant and chickpea curry with cauliflower rice"
                ],
                'snacks': [
                    "Apple slices with almond butter",
                    "Hummus with cucumber and carrot sticks",
                    "Greek yogurt with cinnamon",
                    "Mixed nuts and berries"
                ]
            },
            'standard': {
                'breakfast': [
                    "Greek yogurt with berries and nuts",
                    "Scrambled eggs with spinach and whole grain toast",
                    "Oatmeal with protein powder and fruit",
                    "Cottage cheese with sliced tomatoes"
                ],
                'lunch': [
                    "Grilled chicken salad with mixed vegetables",
                    "Turkey and avocado wrap",
                    "Salmon salad with quinoa",
                    "Lean protein bowl with vegetables"
                ],
                'dinner': [
                    "Baked salmon with sweet potato and steamed vegetables",
                    "Grilled chicken with quinoa and roasted broccoli",
                    "Lean beef stir-fry with vegetables",
                    "Turkey meatballs with zucchini noodles"
                ],
                'snacks': [
                    "Hard-boiled egg with vegetables",
                    "Protein smoothie",
                    "Cottage cheese with berries",
                    "Nuts and Greek yogurt"
                ]
            }
        }
        
        self.preloaded_data['meal_templates'] = meal_templates
    
    async def _load_dietary_mappings(self):
        """Load dietary restriction to meal type mappings"""
        dietary_mappings = {
            'vegetarian_keywords': [
                'vegetarian', 'veg', 'plant-based', 'no meat', 'meat-free'
            ],
            'vegan_keywords': [
                'vegan', 'plant only', 'no dairy', 'no eggs', 'no animal products'
            ],
            'diabetic_friendly': [
                'low gi', 'low glycemic', 'diabetes friendly', 'sugar free', 'low carb'
            ],
            'allergies': {
                'nuts': ['almond', 'peanut', 'walnut', 'cashew', 'pistachio'],
                'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
                'eggs': ['egg', 'eggs', 'omelet', 'mayonnaise'],
                'gluten': ['wheat', 'bread', 'pasta', 'flour', 'oats']
            }
        }
        
        self.preloaded_data['dietary_mappings'] = dietary_mappings
    
    async def _load_nutrition_data(self):
        """Load common nutrition data for quick calculations"""
        nutrition_data = {
            'macros_per_gram': {
                'protein': 4,  # calories per gram
                'carbs': 4,
                'fat': 9,
                'alcohol': 7
            },
            'daily_targets': {
                'sedentary_male': {'calories': 2000, 'protein': 100, 'carbs': 250, 'fat': 67},
                'sedentary_female': {'calories': 1600, 'protein': 80, 'carbs': 200, 'fat': 53},
                'active_male': {'calories': 2400, 'protein': 120, 'carbs': 300, 'fat': 80},
                'active_female': {'calories': 2000, 'protein': 100, 'carbs': 250, 'fat': 67}
            },
            'diabetes_guidelines': {
                'max_carbs_per_meal': 45,
                'max_sugar_per_meal': 15,
                'min_fiber_per_meal': 5,
                'max_sodium_per_meal': 800
            }
        }
        
        self.preloaded_data['nutrition_data'] = nutrition_data
    
    def get_meal_templates(self, diet_type: str = 'standard') -> Dict[str, List[str]]:
        """Get preloaded meal templates"""
        if not self.is_loaded:
            return self._get_fallback_templates(diet_type)
        
        templates = self.preloaded_data.get('meal_templates', {})
        return templates.get(diet_type, templates.get('standard', {}))
    
    def get_dietary_mappings(self) -> Dict[str, Any]:
        """Get preloaded dietary mappings"""
        if not self.is_loaded:
            return {}
        
        return self.preloaded_data.get('dietary_mappings', {})
    
    def get_nutrition_data(self) -> Dict[str, Any]:
        """Get preloaded nutrition data"""
        if not self.is_loaded:
            return self._get_fallback_nutrition()
        
        return self.preloaded_data.get('nutrition_data', {})
    
    def _get_fallback_templates(self, diet_type: str) -> Dict[str, List[str]]:
        """Fallback templates if preload failed"""
        if 'vegetarian' in diet_type.lower():
            return {
                'breakfast': ["Oatmeal with berries"],
                'lunch': ["Quinoa salad"],
                'dinner': ["Lentil curry"],
                'snack': ["Apple with almond butter"]
            }
        else:
            return {
                'breakfast': ["Greek yogurt with fruit"],
                'lunch': ["Chicken salad"],
                'dinner': ["Grilled fish with vegetables"],
                'snack': ["Mixed nuts"]
            }
    
    def _get_fallback_nutrition(self) -> Dict[str, Any]:
        """Fallback nutrition data"""
        return {
            'macros_per_gram': {'protein': 4, 'carbs': 4, 'fat': 9},
            'daily_targets': {'calories': 2000, 'protein': 100, 'carbs': 250, 'fat': 67}
        }
    
    def get_load_status(self) -> Dict[str, Any]:
        """Get preload service status"""
        load_time = 0
        if self.load_start_time:
            load_time = (datetime.utcnow() - self.load_start_time).total_seconds()
        
        return {
            'is_loaded': self.is_loaded,
            'load_time_seconds': load_time,
            'data_keys': list(self.preloaded_data.keys()),
            'total_items': sum(len(v) if isinstance(v, (list, dict)) else 1 for v in self.preloaded_data.values())
        }

# Global preload service instance
preload_service = PreloadService()

# Convenience functions
def get_quick_meal_templates(diet_type: str = 'standard'):
    """Get meal templates quickly"""
    return preload_service.get_meal_templates(diet_type)

def get_dietary_restrictions_info():
    """Get dietary restrictions information"""
    return preload_service.get_dietary_mappings()

def get_nutrition_guidelines():
    """Get nutrition calculation data"""
    return preload_service.get_nutrition_data()