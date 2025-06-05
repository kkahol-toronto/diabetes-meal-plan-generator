export interface UserProfile {
  // Patient Demographics
  name: string;
  dateOfBirth?: string;
  age?: number;
  gender?: string;
  ethnicity?: string[];
  
  // Medical History
  medicalConditions?: string[];
  
  // Current Medications
  currentMedications?: string[];
  
  // Lab Values (Optional)
  labValues?: {
    a1c?: string;
    fastingGlucose?: string;
    ldlCholesterol?: string;
    hdlCholesterol?: string;
    triglycerides?: string;
    totalCholesterol?: string;
    egfr?: string;
    creatinine?: string;
    potassium?: string;
    uacr?: string;
    alt?: string;
    ast?: string;
    vitaminD?: string;
    b12?: string;
  };
  
  // Vital Signs
  height: number;
  weight: number;
  bmi?: number;
  waistCircumference?: number;
  systolicBP?: number;
  diastolicBP?: number;
  heartRate?: number;
  
  // Dietary Information
  dietType?: string[];
  dietaryFeatures?: string[];
  dietaryRestrictions?: string[];
  foodPreferences?: string[];
  allergies?: string[];
  strongDislikes?: string[];
  
  // Physical Activity
  workActivityLevel?: string;
  exerciseFrequency?: string;
  exerciseTypes?: string[];
  mobilityIssues?: boolean;
  
  // Lifestyle & Preferences
  mealPrepCapability?: string;
  availableAppliances?: string[];
  eatingSchedule?: string;
  
  // Goals & Readiness
  primaryGoals?: string[];
  readinessToChange?: string;
  
  // Meal Plan Targeting
  wantsWeightLoss: boolean;
  calorieTarget?: string;
  
  // Legacy fields for backward compatibility
  dietFeatures?: string[];
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
  recipes?: Recipe[];
  shopping_list?: ShoppingItem[];
  consolidated_pdf?: {
    filename: string;
    file_path: string;
    generated_at: string;
    file_size: number;
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