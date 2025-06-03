import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Grid,
  Box,
  Chip,
  OutlinedInput,
  SelectChangeEvent,
  FormHelperText,
  FormControlLabel,
  Checkbox,
  Switch,
  TableContainer,
  Table,
  TableBody,
  TableCell,
  TableRow,
  FormLabel,
  RadioGroup,
  Radio,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { format, differenceInYears, parseISO, isValid } from 'date-fns';
import { UserProfile } from '../types';

const dietTypeOptions = [
  'Western',
  'Mediterranean',
  'South Asian – North Indian',
  'South Asian – Pakistani',
  'South Asian – Sri Lankan',
  'South Asian – South Indian',
  'East Asian – Chinese / Korean',
  'Caribbean – Jamaican / Guyanese',
  'Filipino',
  'Other'
];

const medicalConditions = [
  'Diabetes',
  'Obesity',
  'Coronary Artery Disease',
  'Stroke',
  'Peripheral Vascular Disease',
  'Chronic Kidney Disease',
  'Proteinuria',
  'Elevated Potassium',
  'Hypertension',
  'High Cholesterol',
  'High Triglycerides',
  'Fatty Liver',
  'PCOS',
  'Other'
];

const ethnicities = [
  'South Asian',
  'East Asian',
  'European',
  'Caucasian',
  'African',
  'African American',
  'Caribbean',
  'Jamaican',
  'Guyanese',
  'Middle Eastern'
];

const dietTypes = [
  'Western',
  'Mediterranean',
  'South Asian - North Indian',
  'South Asian - South Indian',
  'South Asian - Sri Lankan',
  'South Asian - Pakistan',
  'South Asian - Bangladesh',
  'East Asian',
  'European',
  'Caucasian',
  'African',
  'African American',
  'Caribbean',
  'Jamaican',
  'Guyanese',
  'Middle Eastern'
];

const dietFeatures = [
  'Low carb',
  'High protein',
  'Normal protein',
  'Low potassium',
  'Low saturated fat',
  'Predominantly plant based with some animal protein',
  'Completely plant based',
  'Vegetarian with no eggs',
  'Vegetarian with eggs'
];

const calorieTargets = [
  '1500',
  '1800',
  '2000',
  '2200'
];

const genderOptions = [
  'Male',
  'Female',
  'Non-binary',
  'Genderqueer',
  'Transgender',
  'Prefer not to say',
  'Other',
];

// Add options for new fields
const dietaryRestrictionsOptions = [
  'Vegetarian',
  'Vegan',
  'Gluten Free',
  'Dairy Free',
  'Nut Free',
  'Low Sodium',
  'Low Sugar',
  'Halal',
  'Kosher',
  'Other',
];
const foodPreferencesOptions = [
  'Spicy',
  'Mild',
  'Sweet',
  'Savory',
  'Crunchy',
  'Soft',
  'Other',
];
const allergiesOptions = [
  'None',
  'Peanuts',
  'Tree Nuts',
  'Milk',
  'Eggs',
  'Fish',
  'Shellfish',
  'Soy',
  'Wheat',
  'Sesame',
  'Other',
];

// Add new options arrays for the expanded form
const medicalConditionsOptions = [
  'Type 1 Diabetes',
  'Type 2 Diabetes',
  'PCOS',
  'GERD',
  'Osteoporosis',
  'Hypertension',
  'High Cholesterol',
  'High Triglycerides',
  'Fatty Liver',
  'Chronic Kidney Disease',
  'Coronary Artery Disease',
  'Stroke',
  'Peripheral Vascular Disease',
  'Obesity',
  'Other',
];

const medicationsOptions = [
  'Metformin',
  'Insulin',
  'Ozempic',
  // Add more common diabetes/related medications
  'Lisinopril', // Example for hypertension
  'Atorvastatin', // Example for high cholesterol
  'Jardiance', // Example SGLT2 inhibitor
  'Trulicity', // Example GLP-1 agonist
  'Januvia', // Example DPP-4 inhibitor
  'Glipizide', // Example Sulfonylurea
  'Warfarin', // Example Anticoagulant
  'Aspirin', // Example Antiplatelet
  'Beta-blockers', // Example for heart conditions
  'ACE Inhibitors', // Example for hypertension/CKD
  'Statins', // Example for high cholesterol
  'Diuretics', // Example for hypertension/fluid retention
  'Other',
];

const workActivityLevelOptions = ['Sedentary', 'Moderate', 'Physical Labor'];

const exerciseFrequencyOptions = ['None', '<60min', '60–150', '>150min'];

const exerciseTypesOptions = [
  'Walking',
  'Running',
  'Cycling',
  'Swimming',
  'Weights',
  'Yoga',
  'Pilates',
  'Aerobics',
  'Sports',
  'Other',
];

const mealPrepOptions = ['Own', 'Assisted', 'Caregiver', 'Delivery Service'];

const appliancesOptions = [
  'Microwave',
  'Oven',
  'Stove',
  'Air Fryer',
  'Blender',
  'Food Processor',
  'Slow Cooker',
  'Pressure Cooker',
  'Toaster',
  'Grill',
  'Other',
];

