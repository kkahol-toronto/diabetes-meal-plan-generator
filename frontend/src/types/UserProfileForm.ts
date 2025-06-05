import { UserProfile } from './UserProfile';

export interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => Promise<void>;
  initialProfile?: UserProfile;
}

export interface UserProfileFormData {
  name: string;
  dateOfBirth: string;
  age: number;
  gender: string;
  ethnicity: string;
  medicalConditions: string[];
  dietaryRestrictions: string[];
  foodPreferences: string[];
  allergies: string[];
  height: number;
  weight: number;
  waistCircumference?: number;
  systolicBP?: number;
  diastolicBP?: number;
  heartRate?: number;
  dietType: string[];
  calorieTarget: string;
  dietFeatures: string[];
  wantsWeightLoss: boolean;
}

export const emptyFormData: UserProfileFormData = {
  name: '',
  dateOfBirth: '',
  age: 0,
  gender: '',
  ethnicity: '',
  medicalConditions: [],
  dietaryRestrictions: [],
  foodPreferences: [],
  allergies: [],
  height: 0,
  weight: 0,
  waistCircumference: undefined,
  systolicBP: undefined,
  diastolicBP: undefined,
  heartRate: undefined,
  dietType: [],
  calorieTarget: '',
  dietFeatures: [],
  wantsWeightLoss: false
}; 