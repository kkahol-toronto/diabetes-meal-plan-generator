import React, { useState, useEffect, useCallback } from 'react';
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
} from '@mui/material';
import { UserProfile } from '../types';

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
const healthConditionsOptions = [
  'Diabetes',
  'Hypertension',
  'Celiac Disease',
  'Heart Disease',
  'Kidney Disease',
  'High Cholesterol',
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

// Helper to safely parse optional numeric fields from various input types
const parseOptionalNumber = (value: any): number | undefined => {
  if (value === null || value === undefined || value === '') {
    return undefined;
  }
  const num = Number(value);
  return isNaN(num) ? undefined : num;
};

interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  initialProfile?: UserProfile;
  onProfileChange: (profile: Partial<UserProfile>) => void;
}

function toSnakeCase(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(toSnakeCase);
  } else if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [
        key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`),
        toSnakeCase(value)
      ])
    );
  }
  return obj;
}

// Convert height from cm to feet/inches, ensuring correct return types
const convertHeightToFtIn = (cm: number | undefined | null): { feet: number | ''; inches: number | '' } => {
  if (typeof cm !== 'number' || isNaN(cm)) return { feet: '', inches: '' };
  const totalInches = cm / 2.54;
  const feet = Math.floor(totalInches / 12);
  const inches = Math.round(totalInches % 12);
  return { feet, inches };
};

// Ensure createDefaultProfile provides valid numbers for non-optional fields
const createDefaultProfile = (): UserProfile => ({
  name: '',
  age: 0, // Default to 0 for non-optional number
  gender: '',
  weight: 0, // Default to 0 for non-optional number
  height: 0, // Default to 0 for non-optional number
  waistCircumference: undefined,
  systolicBP: undefined,
  diastolicBP: undefined,
  heartRate: undefined,
  ethnicity: '',
  dietTypes: [],
  calorieTarget: '2000',
  dietFeatures: [],
  medicalConditions: [],
  otherMedicalCondition: '',
  wantsWeightLoss: false,
  dietaryRestrictions: [],
  otherDietaryRestriction: '',
  healthConditions: [],
  otherHealthCondition: '',
  foodPreferences: [],
  otherFoodPreference: '',
  allergies: [],
  otherAllergy: '',
});

const UserProfileForm: React.FC<UserProfileFormProps> = ({ onSubmit, initialProfile, onProfileChange }) => {
  const [formData, setFormData] = useState<Partial<UserProfile>>(() => {
    const defaultP = createDefaultProfile();
    if (initialProfile) {
      return { 
        ...defaultP, 
        ...initialProfile,
        // Ensure non-optional numbers default to a number if parsing fails
        age: parseOptionalNumber(initialProfile.age) ?? defaultP.age, 
        weight: parseOptionalNumber(initialProfile.weight) ?? defaultP.weight,
        height: parseOptionalNumber(initialProfile.height) ?? defaultP.height,
        // Optional numbers are fine with undefined
        waistCircumference: parseOptionalNumber(initialProfile.waistCircumference),
        systolicBP: parseOptionalNumber(initialProfile.systolicBP),
        diastolicBP: parseOptionalNumber(initialProfile.diastolicBP),
        heartRate: parseOptionalNumber(initialProfile.heartRate),
        // Arrays and booleans
        medicalConditions: initialProfile.medicalConditions || [],
        dietaryRestrictions: initialProfile.dietaryRestrictions || [],
        healthConditions: initialProfile.healthConditions || [],
        foodPreferences: initialProfile.foodPreferences || [],
        allergies: initialProfile.allergies || [],
        dietTypes: initialProfile.dietTypes || [],
        dietFeatures: initialProfile.dietFeatures || [],
        wantsWeightLoss: typeof initialProfile.wantsWeightLoss === 'boolean' ? initialProfile.wantsWeightLoss : false,
        // Strings
        name: initialProfile.name || defaultP.name,
        gender: initialProfile.gender || defaultP.gender,
        ethnicity: initialProfile.ethnicity || defaultP.ethnicity,
        calorieTarget: initialProfile.calorieTarget || defaultP.calorieTarget,
        otherMedicalCondition: initialProfile.otherMedicalCondition || defaultP.otherMedicalCondition,
        otherDietaryRestriction: initialProfile.otherDietaryRestriction || defaultP.otherDietaryRestriction,
        otherHealthCondition: initialProfile.otherHealthCondition || defaultP.otherHealthCondition,
        otherFoodPreference: initialProfile.otherFoodPreference || defaultP.otherFoodPreference,
        otherAllergy: initialProfile.otherAllergy || defaultP.otherAllergy,
      };
    }
    return defaultP;
  });

  const [heightUnit, setHeightUnit] = useState<'cm' | 'ft-in'>('cm');
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lbs'>('kg');
  const [waistUnit, setWaistUnit] = useState<'cm' | 'in'>('cm');
  
  // Correctly initialize heightFeet and heightInches with type guards
  const getInitialHeightFeet = () => {
    if (initialProfile?.height && heightUnit === 'ft-in') {
      const converted = convertHeightToFtIn(initialProfile.height);
      return typeof converted.feet === 'number' ? converted.feet : '';
    }
    return '';
  };
  const getInitialHeightInches = () => {
    if (initialProfile?.height && heightUnit === 'ft-in') {
      const converted = convertHeightToFtIn(initialProfile.height);
      return typeof converted.inches === 'number' ? converted.inches : '';
    }
    return '';
  };

  const [heightFeet, setHeightFeet] = useState<number | ''>(getInitialHeightFeet());
  const [heightInches, setHeightInches] = useState<number | ''>(getInitialHeightInches());
  const [errors, setErrors] = useState<Partial<Record<keyof UserProfile, string>>>({});

  // Effect to synchronize formData with initialProfile changes from parent
  useEffect(() => {
    const defaultP = createDefaultProfile();
    let profileToSet: UserProfile = defaultP;

    if (initialProfile) {
      profileToSet = {
        ...defaultP, 
        ...initialProfile,
        // Ensure non-optional numbers default to a number if parsing fails
        age: parseOptionalNumber(initialProfile.age) ?? defaultP.age,
        weight: parseOptionalNumber(initialProfile.weight) ?? defaultP.weight,
        height: parseOptionalNumber(initialProfile.height) ?? defaultP.height,
        // Optional numbers are fine with undefined
        waistCircumference: parseOptionalNumber(initialProfile.waistCircumference),
        systolicBP: parseOptionalNumber(initialProfile.systolicBP),
        diastolicBP: parseOptionalNumber(initialProfile.diastolicBP),
        heartRate: parseOptionalNumber(initialProfile.heartRate),
        // Arrays and booleans
        medicalConditions: initialProfile.medicalConditions || [],
        dietaryRestrictions: initialProfile.dietaryRestrictions || [],
        healthConditions: initialProfile.healthConditions || [],
        foodPreferences: initialProfile.foodPreferences || [],
        allergies: initialProfile.allergies || [],
        dietTypes: initialProfile.dietTypes || [],
        dietFeatures: initialProfile.dietFeatures || [],
        wantsWeightLoss: typeof initialProfile.wantsWeightLoss === 'boolean' ? initialProfile.wantsWeightLoss : false,
        // Strings
        name: initialProfile.name || defaultP.name,
        gender: initialProfile.gender || defaultP.gender,
        ethnicity: initialProfile.ethnicity || defaultP.ethnicity,
        calorieTarget: initialProfile.calorieTarget || defaultP.calorieTarget,
        otherMedicalCondition: initialProfile.otherMedicalCondition || defaultP.otherMedicalCondition,
        otherDietaryRestriction: initialProfile.otherDietaryRestriction || defaultP.otherDietaryRestriction,
        otherHealthCondition: initialProfile.otherHealthCondition || defaultP.otherHealthCondition,
        otherFoodPreference: initialProfile.otherFoodPreference || defaultP.otherFoodPreference,
        otherAllergy: initialProfile.otherAllergy || defaultP.otherAllergy,
      };
    }

    if (JSON.stringify(formData) !== JSON.stringify(profileToSet)) {
      setFormData(profileToSet as Partial<UserProfile>); // Cast to Partial as formData is Partial
    }
  }, [initialProfile]);

  // Effect to update UI states like heightFeet, heightInches when formData.height or heightUnit changes
  useEffect(() => {
    const { feet, inches } = convertHeightToFtIn(formData.height);
    if (heightUnit === 'ft-in') {
      setHeightFeet(feet);
      setHeightInches(inches);
    } else {
      setHeightFeet(''); 
      setHeightInches('');
    }
  }, [formData.height, heightUnit]);
  
  // Centralized change handler
  const handleChange = useCallback((field: keyof UserProfile, value: any) => {
    setFormData(prevFormData => {
      const updatedFormData = { ...prevFormData, [field]: value };
      onProfileChange(updatedFormData); // Notify parent (MealPlanRequest)
      return updatedFormData;
    });
  }, [onProfileChange]);

  const handleInputChange = (field: keyof UserProfile) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const value = event.target.type === 'checkbox' ? (event.target as HTMLInputElement).checked : event.target.value;
    handleChange(field, value);
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSelectChange = (field: keyof UserProfile) => (
    event: SelectChangeEvent<string | string[]>
  ) => {
    handleChange(field, event.target.value);
  };
  
  const handleMultiSelectChange = (field: keyof UserProfile) => (
    event: SelectChangeEvent<string[]>
  ) => {
    const value = event.target.value as string[];
    handleChange(field, value || []);
  };
  
  const handleSwitchChange = (field: keyof UserProfile) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    handleChange(field, event.target.checked);
  };

  // Convert height from feet/inches to cm
  const convertHeightToCm = (feet: number, inches: number) => {
    return Math.round((feet * 30.48) + (inches * 2.54));
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
      handleChange('weight', newWeight);
    }
  };

  const handleHeightChange = (type: 'feet' | 'inches' | 'cm', value: string) => {
    let newHeightCm: number | undefined;
    if (heightUnit === 'cm') {
      newHeightCm = value === '' ? undefined : Number(value);
      handleChange('height', newHeightCm);
    } else {
      const numValue = value === '' ? '' : Number(value);
      let currentFeet = heightFeet;
      let currentInches = heightInches;
      if (type === 'feet') {
        setHeightFeet(numValue);
        currentFeet = numValue;
      } else {
        setHeightInches(numValue);
        currentInches = numValue;
      }
      if (typeof currentFeet === 'number' && typeof currentInches === 'number') {
        newHeightCm = convertHeightToCm(currentFeet, currentInches);
        handleChange('height', newHeightCm);
      }
    }
  };

  const handleWaistUnitChange = (event: SelectChangeEvent<'cm' | 'in'>) => {
    const newUnit = event.target.value as 'cm' | 'in';
    setWaistUnit(newUnit);
    
    if (formData.waistCircumference) {
      const newWaist = convertWaist(formData.waistCircumference, waistUnit, newUnit);
      handleChange('waistCircumference', newWaist);
    }
  };

  const calculateBMI = () => {
    // Guard against undefined or 0 for height/weight before calculation
    if (formData.height && formData.weight && formData.height > 0 && formData.weight > 0) {
      const heightInMeters = formData.height / 100;
      const weightInKg = weightUnit === 'lbs' ? formData.weight / 2.20462 : formData.weight;
      return (weightInKg / (heightInMeters * heightInMeters)).toFixed(1);
    }
    return '';
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const newErrors: Partial<Record<keyof UserProfile, string>> = {};

    // Validate required fields
    if (!formData.name?.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.dietTypes || formData.dietTypes.length === 0) {
      newErrors.dietTypes = 'At least one diet type is required';
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
      // Always save to localStorage before submitting
      localStorage.setItem('userProfile', JSON.stringify(formData));
      
      // Save to backend
      const token = localStorage.getItem('token');
      const snakeCaseProfile = toSnakeCase(formData);
      if (token) {
        const response = await fetch('http://localhost:8000/user/profile', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ profile: snakeCaseProfile }),
        });

        if (!response.ok) {
          throw new Error('Failed to save profile to backend');
        }
      }

      // Call onSubmit with the profile data
      onSubmit(snakeCaseProfile as UserProfile);
    } catch (error) {
      console.error('Error saving profile:', error);
      setErrors({
        name: 'Failed to save profile. Please try again.'
      });
    }
  };

  return (
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
              <TextField
                fullWidth
                required
                label="Age (Years)"
                type="number"
                value={formData.age || ''}
                onChange={handleInputChange('age')}
                InputProps={{ inputProps: { min: 1, max: 120 } }}
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
                  value={formData.medicalConditions || []}
                  onChange={handleMultiSelectChange('medicalConditions')}
                  input={<OutlinedInput label="Select Medical Conditions" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} />
                      ))}
                    </Box>
                  )}
                >
                  {medicalConditions.map((condition) => (
                    <MenuItem key={condition} value={condition}>
                      {condition}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {formData.medicalConditions?.includes('Other') && (
                <TextField
                  fullWidth
                  label="Please specify other medical condition"
                  value={formData.otherMedicalCondition || ''}
                  onChange={(e) => {
                    handleChange('otherMedicalCondition', e.target.value);
                  }}
                  sx={{ mt: 2 }}
                />
              )}
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Dietary Restrictions
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Select Dietary Restrictions</InputLabel>
                <Select
                  multiple
                  value={formData.dietaryRestrictions || []}
                  onChange={handleMultiSelectChange('dietaryRestrictions')}
                  input={<OutlinedInput label="Select Dietary Restrictions" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
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
              {formData.dietaryRestrictions?.includes('Other') && (
                <TextField
                  fullWidth
                  label="Please specify other dietary restriction"
                  value={formData.otherDietaryRestriction || ''}
                  onChange={(e) => {
                    handleChange('otherDietaryRestriction', e.target.value);
                  }}
                  sx={{ mt: 2 }}
                />
              )}
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Health Conditions
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Select Health Conditions</InputLabel>
                <Select
                  multiple
                  value={formData.healthConditions || []}
                  onChange={handleMultiSelectChange('healthConditions')}
                  input={<OutlinedInput label="Select Health Conditions" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} />
                      ))}
                    </Box>
                  )}
                >
                  {healthConditionsOptions.map((condition) => (
                    <MenuItem key={condition} value={condition}>
                      {condition}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {formData.healthConditions?.includes('Other') && (
                <TextField
                  fullWidth
                  label="Please specify other health condition"
                  value={formData.otherHealthCondition || ''}
                  onChange={(e) => {
                    handleChange('otherHealthCondition', e.target.value);
                  }}
                  sx={{ mt: 2 }}
                />
              )}
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Food Preferences
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Select Food Preferences</InputLabel>
                <Select
                  multiple
                  value={formData.foodPreferences || []}
                  onChange={handleMultiSelectChange('foodPreferences')}
                  input={<OutlinedInput label="Select Food Preferences" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
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
              {formData.foodPreferences?.includes('Other') && (
                <TextField
                  fullWidth
                  label="Please specify other food preference"
                  value={formData.otherFoodPreference || ''}
                  onChange={(e) => {
                    handleChange('otherFoodPreference', e.target.value);
                  }}
                  sx={{ mt: 2 }}
                />
              )}
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Allergies
              </Typography>
              <FormControl fullWidth>
                <InputLabel>Select Allergies</InputLabel>
                <Select
                  multiple
                  value={formData.allergies || []}
                  onChange={handleMultiSelectChange('allergies')}
                  input={<OutlinedInput label="Select Allergies" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
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
              {formData.allergies?.includes('Other') && (
                <TextField
                  fullWidth
                  label="Please specify other allergy"
                  value={formData.otherAllergy || ''}
                  onChange={(e) => {
                    handleChange('otherAllergy', e.target.value);
                  }}
                  sx={{ mt: 2 }}
                />
              )}
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
                    handleChange('weight', value);
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
                    handleChange('waistCircumference', value);
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
                  value={formData.ethnicity}
                  onChange={handleSelectChange('ethnicity')}
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
                <InputLabel id="diet-types-label">Type of Diet</InputLabel>
                <Select
                  labelId="diet-types-label"
                  multiple
                  value={formData.dietTypes || []}
                  onChange={handleMultiSelectChange('dietTypes')}
                  input={<OutlinedInput label="Type of Diet" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} />
                      ))}
                    </Box>
                  )}
                >
                  {dietTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
                {errors.dietTypes && <FormHelperText error>{errors.dietTypes}</FormHelperText>}
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
              <FormControl fullWidth>
                <InputLabel>Features of Diet</InputLabel>
                <Select
                  multiple
                  value={formData.dietFeatures || []}
                  onChange={handleMultiSelectChange('dietFeatures')}
                  input={<OutlinedInput label="Features of Diet" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} />
                      ))}
                    </Box>
                  )}
                >
                  {dietFeatures.map((feature) => (
                    <MenuItem key={feature} value={feature}>
                      {feature}
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
                    onChange={handleSwitchChange('wantsWeightLoss')}
                  />
                }
                label="Patient wants weight loss"
              />
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
  );
};

export default UserProfileForm; 