const eatingScheduleOptions = ['3 meals', '2 meals + snack', 'Fasting', 'Night Shift'];

const goalsOptions = [
  'Weight loss',
  'Lower A1C',
  'Increase energy',
  'Improve cholesterol',
  'Lower blood pressure',
  'Better blood sugar control',
  'Reduce medication reliance',
  'Learn healthy eating habits',
  'Meal planning skills',
  'More physical activity',
  'Other',
];

const readinessToChangeOptions = ['Not ready', 'Considering', 'Preparing', 'Taking action'];

const calorieTargetOptions = ['1500', '1800', '2000', '2200', 'Other'];

// New options array for Dietary Features
const dietFeaturesOptions = [
  'Low Carb',
  'High Protein',
  'Normal Protein',
  'Low Saturated Fat',
  'Low Potassium',
  'Predominantly Plant-Based',
  'Plant-Based + Egg Whites / Chicken / Fish',
  'Vegetarian (with eggs)',
  'Vegetarian (no eggs)',
  'Soft Texture Required',
  'Gluten-Free',
  'Lactose-Free',
  'Avoids: tofu, coconut, turmeric, etc.',
];

interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  initialProfile?: Partial<UserProfile>;
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ onSubmit, initialProfile }) => {
  // Add state for registration code and stored patient ID
  const [storedRegistrationCode, setStoredRegistrationCode] = useState<string | null>(null);
  const [storedPatientId, setStoredPatientId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize visibility states based on initialProfile, defaulting to false if profile data is missing or empty
  const [showDietType, setShowDietType] = useState((initialProfile?.dietType || []).length > 0);
  const [showDietFeatures, setShowDietFeatures] = useState((initialProfile?.dietFeatures || []).length > 0 || !!initialProfile?.foodAllergiesCustom || !!initialProfile?.strongDislikesCustom);

  // Convert height from feet/inches to cm
  const convertHeightToCm = (feet: number, inches: number) => {
    return Math.round((feet * 30.48) + (inches * 2.54));
  };

  // Convert height from cm to feet/inches
  const convertHeightToFtIn = (cm: number) => {
    const totalInches = cm / 2.54;
    const feet = Math.floor(totalInches / 12);
    const inches = Math.round(totalInches % 12);
    return { feet, inches };
  };

  // Convert weight between kg and lbs
  const convertWeight = (value: number, from: 'kg' | 'lbs', to: 'kg' | 'lbs') => {
    if (from === to) return value;
    return from === 'kg' ? Math.round(value * 2.20462) : Math.round(value / 2.20462);
  };

  // Convert waist circumference between cm and inches
  const convertWaist = (value: number, from: 'cm' | 'in', to: 'cm' | 'in') => {
    if (from === to) return value;
    return from === 'cm' ? Math.round(value / 2.54) : Math.round(value * 2.54);
  };

  // Initialize state with initialProfile if provided, otherwise use empty defaults
  const defaultProfile: Partial<UserProfile> = {
    name: '',
    dateOfBirth: undefined,
    age: undefined,
    gender: undefined,
    ethnicity: [], // Default to empty array
    weight: undefined,
    height: undefined,
    waistCircumference: undefined,
    systolicBP: undefined,
    diastolicBP: undefined,
    heartRate: undefined,
    medicalConditions: [], // Default to empty array
    otherMedicalCondition: '',
    medications: [], // Default to empty array
    otherMedication: '',
    labValues: {}, // Default to empty object
    workActivityLevel: undefined,
    exerciseFrequency: undefined,
    exerciseTypes: [], // Default to empty array
    jointIssues: undefined,
    mealPrep: undefined,
    appliances: [], // Default to empty array
    eatingSchedule: undefined,
    goals: [], // Default to empty array
    readinessToChange: undefined,
    wantsWeightLoss: false,
    calorieTarget: '',
    otherCalorieTarget: undefined,
    dietaryRestrictions: [], // Default to empty array
    foodPreferences: [], // Default to empty array
    allergies: [], // Default to empty array
    otherEthnicity: '',
    dietType: [], // Default to empty array
    otherDietType: '',
    dietFeatures: [], // Default to empty array
    foodAllergiesCustom: '',
    strongDislikesCustom: '',
  };

  // Calculate initial state for formData, ensuring all array fields are arrays and using initialProfile
  const initialFormData: Partial<UserProfile> = {
    ...defaultProfile,
    ...initialProfile,
    // Explicitly ensure these fields are arrays, even if initialProfile has null/undefined/non-array values
    ethnicity: Array.isArray(initialProfile?.ethnicity) ? initialProfile.ethnicity : [],
    medicalConditions: Array.isArray(initialProfile?.medicalConditions) ? initialProfile.medicalConditions : [],
    medications: Array.isArray(initialProfile?.medications) ? initialProfile.medications : [],
    exerciseTypes: Array.isArray(initialProfile?.exerciseTypes) ? initialProfile.exerciseTypes : [],
    appliances: Array.isArray(initialProfile?.appliances) ? initialProfile.appliances : [],
    goals: Array.isArray(initialProfile?.goals) ? initialProfile.goals : [],
    dietaryRestrictions: Array.isArray(initialProfile?.dietaryRestrictions) ? initialProfile.dietaryRestrictions : [],
    foodPreferences: Array.isArray(initialProfile?.foodPreferences) ? initialProfile.foodPreferences : [],
    allergies: Array.isArray(initialProfile?.allergies) ? initialProfile.allergies : [],
    dietType: Array.isArray(initialProfile?.dietType) ? initialProfile.dietType : [],
    dietFeatures: Array.isArray(initialProfile?.dietFeatures) ? initialProfile.dietFeatures : [],
    // Handle nested labValues, ensuring it's an object, defaulting to empty object
    labValues: typeof initialProfile?.labValues === 'object' && initialProfile.labValues !== null && !Array.isArray(initialProfile.labValues)
               ? initialProfile.labValues
               : {},
    // Ensure boolean and optional fields use defaults if undefined or null in initialProfile
    wantsWeightLoss: initialProfile?.wantsWeightLoss ?? defaultProfile.wantsWeightLoss,
    otherEthnicity: initialProfile?.otherEthnicity ?? defaultProfile.otherEthnicity,
    otherDietType: initialProfile?.otherDietType ?? defaultProfile.otherDietType,
    foodAllergiesCustom: initialProfile?.foodAllergiesCustom ?? defaultProfile.foodAllergiesCustom,
    strongDislikesCustom: initialProfile?.strongDislikesCustom ?? defaultProfile.strongDislikesCustom,
    dateOfBirth: initialProfile?.dateOfBirth || undefined, // Keep dateOfBirth as is for useEffect
    // Age will be calculated by the useEffect hook below
    age: undefined,
  };

  const [formData, setFormData] = useState<Partial<UserProfile>>(initialFormData);

  // Calculate initial unit states based on initialProfile
  let initialHeightUnit = 'cm' as 'cm' | 'ft-in';
  let initialWeightUnit = 'kg' as 'kg' | 'lbs';
  let initialWaistUnit = 'cm' as 'cm' | 'in';

  // We only set the unit if the initial value is actually present.
  if (initialProfile?.height !== undefined && initialProfile.height !== null) {
      // Assuming initial height is in cm if present
      initialHeightUnit = 'cm'; // Default is already cm, but being explicit
      // If we had logic to detect imperial, we would set it here
  }
   if (initialProfile?.weight !== undefined && initialProfile.weight !== null) {
      // Assuming initial weight is in kg if present
      initialWeightUnit = 'kg'; // Default is already kg
      // If we had logic to detect imperial, we would set it here
  }
   if (initialProfile?.waistCircumference !== undefined && initialProfile.waistCircumference !== null) {
     // Assuming initial waist is in cm if present
      initialWaistUnit = 'cm'; // Default is already cm
      // If we had logic to detect imperial, we would set it here
  }

  // Calculate initial height feet and inches if unit is feet/inches and height is a number
  let initialHeightFeet: number | '' = '';
  let initialHeightInches: number | '' = '';
  if (initialHeightUnit === 'ft-in' && typeof initialFormData.height === 'number') {
       const { feet, inches } = convertHeightToFtIn(initialFormData.height);
       initialHeightFeet = feet;
       initialHeightInches = inches;
  }

  // Declare state hooks with calculated initial values
  const [heightUnit, setHeightUnit] = useState<'cm' | 'ft-in'>(initialHeightUnit);
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lbs'>(initialWeightUnit);
  const [waistUnit, setWaistUnit] = useState<'cm' | 'in'>(initialWaistUnit);
  const [heightFeet, setHeightFeet] = useState<number | ''>(
    initialHeightFeet
  );
  const [heightInches, setHeightInches] = useState<number | ''>(
    initialHeightInches
  );
  const [errors, setErrors] = useState<Partial<Record<keyof UserProfile, string>>>({});
  const [loadingProfile, setLoadingProfile] = useState(false);

  const handleHeightUnitChange = (event: SelectChangeEvent<'cm' | 'ft-in'>) => {
    const newUnit = event.target.value as 'cm' | 'ft-in';
    setHeightUnit(newUnit);
    
    if (formData.height) {
      if (newUnit === 'ft-in') {
        const { feet, inches } = convertHeightToFtIn(formData.height);
        setHeightFeet(feet);
        setHeightInches(inches);
      }
    }
  };

  const handleWeightUnitChange = (event: SelectChangeEvent<'kg' | 'lbs'>) => {
    const newUnit = event.target.value as 'kg' | 'lbs';
    setWeightUnit(newUnit);
    
    if (formData.weight) {
      const newWeight = convertWeight(formData.weight, weightUnit, newUnit);
      setFormData(prev => ({ ...prev, weight: newWeight }));
    }
  };

  const handleHeightChange = (type: 'feet' | 'inches' | 'cm', value: string) => {
    if (heightUnit === 'cm') {
      setFormData(prev => ({ ...prev, height: value === '' ? undefined : Number(value) }));
    } else {
      const numValue = value === '' ? '' : Number(value);
      if (type === 'feet') {
        setHeightFeet(numValue);
      } else {
        setHeightInches(numValue);
      }
      
      if (typeof heightFeet === 'number' && typeof heightInches === 'number') {
        const heightInCm = convertHeightToCm(heightFeet, heightInches);
        setFormData(prev => ({ ...prev, height: heightInCm }));
      }
    }
  };

  const handleWaistUnitChange = (event: SelectChangeEvent<'cm' | 'in'>) => {
    const newUnit = event.target.value as 'cm' | 'in';
    setWaistUnit(newUnit);
    
    if (formData.waistCircumference) {
      const newWaist = convertWaist(formData.waistCircumference, waistUnit, newUnit);
      setFormData(prev => ({ ...prev, waistCircumference: newWaist }));
    }
  };

  const handleInputChange = (field: keyof UserProfile) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const value = event.target.value;
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleSelectChange = (field: keyof UserProfile) => (
    event: SelectChangeEvent<string>
  ) => {
    const value = event.target.value;
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleMultiSelectChange = (field: keyof UserProfile) => (
    event: SelectChangeEvent<string[]>
  ) => {
    const value = event.target.value as string[];
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const calculateBMI = () => {
    if (formData.height && formData.weight) {
      // Height should always be in cm and weight in kg in formData
      const heightInMeters = formData.height / 100;
      const weightInKg = weightUnit === 'lbs' ? formData.weight / 2.20462 : formData.weight;
      return (weightInKg / (heightInMeters * heightInMeters)).toFixed(1);
    }
    return '';
  };

  // Fetch user profile and registration code on mount
  useEffect(() => {
    const fetchUserData = async () => {
      setIsLoading(true); // Ensure loading is true when fetching starts
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          console.error('No authentication token found');
          // If no token, initialize form and stop loading
          setFormData(initialFormData);
          setIsLoading(false);
          return;
        }

        // Attempt to fetch the user's profile using the auth token
        console.log('Attempting to fetch user profile with token...');
        const response = await fetch('/api/user/profile', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        const responseText = await response.text(); // Read response as text first
        console.log('Raw response status:', response.status);
        console.log('Raw response text:', responseText); // Log the raw response text

        if (response.ok) {
          // Response status is OK (e.g., 200), now try to parse JSON
          console.log('Profile found (OK status). Attempting to parse data...');

          try {
            const profileData = JSON.parse(responseText); // Manually parse after logging

            setFormData(prevFormData => ({
              ...prevFormData,
              ...profileData,
              labValues: { ...prevFormData.labValues, ...profileData.labValues },
              ethnicity: Array.isArray(profileData.ethnicity) ? profileData.ethnicity : prevFormData.ethnicity,
              medicalConditions: Array.isArray(profileData.medicalConditions) ? profileData.medicalConditions : prevFormData.medicalConditions,
              medications: Array.isArray(profileData.medications) ? profileData.medications : prevFormData.medications,
              exerciseTypes: Array.isArray(profileData.exerciseTypes) ? profileData.exerciseTypes : prevFormData.exerciseTypes,
              appliances: Array.isArray(profileData.appliances) ? profileData.appliances : prevFormData.appliances,
              goals: Array.isArray(profileData.goals) ? profileData.goals : prevFormData.goals,
              dietaryRestrictions: Array.isArray(profileData.dietaryRestrictions) ? profileData.dietaryRestrictions : prevFormData.dietaryRestrictions,
              foodPreferences: Array.isArray(profileData.foodPreferences) ? profileData.foodPreferences : prevFormData.foodPreferences,
              allergies: Array.isArray(profileData.allergies) ? profileData.allergies : prevFormData.allergies,
              dietType: Array.isArray(profileData.dietType) ? profileData.dietType : prevFormData.dietType,
              dietFeatures: Array.isArray(profileData.dietFeatures) ? profileData.dietFeatures : prevFormData.dietFeatures,
              wantsWeightLoss: profileData.wantsWeightLoss ?? prevFormData.wantsWeightLoss,
              otherEthnicity: profileData.otherEthnicity ?? prevFormData.otherEthnicity,
              otherDietType: profileData.otherDietType ?? prevFormData.otherDietType,
              foodAllergiesCustom: profileData.foodAllergiesCustom ?? prevFormData.foodAllergiesCustom,
              strongDislikesCustom: profileData.strongDislikesCustom ?? defaultProfile.strongDislikesCustom,
              dateOfBirth: profileData.dateOfBirth || undefined,
              age: profileData.dateOfBirth ? differenceInYears(new Date(), parseISO(profileData.dateOfBirth)) : undefined,
            }));
            setStoredPatientId(profileData.patient_id); // Store the fetched patient ID
            // Assuming registration_code might also be returned here for existing users, store it
            if (profileData.registration_code) {
              setStoredRegistrationCode(profileData.registration_code);
              // Keep it in localStorage for the create case if needed later
              localStorage.setItem('registrationCode', profileData.registration_code);
            }
            console.log('Profile data loaded successfully.');
          } catch (parseError) {
            console.error("Failed to parse profile data as JSON (unexpected format?):", parseError);
            // If parsing fails, it's likely not the expected JSON response (e.g., HTML).
            // Treat this as no profile found or an error, and fallback to registration code.
             console.log('Assuming no profile found due to JSON parsing error. Checking localStorage for registration code.');
             const regCode = localStorage.getItem('registrationCode');
             setStoredRegistrationCode(regCode);
             // Initialize form data for new profile creation
              setFormData(initialFormData);
             console.log('Initialized form for new profile creation after parse error.');
          }
        } else if (response.status === 404) {
          // No existing profile found for this user (404 response).
          // Get the registration code from localStorage for potential new profile creation.
          console.log('No existing profile found for this user (404 response). Checking localStorage for registration code.');
          const regCode = localStorage.getItem('registrationCode');
          setStoredRegistrationCode(regCode);
           // Initialize form data with initialProfile if provided, otherwise defaults.
            setFormData(initialFormData);
           console.log('Initialized form for new profile creation after 404.');

        } else {
          // Handle other potential errors when fetching profile (e.g., 500, 401, etc.)
          console.error('Error fetching user profile:', response.status, response.statusText);
          // Optionally, set an error state to display to the user
            setFormData(initialFormData);
           console.log('Initialized form after other fetch error.');
        }
      } catch (error) {
        // Catch network errors or errors before response is received
        console.error('Error in fetchUserData (catch block):', error);
         // Initialize form data with initialProfile if provided, otherwise defaults.
           setFormData(initialFormData);
           console.log('Initialized form after fetch error in catch block.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, []); // Empty dependency array to run only on mount

  // Calculate age whenever dateOfBirth changes
  useEffect(() => {
    if (formData.dateOfBirth) {
      try {
        const dob = parseISO(formData.dateOfBirth);
        if (isValid(dob)) {
          const age = differenceInYears(new Date(), dob);
          setFormData(prev => ({ ...prev, age }));
        } else {
          setFormData(prev => ({ ...prev, age: undefined }));
        }
      } catch (error) {
        console.error("Error calculating age from dateOfBirth:", error);
        setFormData(prev => ({ ...prev, age: undefined }));
      }
    } else {
      setFormData(prev => ({ ...prev, age: undefined }));
    }
  }, [formData.dateOfBirth]);

  // Show loading state while fetching user data
  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6">Loading profile data...</Typography>
        </Paper>
      </Container>
    );
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const newErrors: Partial<Record<keyof UserProfile, string>> = {};

    // Validate required fields
    if (!formData.name?.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.height || formData.height <= 0) {
      newErrors.height = 'Height is required and must be greater than 0';
    }
    if (!formData.weight || formData.weight <= 0) {
      newErrors.weight = 'Weight is required and must be greater than 0';
    }
    if (!formData.gender) {
      newErrors.gender = 'Gender is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Debug logging in development mode
      if (process.env.NODE_ENV === 'development') {
        console.log('Submitting form...');
        console.log('Registration Code (from state):', storedRegistrationCode);
        console.log('Patient ID (from state):', storedPatientId);
        console.log('Form Data:', formData);
      }

      // Determine the API endpoint and method
      let apiUrl;
      let httpMethod;
      let requestBody: Partial<UserProfile> & { registration_code?: string; patient_id?: string };

      if (storedPatientId) {
        // If we have a stored patient ID, update the existing profile
        apiUrl = `/api/patient/${storedPatientId}`;
        httpMethod = 'PUT';
        requestBody = { ...formData, patient_id: storedPatientId };
        console.log(`Attempting to update profile for patient ID: ${storedPatientId}`);
      } else {
        // If no patient ID, create a new profile
        if (!storedRegistrationCode) {
          setErrors({ 
            name: "Cannot create profile: Registration code not found. Please ensure you have a valid registration code from registration."
          });
          console.error('Registration code is missing for new profile creation.');
          return;
        }
        apiUrl = `/api/patient/${storedRegistrationCode}`; // Use registration code in URL for creation
        httpMethod = 'PUT'; // Backend uses PUT for create with code
        requestBody = { ...formData, registration_code: storedRegistrationCode }; // Include in body just in case backend uses it
         console.log(`Attempting to create profile with registration code: ${storedRegistrationCode}`);
      }

      const response = await fetch(apiUrl, {
        method: httpMethod,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        let errorDetail = `Failed to ${storedPatientId ? 'update' : 'create'} profile. Please check your inputs and try again.`;
        try {
          const errorResponse = await response.json();
          if (errorResponse && errorResponse.detail) {
              errorDetail = `Failed to ${storedPatientId ? 'update' : 'create'} profile: ${errorResponse.detail}`;
          } else if (response.status === 404) {
              errorDetail = storedPatientId ? 'Patient not found for update.' : 'Registration code not found or invalid.';
          } else if (response.status === 403) {
               errorDetail = `Not authorized to ${storedPatientId ? 'update' : 'create'} this profile.`;
          } else if (response.status === 409) { // Conflict, e.g., registration code already used
               errorDetail = 'Registration code already used or profile already exists. Please log in.';
          }
        } catch (jsonError) {
            console.error("Failed to parse error response JSON for API error:", jsonError);
        }
        
        console.error(`HTTP Error (${storedPatientId ? 'Update' : 'Create'}): ${response.status} ${response.statusText}`);
        throw new Error(errorDetail);
      }

      const updatedProfile = await response.json();
      console.log('Profile saved successfully.', updatedProfile);
      onSubmit(updatedProfile as UserProfile);
    } catch (error) {
      console.error('Error saving profile:', error);
      
      let errorMessage = 'An unexpected error occurred.';
      if (error instanceof Error) {
          errorMessage = error.message;
      }

      if (errorMessage.includes('401') || errorMessage.toLowerCase().includes('unauthorized') || errorMessage.toLowerCase().includes('token') || errorMessage.toLowerCase().includes('expired')) {
          errorMessage = 'Your session has expired. Please log in again.';
          setTimeout(() => {
            window.location.href = '/login'; 
          }, 3000);
      }

      setErrors({ 
          name: errorMessage
      });
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Create Your Profile
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            Tell us about yourself to get a personalized meal plan
          </Typography>

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  label="Name"
                  value={formData.name}
                  onChange={handleInputChange('name')}
                  error={!!errors.name}
                  helperText={errors.name}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <DatePicker
                  label="Date of Birth"
                  value={
                    formData.dateOfBirth && isValid(parseISO(formData.dateOfBirth))
                      ? parseISO(formData.dateOfBirth)
                      : null
                  }
                  onChange={(date) => {
                    setFormData(prev => ({
                      ...prev,
                      dateOfBirth: date && isValid(date) ? format(date, 'yyyy-MM-dd') : undefined,
                    }));
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Age (Years)"
                  type="number"
                  value={formData.age || []}
                  InputProps={{ readOnly: true, inputProps: { min: 0 } }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth required>
                  <InputLabel>Gender</InputLabel>
                  <Select
                    value={formData.gender}
                    onChange={handleSelectChange('gender')}
                    label="Gender"
                  >
                    {genderOptions.map((option) => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Medical Conditions
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Medical Conditions</InputLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.medicalConditions) ? formData.medicalConditions : []}
                    onChange={handleMultiSelectChange('medicalConditions')}
                    input={<OutlinedInput label="Select Medical Conditions" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    {medicalConditionsOptions.map((condition) => (
                      <MenuItem key={condition} value={condition}>
                        {condition}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Dietary Restrictions
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Dietary Restrictions</InputLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.dietaryRestrictions) ? formData.dietaryRestrictions : []}
                    onChange={handleMultiSelectChange('dietaryRestrictions')}
                    input={<OutlinedInput label="Select Dietary Restrictions" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    {dietaryRestrictionsOptions.map((restriction) => (
                      <MenuItem key={restriction} value={restriction}>
                        {restriction}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Food Preferences
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Food Preferences</InputLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.foodPreferences) ? formData.foodPreferences : []}
                    onChange={handleMultiSelectChange('foodPreferences')}
                    input={<OutlinedInput label="Select Food Preferences" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    {foodPreferencesOptions.map((preference) => (
                      <MenuItem key={preference} value={preference}>
                        {preference}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Allergies
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Allergies</InputLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.allergies) ? formData.allergies : []}
                    onChange={handleMultiSelectChange('allergies')}
                    input={<OutlinedInput label="Select Allergies" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    {allergiesOptions.map((allergy) => (
                      <MenuItem key={allergy} value={allergy}>
                        {allergy}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Vital Signs
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <FormControl fullWidth>
                    <InputLabel>Height Unit</InputLabel>
                    <Select
                      value={heightUnit}
                      onChange={handleHeightUnitChange}
                      label="Height Unit"
                    >
                      <MenuItem value="cm">Centimeters (cm)</MenuItem>
                      <MenuItem value="ft-in">Feet & Inches</MenuItem>
                    </Select>
                  </FormControl>
                  
                  {heightUnit === 'cm' ? (
                    <TextField
                      fullWidth
                      label="Height"
                      type="number"
                      value={formData.height || ''}
                      onChange={(e) => handleHeightChange('cm', e.target.value)}
                      error={!!errors.height}
                      helperText={errors.height}
                      InputProps={{ endAdornment: 'cm' }}
                    />
                  ) : (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <TextField
                        label="Feet"
                        type="number"
                        value={heightFeet}
                        onChange={(e) => handleHeightChange('feet', e.target.value)}
                        error={!!errors.height}
                        sx={{ width: '100px' }}
                      />
                      <TextField
                        label="Inches"
                        type="number"
                        value={heightInches}
                        onChange={(e) => handleHeightChange('inches', e.target.value)}
                        error={!!errors.height}
                        sx={{ width: '100px' }}
                      />
                    </Box>
                  )}
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <FormControl fullWidth>
                    <InputLabel>Weight Unit</InputLabel>
                    <Select
                      value={weightUnit}
                      onChange={handleWeightUnitChange}
                      label="Weight Unit"
                    >
                      <MenuItem value="kg">Kilograms (kg)</MenuItem>
                      <MenuItem value="lbs">Pounds (lbs)</MenuItem>
                    </Select>
                  </FormControl>
                  
                  <TextField
                    fullWidth
                    label="Weight"
                    type="number"
                    value={formData.weight || ''}
                    onChange={(e) => {
                      const value = e.target.value === '' ? undefined : Number(e.target.value);
                      setFormData(prev => ({ ...prev, weight: value }));
                    }}
                    error={!!errors.weight}
                    helperText={errors.weight}
                    InputProps={{ endAdornment: weightUnit }}
                  />
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="BMI"
                  value={calculateBMI()}
                  InputProps={{ 
                    readOnly: true,
                    endAdornment: 'kg/m²'
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <FormControl fullWidth>
                    <InputLabel>Waist Unit</InputLabel>
                    <Select
                      value={waistUnit}
                      onChange={handleWaistUnitChange}
                      label="Waist Unit"
                    >
                      <MenuItem value="cm">Centimeters (cm)</MenuItem>
                      <MenuItem value="in">Inches (in)</MenuItem>
                    </Select>
                  </FormControl>
                  
                  <TextField
                    fullWidth
                    label="Waist Circumference"
                    type="number"
                    value={formData.waistCircumference || ''}
                    onChange={(e) => {
                      const value = e.target.value === '' ? undefined : Number(e.target.value);
                      setFormData(prev => ({ ...prev, waistCircumference: value }));
                    }}
                    InputProps={{ 
                      endAdornment: waistUnit,
                      inputProps: { 
                        min: waistUnit === 'cm' ? 50 : 20,
                        max: waistUnit === 'cm' ? 200 : 80 
                      }
                    }}
                  />
                </Box>
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Systolic BP"
                  type="number"
                  value={formData.systolicBP || ''}
                  onChange={handleInputChange('systolicBP')}
                  InputProps={{ inputProps: { min: 60, max: 250 } }}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Diastolic BP"
                  type="number"
                  value={formData.diastolicBP || ''}
                  onChange={handleInputChange('diastolicBP')}
                  InputProps={{ inputProps: { min: 40, max: 150 } }}
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Heart Rate (bpm)"
                  type="number"
                  value={formData.heartRate || ''}
                  onChange={handleInputChange('heartRate')}
                  InputProps={{ inputProps: { min: 40, max: 200 } }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Ethnicity</InputLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.ethnicity) ? formData.ethnicity : []}
                    onChange={handleMultiSelectChange('ethnicity')}
                    input={<OutlinedInput label="Ethnicity" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                    label="Ethnicity"
                  >
                    {ethnicities.map((ethnicity) => (
                      <MenuItem key={ethnicity} value={ethnicity}>
                        {ethnicity}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Calories Target</InputLabel>
                  <Select
                    value={formData.calorieTarget}
                    onChange={handleSelectChange('calorieTarget')}
                    label="Calories Target"
                  >
                    {calorieTargets.map((calories) => (
                      <MenuItem key={calories} value={calories}>
                        {calories} kcal
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.wantsWeightLoss}
                      onChange={(e) => setFormData(prev => ({ ...prev, wantsWeightLoss: e.target.checked }))}
                    />
                  }
                  label="Patient wants weight loss"
                />
              </Grid>

              <Grid item xs={12} sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Most Recent Lab Values (Optional)
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>A1C</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.a1c || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, a1c: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>%</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>Fasting Glucose</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.fastingGlucose || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, fastingGlucose: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>mmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>LDL-C</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.ldl || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, ldl: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>mmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>HDL-C</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.hdl || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, hdl: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>mmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>Triglycerides</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.triglycerides || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, triglycerides: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>mmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>eGFR</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.egfr || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, egfr: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}></TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>Creatinine</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.creatinine || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, creatinine: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>µmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>Potassium</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.potassium || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, potassium: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>mmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>ALT</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.alt || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, alt: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}></TableCell>
                      </TableRow>
                       <TableRow>
                        <TableCell>AST</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.ast || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, ast: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}></TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>Vitamin D</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.vitaminD || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, vitaminD: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>nmol/L</TableCell>
                      </TableRow>

                      <TableRow>
                        <TableCell>B12</TableCell>
                        <TableCell sx={{ width: '150px' }}>
                          <TextField
                            fullWidth
                            type="number"
                            value={formData.labValues?.b12 || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              labValues: { ...prev.labValues, b12: e.target.value === '' ? undefined : Number(e.target.value) }
                            }))}
                            InputProps={{ inputProps: { min: 0, step: 0.1 } }}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" sx={{ width: '80px' }}>pmol/L</TableCell>
                      </TableRow>

                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              <Grid item xs={12} sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Physical Activity Profile
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Work Activity Level</FormLabel>
                  <RadioGroup
                    row
                    name="workActivityLevel"
                    value={formData.workActivityLevel || ''}
                    onChange={(e) => handleSelectChange('workActivityLevel')(e as any)}
                  >
                    {workActivityLevelOptions.map((option) => (
                      <FormControlLabel
                        key={option}
                        value={option}
                        control={<Radio />}
                        label={option}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Exercise Frequency</FormLabel>
                  <RadioGroup
                    row
                    name="exerciseFrequency"
                    value={formData.exerciseFrequency || ''}
                    onChange={(e) => handleSelectChange('exerciseFrequency')(e as any)}
                  >
                    {exerciseFrequencyOptions.map((option) => (
                      <FormControlLabel
                        key={option}
                        value={option}
                        control={<Radio />}
                        label={option}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel id="exercise-types-label">Exercise Types</InputLabel>
                  <Select
                    labelId="exercise-types-label"
                    multiple
                    value={Array.isArray(formData.exerciseTypes) ? formData.exerciseTypes : []}
                    onChange={handleMultiSelectChange('exerciseTypes')}
                    input={<OutlinedInput label="Exercise Types" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                    label="Exercise Types"
                  >
                    {exerciseTypesOptions.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Joint Issues</FormLabel>
                  <RadioGroup
                    row
                    name="jointIssues"
                    value={formData.jointIssues === true ? 'Yes' : formData.jointIssues === false ? 'No' : ''}
                    onChange={(e) => {
                      const value = e.target.value;
                      setFormData(prev => ({
                        ...prev,
                        jointIssues: value === 'Yes' ? true : value === 'No' ? false : undefined
                      }));
                    }}
                  >
                    <FormControlLabel value="Yes" control={<Radio />} label="Yes" />
                    <FormControlLabel value="No" control={<Radio />} label="No" />
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12} sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Lifestyle & Preferences
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Type of Diet</InputLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.dietType) ? formData.dietType : []}
                    onChange={handleMultiSelectChange('dietType')}
                    input={<OutlinedInput label="Type of Diet" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                    onFocus={() => setShowDietFeatures(true)}
                    onClick={() => setShowDietFeatures(true)}
                  >
                    {dietTypeOptions.map((type) => (
                      <MenuItem key={type} value={type}>
                        {type}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {(formData.dietType || []).includes('Other') && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Other Diet Type"
                    value={formData.otherDietType || ''}
                    onChange={handleInputChange('otherDietType')}
                    placeholder="Please specify"
                  />
                </Grid>
              )}

              {showDietFeatures && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                    Current Dietary Features (select all that apply)
                  </Typography>
                  <FormControl fullWidth>
                    <InputLabel id="diet-features-label">Select Dietary Features</InputLabel>
                    <Select
                      labelId="diet-features-label"
                      multiple
                      value={Array.isArray(formData.dietFeatures) ? formData.dietFeatures : []}
                      onChange={handleMultiSelectChange('dietFeatures')}
                      input={<OutlinedInput label="Select Dietary Features" />}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(Array.isArray(selected) ? selected : []).map((value) => (
                            <Chip key={value} label={value} />
                          ))}
                        </Box>
                      )}
                    >
                      {dietFeaturesOptions.map((feature) => (
                        <MenuItem key={feature} value={feature}>
                          {feature}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      fullWidth
                      label="Food Allergies (specify)"
                      value={formData.foodAllergiesCustom || ''}
                      onChange={handleInputChange('foodAllergiesCustom')}
                      placeholder="e.g., Peanuts, Shellfish"
                    />
                    <TextField
                      fullWidth
                      label="Strong Dislikes (specify)"
                      value={formData.strongDislikesCustom || ''}
                      onChange={handleInputChange('strongDislikesCustom')}
                      placeholder="e.g., Tofu, Cilantro"
                    />
                  </Box>
                </Grid>
              )}

              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Meal Prep</FormLabel>
                  <RadioGroup
                    row
                    name="mealPrep"
                    value={formData.mealPrep || ''}
                    onChange={(e) => handleSelectChange('mealPrep')(e as any)}
                  >
                    {mealPrepOptions.map((option) => (
                      <FormControlLabel
                        key={option}
                        value={option}
                        control={<Radio />}
                        label={option}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel id="appliances-label">Appliances</InputLabel>
                  <Select
                    labelId="appliances-label"
                    multiple
                    value={Array.isArray(formData.appliances) ? formData.appliances : []}
                    onChange={handleMultiSelectChange('appliances')}
                    input={<OutlinedInput label="Appliances" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                    label="Appliances"
                  >
                    {appliancesOptions.map((appliance) => (
                      <MenuItem key={appliance} value={appliance}>
                        {appliance}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Eating Schedule</FormLabel>
                  <RadioGroup
                    row
                    name="eatingSchedule"
                    value={formData.eatingSchedule || ''}
                    onChange={(e) => handleSelectChange('eatingSchedule')(e as any)}
                  >
                    {eatingScheduleOptions.map((option) => (
                      <FormControlLabel
                        key={option}
                        value={option}
                        control={<Radio />}
                        label={option}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12} sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Goals & Readiness to Change
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Goals</FormLabel>
                  <Select
                    multiple
                    value={Array.isArray(formData.goals) ? formData.goals : []}
                    onChange={handleMultiSelectChange('goals')}
                    input={<OutlinedInput label="Goals" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(Array.isArray(selected) ? selected : []).map((value) => (
                          <Chip key={value} label={value} />
                        ))}
                      </Box>
                    )}
                  >
                    {goalsOptions.map((goal) => (
                      <MenuItem key={goal} value={goal}>
                        <Checkbox checked={(formData.goals || []).indexOf(goal) > -1} />
                        {goal}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Readiness to Change</FormLabel>
                  <RadioGroup
                    row
                    name="readinessToChange"
                    value={formData.readinessToChange || ''}
                    onChange={(e) => handleSelectChange('readinessToChange')(e as any)}
                  >
                    {readinessToChangeOptions.map((option) => (
                      <FormControlLabel
                        key={option}
                        value={option}
                        control={<Radio />}
                        label={option}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    size="large"
                  >
                    Generate Meal Plan
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      </Container>
    </LocalizationProvider>
  );
};

export default UserProfileForm; 