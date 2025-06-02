export interface UserProfile {
  name: string;
  age?: number;
  gender?: string;
  weight: number;
  height: number;
  waistCircumference?: number;
  systolicBP?: number;
  diastolicBP?: number;
  heartRate?: number;
  ethnicity?: string;
  dietType?: string[];
  calorieTarget?: string;
  dietFeatures?: string[];
  medicalConditions?: string[];
  wantsWeightLoss: boolean;
  dietaryRestrictions?: string[];
  foodPreferences?: string[];
  allergies?: string[];
}

export interface MealPlanData {
  id?: string;
  created_at?: string;
  breakfast: string[];
  lunch: string[];
  dinner: string[];
  snacks: string[];
  dailyCalories: number;
  macronutrients: {
    protein: number;
    carbs: number;
    fats: number;
  };
}

export interface Recipe {
  name: string;
  ingredients: string[];
  instructions: string[];
  nutritional_info: {
    calories: string;
    protein: string;
    carbs: string;
    fat: string;
  };
}

export interface ShoppingItem {
  name: string;
  amount: string;
  category: string;
  checked?: boolean;
} 