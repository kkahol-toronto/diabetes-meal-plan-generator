export interface UserProfile {
  name: string;
  // 1. Patient Demographics
  dateOfBirth?: string; // ISO string format
  age?: number; // Calculated from DOB, might not be stored directly
  gender?: 'Male' | 'Female' | 'Other'; // Radio group options
  ethnicity?: string[]; // Multi-select with diverse options
  otherEthnicity?: string; // Added text input for 'Other' ethnicity

  // Existing fields that are still relevant (Physical measurements & Vitals)
  weight?: number;
  height?: number;
  waistCircumference?: number;
  systolicBP?: number;
  diastolicBP?: number;
  heartRate?: number;

  // 2. Medical History
  medicalConditions?: string[]; // Broader checklist
  otherMedicalCondition?: string; // Text input for 'Other' medical condition

  // 3. Current Medications
  medications?: string[]; // Checklist of medications
  otherMedication?: string; // Text input for 'Other' medication

  // 4. Lab Values (Optional) - Grouped under a nested object
  labValues?: {
    a1c?: number;
    fastingGlucose?: number;
    ldl?: number;
    hdl?: number;
    triglycerides?: number;
    totalCholesterol?: number; // Added Total Cholesterol
    egfr?: number;
    creatinine?: number;
    potassium?: number;
    alt?: number;
    ast?: number;
    uacr?: string; // Added uACR / proteinuria (using string for flexibility)
    vitaminD?: number;
    b12?: number;
  };

  // 5. Physical Activity Profile
  workActivityLevel?: 'Sedentary' | 'Moderate' | 'Physical Labor'; // Radio
  exerciseFrequency?: 'None' | '<60min' | '60–150' | '>150min'; // Radio
  exerciseTypes?: string[]; // Multi-select
  jointIssues?: boolean; // Yes/No radio

  // 6. Lifestyle & Preferences
  mealPrep?: 'Own' | 'Assisted' | 'Caregiver' | 'Delivery Service'; // Radio
  appliances?: string[]; // Multi-select checklist
  eatingSchedule?: '3 meals' | '2 meals + snack' | 'Fasting' | 'Night Shift'; // Radio

  // 7. Goals & Readiness to Change
  goals?: string[]; // Checklist of goals
  readinessToChange?: 'Not ready' | 'Considering' | 'Preparing' | 'Taking action'; // Radio

  // 8. Meal Plan Targeting
  wantsWeightLoss: boolean; // Checkbox
  calorieTarget?: string; // Dropdown options (e.g., '1500', '1800', 'Other')
  otherCalorieTarget?: number; // Text input for 'Other' calorie target

  // Existing dietary restrictions, food preferences, and allergies
  dietaryRestrictions?: string[];
  foodPreferences?: string[];
  allergies?: string[];

  // Remove fields that are replaced or no longer needed based on the new structure
  // dietType?: string[]; // Assuming replaced by dietFeatures/eatingSchedule
  // dietFeatures?: string[]; // Assuming replaced by exerciseTypes/goals

  // New fields
  dietType: string[];
  otherDietType?: string;

  // New fields for Dietary Features
  dietFeatures?: string[];
  foodAllergiesCustom?: string;
  strongDislikesCustom?: string;
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