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

interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  initialProfile?: UserProfile;
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ onSubmit, initialProfile }) => {
  const [formData, setFormData] = useState<Partial<UserProfile>>(() => {
    if (initialProfile) {
      return initialProfile;
    }
    return {
      name: '',
      age: undefined,
      gender: '',
      weight: undefined,
      height: undefined,
      waistCircumference: undefined,
      systolicBP: undefined,
      diastolicBP: undefined,
      heartRate: undefined,
      ethnicity: '',
      dietType: '',
      calorieTarget: '',
      dietFeatures: [],
      medicalConditions: [],
      wantsWeightLoss: false,
      dietaryRestrictions: [],
      healthConditions: [],
      foodPreferences: [],
      allergies: [],
    };
  });

  const [heightUnit, setHeightUnit] = useState<'cm' | 'ft-in'>('cm');
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lbs'>('kg');
  const [waistUnit, setWaistUnit] = useState<'cm' | 'in'>('cm');
  const [heightFeet, setHeightFeet] = useState<number | ''>('');
  const [heightInches, setHeightInches] = useState<number | ''>('');
  const [errors, setErrors] = useState<Partial<Record<keyof UserProfile, string>>>({});
  const [loadingProfile, setLoadingProfile] = useState(false);

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

  useEffect(() => {
    const fetchProfile = async () => {
      setLoadingProfile(true);
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const response = await fetch('http://localhost:8000/user/profile', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (response.ok) {
          const data = await response.json();
          if (data && Object.keys(data).length > 0) {
            setFormData(data);
          }
        }
      } catch (err) {
        // ignore
      } finally {
        setLoadingProfile(false);
      }
    };
    fetchProfile();
  }, []);

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
      // Save profile to backend
      const token = localStorage.getItem('token');
      if (token) {
        await fetch('http://localhost:8000/user/profile', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ profile: formData }),
        });
      }
      onSubmit(formData as UserProfile);
    } catch (error) {
      console.error('Error creating profile:', error);
      setErrors({
        name: 'Failed to generate meal plan. Please check your inputs and try again.'
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
                <InputLabel>Type of Diet</InputLabel>
                <Select
                  value={formData.dietType}
                  onChange={handleSelectChange('dietType')}
                  label="Type of Diet"
                >
                  {dietTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
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
                    onChange={(e) => setFormData(prev => ({ ...prev, wantsWeightLoss: e.target.checked }))}
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