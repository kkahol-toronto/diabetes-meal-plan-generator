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
  avoids?: string[];
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
  proteinTarget?: string;  // Daily protein goal in grams
  
  // Comprehensive Macro Goals
  macroGoals?: {
    protein?: number;
    carbs?: number;
    fat?: number;
  };
  
  // Legacy fields for backward compatibility
  dietFeatures?: string[];
  
  // Timezone for proper date filtering
  timezone?: string;
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

// Privacy & Consent Related Types
export interface ConsentSettings {
  consent_given: boolean;
  marketing_consent: boolean;
  analytics_consent: boolean;
  data_retention_preference: 'minimal' | 'standard' | 'extended';
  policy_version?: string;
  consent_timestamp?: string;
  last_consent_update?: string;
}

export interface UserData {
  email: string;
  username: string;
  disabled?: boolean;
  is_admin?: boolean;
  profile?: UserProfile;
  // Privacy & Consent Fields
  consent_given?: boolean;
  consent_timestamp?: string;
  policy_version?: string;
  data_retention_preference?: 'minimal' | 'standard' | 'extended';
  marketing_consent?: boolean;
  analytics_consent?: boolean;
  last_consent_update?: string;
}

export interface DataExportRequest {
  data_types: ('profile' | 'meal_plans' | 'consumption_history' | 'chat_history' | 'recipes' | 'shopping_lists')[];
  format_type: 'pdf' | 'json' | 'docx';
}

export interface AccountDeletionRequest {
  deletion_type: 'complete' | 'anonymize';
  confirmation: string;
}

export interface ConsentUpdateRequest {
  consent_given?: boolean;
  marketing_consent?: boolean;
  analytics_consent?: boolean;
  data_retention_preference?: 'minimal' | 'standard' | 'extended';
  policy_version?: string;
}

export interface DataExportMetadata {
  export_date: string;
  user_email: string;
  data_types_included: string[];
  policy_version: string;
  total_records: number;
} 