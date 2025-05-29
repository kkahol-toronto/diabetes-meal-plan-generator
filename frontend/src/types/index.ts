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
  dietTypes?: string[];
  calorieTarget?: string;
  dietFeatures?: string[];
  medicalConditions?: string[];
  otherMedicalCondition?: string;
  wantsWeightLoss: boolean;
  dietaryRestrictions?: string[];
  otherDietaryRestriction?: string;
  healthConditions?: string[];
  otherHealthCondition?: string;
  foodPreferences?: string[];
  otherFoodPreference?: string;
  allergies?: string[];
  otherAllergy?: string;
}

export interface MealPlanData {
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

export interface SavedMealPlan extends MealPlanData {
  id: string;
  session_id: string;
  created_at: string;
  user_id: string;
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