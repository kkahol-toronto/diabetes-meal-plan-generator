export interface LabValues {
    a1c?: number;
    fastingGlucose?: number;
    ldlC?: number;
    hdlC?: number;
    triglycerides?: number;
    totalCholesterol?: number;
    egfr?: number;
    creatinine?: number;
    potassium?: number;
    uacr?: number;
    alt?: number;
    ast?: number;
    vitaminD?: number;
    vitaminB12?: number;
}

export interface VitalSigns {
    heightCm?: number;
    weightKg?: number;
    bmi?: number;
    bloodPressureSystolic?: number;
    bloodPressureDiastolic?: number;
    heartRateBpm?: number;
}

export interface DietaryInfo {
    dietType?: string;
    dietFeatures?: string[];
    allergies?: string;
    dislikes?: string;
}

export interface PhysicalActivity {
    workActivityLevel?: 'Sedentary' | 'Light' | 'Moderate' | 'Heavy';
    exerciseFrequency?: 'None' | '1-2 times/week' | '3-4 times/week' | '5+ times/week';
    exerciseTypes?: string[];
    exerciseTypesOther?: string;
    exerciseTypesOtherUpdatedBy?: 'admin' | 'user';
    mobilityIssues?: boolean;
}

export interface Lifestyle {
    mealPrepMethod?: 'Own' | 'Assisted' | 'Caregiver' | 'Delivery';
    availableAppliances?: string[];
    eatingSchedule?: '3 meals' | '2 meals + snack' | 'Fasting' | 'Night Shift' | 'Other';
    eatingScheduleOther?: string;
}

export interface MealPlanTargeting {
    wantsWeightLoss?: boolean;
    calorieTarget?: number;
}

export interface PatientProfile {
    // Date of Intake
    intakeDate?: string;
    intakeDateUpdatedBy?: string;

    // Patient Demographics
    fullName?: string;
    fullNameUpdatedBy?: string;
    dateOfBirth?: string;
    dateOfBirthUpdatedBy?: string;
    age?: number;
    ageUpdatedBy?: string;
    sex?: 'Male' | 'Female' | 'Other';
    sexUpdatedBy?: string;
    ethnicity?: string[];
    ethnicityUpdatedBy?: string;
    ethnicityOther?: string;
    ethnicityOtherUpdatedBy?: string;

    // Medical History
    medicalHistory?: string[];
    medicalHistoryUpdatedBy?: string;
    medicalHistoryOther?: string;
    medicalHistoryOtherUpdatedBy?: string;

    // Current Medications
    medications?: string[];
    medicationsUpdatedBy?: string;
    medicationsOther?: string;
    medicationsOtherUpdatedBy?: string;

    // Most Recent Lab Values
    labValues?: LabValues;
    labValuesUpdatedBy?: string;

    // Vital Signs
    vitalSigns?: VitalSigns;
    vitalSignsUpdatedBy?: string;

    // Dietary Information
    dietaryInfo?: DietaryInfo;
    dietaryInfoUpdatedBy?: string;

    // Physical Activity Profile
    physicalActivity?: PhysicalActivity;
    physicalActivityUpdatedBy?: string;

    // Lifestyle & Preferences
    lifestyle?: Lifestyle;
    lifestyleUpdatedBy?: string;

    // Goals & Readiness to Change
    goals?: string[];
    goalsUpdatedBy?: string;
    goalsOther?: string;
    goalsOtherUpdatedBy?: string;
    readiness?: 'Not ready' | 'Thinking about it' | 'Getting started' | 'Already making changes';
    readinessUpdatedBy?: string;

    // Meal Plan Targeting
    mealPlanTargeting?: MealPlanTargeting;
    mealPlanTargetingUpdatedBy?: string;
} 