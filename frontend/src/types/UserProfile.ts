export interface UserProfile {
  // Patient Demographics
  fullName: string;
  dateOfBirth: string;         // yyyy-MM-dd
  age: number;
  sex: 'Male' | 'Female' | 'Other' | '';
  ethnicity: string[];         // multi-select

  // Medical History & Conditions
  medicalHistory: string[];
  medicalConditions: string[]; // multi-select
  currentMedications: string[];

  // Most Recent Lab Values (all optional numbers; allow empty string or null)
  a1c: number | null;
  fastingGlucose: number | null;
  ldl: number | null;
  hdl: number | null;
  triglycerides: number | null;
  totalCholesterol: number | null;
  egfr: number | null;
  creatinine: number | null;
  potassium: number | null;
  uacr: number | null;
  altAst: number | null;
  vitaminD: number | null;
  b12: number | null;

  // Vital Signs
  height: number | null;       // in cm
  weight: number | null;       // in kg
  bmi: number | null;          // auto-calc if both height & weight present
  bloodPressureSys: number | null;
  bloodPressureDia: number | null;
  heartRate: number | null;
  waistCircumference: number | null;
  systolicBP: number | null;
  diastolicBP: number | null;

  // Dietary Information
  typeOfDiet: string;          // single-select
  dietaryFeatures: string[];   // multi-select
  dietaryAllergies: string;    // free text for "Other" (if any)
  strongDislikes: string;      // free text
  dietaryRestrictions: string[]; // multi-select
  foodPreferences: string[];   // multi-select
  allergies: string[];        // multi-select
  dietType: string[];         // multi-select
  calorieTarget: string;      // single-select

  // Physical Activity Profile
  workActivity: 'Sedentary' | 'Moderately Active' | 'Active' | '';
  exerciseFrequency: '<30–60' | '60–150' | '>150' | 'None' | '';
  exerciseTypes: string[];     // multi-select
  mobilityIssues: boolean;

  // Lifestyle & Preferences
  mealPrepCapability: string;  // single-select
  appliances: string[];        // multi-select
  eatingSchedule: string;      // single-select
  eatingScheduleOther: string; // free text if "Other" chosen

  // Goals & Readiness
  primaryGoals: string[];      // multi-select
  readinessToChange: string;   // single-select

  // Meal Plan Targeting
  weightLossDesired: boolean;
  wantsWeightLoss: boolean;
  suggestedCalorieTarget: number | null;
  suggestedCalorieOther: number | null; // if "Other" chosen
}

export const emptyProfile: UserProfile = {
  // Patient Demographics
  fullName: '',
  dateOfBirth: '',
  age: 0,
  sex: '',
  ethnicity: [],

  // Medical History & Conditions
  medicalHistory: [],
  medicalConditions: [],
  currentMedications: [],

  // Lab Values
  a1c: null,
  fastingGlucose: null,
  ldl: null,
  hdl: null,
  triglycerides: null,
  totalCholesterol: null,
  egfr: null,
  creatinine: null,
  potassium: null,
  uacr: null,
  altAst: null,
  vitaminD: null,
  b12: null,

  // Vital Signs
  height: null,
  weight: null,
  bmi: null,
  bloodPressureSys: null,
  bloodPressureDia: null,
  heartRate: null,
  waistCircumference: null,
  systolicBP: null,
  diastolicBP: null,

  // Dietary Information
  typeOfDiet: '',
  dietaryFeatures: [],
  dietaryAllergies: '',
  strongDislikes: '',
  dietaryRestrictions: [],
  foodPreferences: [],
  allergies: [],
  dietType: [],
  calorieTarget: '',

  // Physical Activity
  workActivity: '',
  exerciseFrequency: '',
  exerciseTypes: [],
  mobilityIssues: false,

  // Lifestyle & Preferences
  mealPrepCapability: '',
  appliances: [],
  eatingSchedule: '',
  eatingScheduleOther: '',

  // Goals & Readiness
  primaryGoals: [],
  readinessToChange: '',

  // Meal Plan Targeting
  weightLossDesired: false,
  wantsWeightLoss: false,
  suggestedCalorieTarget: null,
  suggestedCalorieOther: null,
}; 