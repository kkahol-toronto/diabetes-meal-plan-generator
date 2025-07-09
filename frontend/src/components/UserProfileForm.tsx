import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Select,
  MenuItem,
  Card,
  CardContent,
  Grid,
  Chip,
  Autocomplete,
  InputAdornment,
  Divider,
  Alert,
  Paper,
  useTheme,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  RadioGroup,
  Radio,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PersonIcon from '@mui/icons-material/Person';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import MedicationIcon from '@mui/icons-material/Medication';
import ScienceIcon from '@mui/icons-material/Science';
import FavoriteIcon from '@mui/icons-material/Favorite';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import FitnessIcon from '@mui/icons-material/FitnessCenter';
import HomeIcon from '@mui/icons-material/Home';
import TrackChangesIcon from '@mui/icons-material/TrackChanges';
import { UserProfile } from '../types';

interface UserProfileFormProps {
  onSubmit: (profile: UserProfile) => void;
  initialProfile?: UserProfile;
  submitButtonText?: string;
  isAdminMode?: boolean;
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ 
  onSubmit, 
  initialProfile, 
  submitButtonText = "🚀 Generate My Personalized Meal Plan",
  isAdminMode = false 
}) => {
  const theme = useTheme();
  
  // Normalize profile data to handle old format
  const normalizeProfile = (profileData: any): Partial<UserProfile> => {
    if (!profileData) return {};
    
    const normalized = { ...profileData };
    
    // Convert old string fields to arrays
    if (typeof normalized.ethnicity === 'string') {
      normalized.ethnicity = normalized.ethnicity ? [normalized.ethnicity] : [];
    }
    if (typeof normalized.dietType === 'string') {
      normalized.dietType = normalized.dietType ? [normalized.dietType] : [];
    }
    if (typeof normalized.medicalConditions === 'string') {
      normalized.medicalConditions = normalized.medicalConditions ? [normalized.medicalConditions] : [];
    }
    if (typeof normalized.dietaryFeatures === 'string') {
      normalized.dietaryFeatures = normalized.dietaryFeatures ? [normalized.dietaryFeatures] : [];
    }
    if (typeof normalized.dietFeatures === 'string') {
      normalized.dietaryFeatures = normalized.dietFeatures ? [normalized.dietFeatures] : [];
    }
    
    // Ensure arrays exist
    normalized.ethnicity = normalized.ethnicity || [];
    normalized.dietType = normalized.dietType || [];
    normalized.medicalConditions = normalized.medicalConditions || [];
    normalized.currentMedications = normalized.currentMedications || [];
    normalized.dietaryFeatures = normalized.dietaryFeatures || [];
    normalized.dietaryRestrictions = normalized.dietaryRestrictions || [];
    normalized.foodPreferences = normalized.foodPreferences || [];
    normalized.allergies = normalized.allergies || [];
    normalized.strongDislikes = normalized.strongDislikes || [];
    normalized.exerciseTypes = normalized.exerciseTypes || [];
    normalized.availableAppliances = normalized.availableAppliances || [];
    normalized.primaryGoals = normalized.primaryGoals || [];
    
    return normalized;
  };

  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    dateOfBirth: '',
    age: undefined,
    gender: '',
    ethnicity: [],
    medicalConditions: [],
    currentMedications: [],
    labValues: {},
    height: 0,
    weight: 0,
    bmi: undefined,
    waistCircumference: undefined,
    systolicBP: undefined,
    diastolicBP: undefined,
    heartRate: undefined,
    dietType: [],
    dietaryFeatures: [],
    dietaryRestrictions: [],
    foodPreferences: [],
    allergies: [],
    strongDislikes: [],
    workActivityLevel: '',
    exerciseFrequency: '',
    exerciseTypes: [],
    mobilityIssues: false,
    mealPrepCapability: '',
    availableAppliances: [],
    eatingSchedule: '',
    primaryGoals: [],
    readinessToChange: '',
    wantsWeightLoss: false,
    calorieTarget: '',
    ...normalizeProfile(initialProfile),
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // State for "Other" text inputs
  const [otherValues, setOtherValues] = useState({
    ethnicity: '',
    medicalConditions: '',
    medications: '',
    dietType: '',
    exerciseTypes: '',
    appliances: '',
    goals: '',
    eatingSchedule: '',
    calorieTarget: '',
  });

  // Auto-calculate age from date of birth
  useEffect(() => {
    if (profile.dateOfBirth) {
      const today = new Date();
      const birthDate = new Date(profile.dateOfBirth);
      const age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        setProfile(prev => ({ ...prev, age: age - 1 }));
      } else {
        setProfile(prev => ({ ...prev, age }));
      }
    }
  }, [profile.dateOfBirth]);

  // Auto-calculate BMI
  useEffect(() => {
    if (profile.height && profile.weight && profile.height > 0 && profile.weight > 0) {
      const heightInMeters = profile.height / 100;
      const bmi = profile.weight / (heightInMeters * heightInMeters);
      setProfile(prev => ({ ...prev, bmi: Math.round(bmi * 10) / 10 }));
    }
  }, [profile.height, profile.weight]);

  // Auto-save functionality
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem('userProfile', JSON.stringify(profile));
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [profile]);

  // Load saved profile on mount
  useEffect(() => {
    if (!initialProfile) {
      const savedProfile = localStorage.getItem('userProfile');
      if (savedProfile) {
        try {
          const parsed = JSON.parse(savedProfile);
          setProfile(prev => ({ ...prev, ...normalizeProfile(parsed) }));
        } catch (error) {
          console.error('Error loading saved profile:', error);
        }
      }
    }
  }, [initialProfile]);

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    setProfile(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleLabValueChange = (field: string, value: string) => {
    setProfile(prev => ({
      ...prev,
      labValues: { ...prev.labValues, [field]: value }
    }));
  };

  const handleArrayChange = (field: keyof UserProfile, value: string, checked: boolean) => {
    const currentValue = profile[field];
    let currentArray: string[] = [];
    
    // Ensure we always work with an array
    if (Array.isArray(currentValue)) {
      currentArray = currentValue;
    } else if (typeof currentValue === 'string' && currentValue) {
      currentArray = [currentValue];
    }
    
    const newArray = checked
      ? [...currentArray, value]
      : currentArray.filter(item => item !== value);
    
    setProfile(prev => ({ ...prev, [field]: newArray }));
  };

  const handleOtherChange = (field: string, value: string) => {
    setOtherValues(prev => ({ ...prev, [field]: value }));
  };

  const addOtherOption = (profileField: keyof UserProfile, otherField: string) => {
    const otherValue = otherValues[otherField as keyof typeof otherValues];
    
    if (otherValue && otherValue.trim()) {
      const currentArray = (profile[profileField] as string[]) || [];
      
      // Remove any existing "Other:" entries and add the new one
      const filteredArray = currentArray.filter(item => !item.startsWith('Other:'));
      const newArray = [...filteredArray, `Other: ${otherValue.trim()}`];
      
      setProfile(prev => ({ ...prev, [profileField]: newArray }));
      
      // Clear the input field
      setOtherValues(prev => ({ ...prev, [otherField]: '' }));
    }
  };

  const getBMICategory = (bmi: number): string => {
    if (bmi < 18.5) return '(Underweight)';
    if (bmi < 25) return '(Normal)';
    if (bmi < 30) return '(Overweight)';
    return '(Obese)';
  };

  const getBMIColor = (bmi: number): string => {
    if (bmi < 18.5) return '#2196f3'; // Blue
    if (bmi < 25) return '#4caf50'; // Green
    if (bmi < 30) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    // For admin mode, validation is more relaxed - only name is required
    if (isAdminMode) {
      if (!profile.name?.trim()) {
        newErrors.name = 'Patient name is required';
      }
    } else {
      // For patient mode, more strict validation
      if (!profile.name?.trim()) {
        newErrors.name = 'Full name is required';
      }
      
      if (!profile.height || profile.height <= 0) {
        newErrors.height = 'Please enter a valid height (e.g., 170 cm)';
      } else if (profile.height < 100 || profile.height > 250) {
        newErrors.height = 'Height should be between 100-250 cm';
      }
      
      if (!profile.weight || profile.weight <= 0) {
        newErrors.weight = 'Please enter a valid weight (e.g., 70 kg)';
      } else if (profile.weight < 30 || profile.weight > 300) {
        newErrors.weight = 'Weight should be between 30-300 kg';
      }
      
      if (!profile.gender) {
        newErrors.gender = 'Please select your sex';
      }
      
      // Warn if important fields are missing but don't block submission
      const warnings: string[] = [];
      if (!profile.age && !profile.dateOfBirth) {
        warnings.push('Age or date of birth');
      }
      if (!profile.medicalConditions?.length) {
        warnings.push('Medical conditions');
      }
      if (!profile.dietType?.length) {
        warnings.push('Diet type');
      }
      
      if (warnings.length > 0 && Object.keys(newErrors).length === 0) {
        // Show a gentle reminder but allow submission
        console.log('Optional fields that could improve meal planning:', warnings.join(', '));
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      onSubmit(profile);
    }
  };

  // Option arrays
  const ethnicityOptions = [
    'South Asian – North Indian',
    'South Asian – Pakistani', 
    'South Asian – Sri Lankan',
    'South Asian – Bangladeshi',
    'East Asian – Chinese',
    'East Asian – Korean',
    'Filipino',
    'Caucasian / White',
    'Black / African / African-American',
    'Caribbean – Jamaican',
    'Caribbean – Guyanese',
    'Indigenous / First Nations',
    'Middle Eastern',
    'Hispanic / Latin American',
    'Other'
  ];

  const medicalConditionsOptions = [
    'Type 2 Diabetes',
    'Type 1 Diabetes',
    'Obesity',
    'Hypertension',
    'High Cholesterol',
    'High Triglycerides',
    'Coronary Artery Disease',
    'Stroke',
    'Peripheral Vascular Disease',
    'Fatty Liver',
    'Chronic Kidney Disease',
    'Proteinuria',
    'Elevated Potassium',
    'PCOS',
    'Hypothyroidism',
    'Osteoporosis',
    'GERD / acid reflux',
    'B12 deficiency',
    'Iron deficiency / anemia',
    'Other'
  ];

  const medicationsOptions = [
    'Metformin',
    'Insulin',
    'GLP-1 agonist (e.g., Ozempic, Trulicity)',
    'SGLT2 inhibitor (e.g., Jardiance, Farxiga)',
    'Statin',
    'Diuretic',
    'Thyroid hormone',
    'Antihypertensives',
    'Anticoagulants (e.g., Aspirin, Eliquis)',
    'Other'
  ];

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

  const dietaryFeaturesOptions = [
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
    'Lactose-Free'
  ];

  const exerciseTypesOptions = [
    'Walking',
    'Jogging',
    'Resistance training / weights',
    'Yoga / Pilates',
    'Swimming',
    'Cycling (indoor/outdoor)',
    'Fitness classes (e.g., Zumba, aerobics)',
    'Home workouts',
    'Other'
  ];

  const appliancesOptions = [
    'Fridge & Freezer',
    'Microwave',
    'Instant Pot',
    'Air Fryer',
    'Blender',
    'Other'
  ];

  const primaryGoalsOptions = [
    'Weight loss',
    'Improve A1C',
    'Lower cholesterol / triglycerides',
    'Improve energy / stamina',
    'Reduce blood pressure',
    'Improve digestion',
    'General wellness',
    'Other'
  ];

  const sectionStyle = {
    mb: 3,
    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
    borderRadius: 2,
    overflow: 'hidden',
  };

  const sectionHeaderStyle = {
    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
    color: 'white',
    py: 2,
    px: 3,
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" align="center" gutterBottom sx={{ 
          color: theme.palette.primary.main,
          fontWeight: 'bold',
          mb: 3 
        }}>
          Comprehensive Health Profile
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          {isAdminMode ? (
            <>🏥 You are filling out this profile on behalf of the patient. The patient can complete any missing information later. Only the patient name is required.</>
          ) : (
            <>🔒 Your information is automatically saved as you type and stays private. The more details you provide, the more personalized your meal plan will be. All fields marked with * are required.</>
          )}
        </Alert>

        {/* Patient Demographics */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon />
              <Typography variant="h6">👤 Patient Demographics</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={isAdminMode ? "Patient Name *" : "Full Name *"}
                  value={profile.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  error={!!errors.name}
                  helperText={errors.name}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Date of Birth"
                  type="date"
                  value={profile.dateOfBirth}
                  onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Age"
                  type="number"
                  value={profile.age || ''}
                  onChange={(e) => handleInputChange('age', parseInt(e.target.value) || undefined)}
                  variant="outlined"
                  InputProps={{ readOnly: !!profile.dateOfBirth }}
                  helperText={profile.dateOfBirth ? "Auto-calculated" : "Years"}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth error={!!errors.gender}>
                  <FormLabel>{isAdminMode ? "Sex" : "Sex *"}</FormLabel>
                  <RadioGroup
                    row
                    value={profile.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                  >
                    <FormControlLabel value="Male" control={<Radio />} label="Male" />
                    <FormControlLabel value="Female" control={<Radio />} label="Female" />
                    <FormControlLabel value="Other" control={<Radio />} label="Other" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  options={ethnicityOptions}
                  value={profile.ethnicity || []}
                  onChange={(_, newValue) => handleInputChange('ethnicity', newValue)}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip variant="outlined" label={option} {...getTagProps({ index })} key={option} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField {...params} label="Ethnicity (select all that apply)" variant="outlined" />
                  )}
                />
                {(profile.ethnicity || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other ethnicity"
                      value={otherValues.ethnicity}
                      onChange={(e) => handleOtherChange('ethnicity', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.ethnicity.trim()) {
                          addOtherOption('ethnicity', 'ethnicity');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('ethnicity', 'ethnicity')}
                      disabled={!otherValues.ethnicity?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom ethnicity values */}
                {(profile.ethnicity || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.ethnicity || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newEthnicity = (profile.ethnicity || []).filter(e => e !== item);
                          handleInputChange('ethnicity', newEthnicity);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Vital Signs */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FavoriteIcon />
              <Typography variant="h6">📏 Vital Signs</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label={isAdminMode ? "Height (cm)" : "Height (cm) *"}
                  type="number"
                  value={profile.height || ''}
                  onChange={(e) => handleInputChange('height', parseFloat(e.target.value) || 0)}
                  error={!!errors.height}
                  helperText={errors.height}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label={isAdminMode ? "Weight (kg)" : "Weight (kg) *"}
                  type="number"
                  value={profile.weight || ''}
                  onChange={(e) => handleInputChange('weight', parseFloat(e.target.value) || 0)}
                  error={!!errors.weight}
                  helperText={errors.weight}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="BMI"
                  value={profile.bmi ? `${profile.bmi} ${getBMICategory(profile.bmi)}` : ''}
                  variant="outlined"
                  InputProps={{ 
                    readOnly: true,
                    style: { 
                      backgroundColor: '#f5f5f5',
                      color: getBMIColor(profile.bmi || 0)
                    }
                  }}
                  helperText="Auto-calculated from height & weight"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Waist Circumference (cm)"
                  type="number"
                  value={profile.waistCircumference || ''}
                  onChange={(e) => handleInputChange('waistCircumference', parseFloat(e.target.value) || undefined)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Blood Pressure (Systolic)"
                  type="number"
                  value={profile.systolicBP || ''}
                  onChange={(e) => handleInputChange('systolicBP', parseInt(e.target.value) || undefined)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">mmHg</InputAdornment>,
                  }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Blood Pressure (Diastolic)"
                  type="number"
                  value={profile.diastolicBP || ''}
                  onChange={(e) => handleInputChange('diastolicBP', parseInt(e.target.value) || undefined)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">mmHg</InputAdornment>,
                  }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Heart Rate"
                  type="number"
                  value={profile.heartRate || ''}
                  onChange={(e) => handleInputChange('heartRate', parseInt(e.target.value) || undefined)}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">bpm</InputAdornment>,
                  }}
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Medical History */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LocalHospitalIcon />
              <Typography variant="h6">🩺 Medical History</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <FormControl component="fieldset" fullWidth>
              <FormLabel component="legend">Check all that apply</FormLabel>
              <FormGroup>
                <Grid container>
                  {medicalConditionsOptions.map((condition) => (
                    <Grid item xs={12} md={6} key={condition}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={(profile.medicalConditions || []).includes(condition)}
                            onChange={(e) => handleArrayChange('medicalConditions', condition, e.target.checked)}
                          />
                        }
                        label={condition}
                      />
                    </Grid>
                  ))}
                </Grid>
                {(profile.medicalConditions || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other medical condition"
                      value={otherValues.medicalConditions}
                      onChange={(e) => handleOtherChange('medicalConditions', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.medicalConditions?.trim()) {
                          addOtherOption('medicalConditions', 'medicalConditions');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('medicalConditions', 'medicalConditions')}
                      disabled={!otherValues.medicalConditions?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom medical conditions */}
                {(profile.medicalConditions || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.medicalConditions || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newConditions = (profile.medicalConditions || []).filter(c => c !== item);
                          handleInputChange('medicalConditions', newConditions);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </FormGroup>
            </FormControl>
          </AccordionDetails>
        </Accordion>

        {/* Current Medications */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MedicationIcon />
              <Typography variant="h6">💊 Current Medications</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <FormControl component="fieldset" fullWidth>
              <FormLabel component="legend">Check all that apply</FormLabel>
              <FormGroup>
                <Grid container>
                  {medicationsOptions.map((medication) => (
                    <Grid item xs={12} md={6} key={medication}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={(profile.currentMedications || []).includes(medication)}
                            onChange={(e) => handleArrayChange('currentMedications', medication, e.target.checked)}
                          />
                        }
                        label={medication}
                      />
                    </Grid>
                  ))}
                </Grid>
                {(profile.currentMedications || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other medication"
                      value={otherValues.medications}
                      onChange={(e) => handleOtherChange('medications', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.medications?.trim()) {
                          addOtherOption('currentMedications', 'medications');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('currentMedications', 'medications')}
                      disabled={!otherValues.medications?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom medications */}
                {(profile.currentMedications || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.currentMedications || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newMedications = (profile.currentMedications || []).filter(m => m !== item);
                          handleInputChange('currentMedications', newMedications);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </FormGroup>
            </FormControl>
          </AccordionDetails>
        </Accordion>

        {/* Lab Values */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ScienceIcon />
              <Typography variant="h6">🧪 Most Recent Lab Values (Optional)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="A1C"
                  value={profile.labValues?.a1c || ''}
                  onChange={(e) => handleLabValueChange('a1c', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">%</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Fasting Glucose"
                  value={profile.labValues?.fastingGlucose || ''}
                  onChange={(e) => handleLabValueChange('fastingGlucose', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="LDL-C"
                  value={profile.labValues?.ldlCholesterol || ''}
                  onChange={(e) => handleLabValueChange('ldlCholesterol', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="HDL-C"
                  value={profile.labValues?.hdlCholesterol || ''}
                  onChange={(e) => handleLabValueChange('hdlCholesterol', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Triglycerides"
                  value={profile.labValues?.triglycerides || ''}
                  onChange={(e) => handleLabValueChange('triglycerides', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Total Cholesterol"
                  value={profile.labValues?.totalCholesterol || ''}
                  onChange={(e) => handleLabValueChange('totalCholesterol', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="eGFR"
                  value={profile.labValues?.egfr || ''}
                  onChange={(e) => handleLabValueChange('egfr', e.target.value)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Creatinine"
                  value={profile.labValues?.creatinine || ''}
                  onChange={(e) => handleLabValueChange('creatinine', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">µmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Potassium"
                  value={profile.labValues?.potassium || ''}
                  onChange={(e) => handleLabValueChange('potassium', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">mmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="uACR / proteinuria"
                  value={profile.labValues?.uacr || ''}
                  onChange={(e) => handleLabValueChange('uacr', e.target.value)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="ALT / AST"
                  value={profile.labValues?.alt || ''}
                  onChange={(e) => handleLabValueChange('alt', e.target.value)}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Vitamin D"
                  value={profile.labValues?.vitaminD || ''}
                  onChange={(e) => handleLabValueChange('vitaminD', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">nmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="B12"
                  value={profile.labValues?.b12 || ''}
                  onChange={(e) => handleLabValueChange('b12', e.target.value)}
                  InputProps={{ endAdornment: <InputAdornment position="end">pmol/L</InputAdornment> }}
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Dietary Information */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <RestaurantIcon />
              <Typography variant="h6">🍽️ Dietary Information</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Type of Diet (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {dietTypeOptions.map((diet) => (
                        <Grid item xs={12} md={6} key={diet}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.dietType || []).includes(diet)}
                                onChange={(e) => handleArrayChange('dietType', diet, e.target.checked)}
                              />
                            }
                            label={diet}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </FormGroup>
                </FormControl>
                {(profile.dietType || []).includes('Other') && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      label="Please specify other diet type"
                      value={otherValues.dietType}
                      onChange={(e) => handleOtherChange('dietType', e.target.value)}
                      variant="outlined"
                      sx={{ flexGrow: 1 }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && otherValues.dietType?.trim()) {
                          addOtherOption('dietType', 'dietType');
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => addOtherOption('dietType', 'dietType')}
                      disabled={!otherValues.dietType?.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                )}
                
                {/* Show current custom diet types */}
                {(profile.dietType || []).filter(item => item.startsWith('Other:')).length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                    {(profile.dietType || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                      <Chip
                        key={index}
                        label={item.replace('Other: ', '')}
                        size="small"
                        onDelete={() => {
                          const newDietTypes = (profile.dietType || []).filter(d => d !== item);
                          handleInputChange('dietType', newDietTypes);
                        }}
                        sx={{ mr: 1, mt: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </Grid>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Current Dietary Features (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {dietaryFeaturesOptions.map((feature) => (
                        <Grid item xs={12} md={6} key={feature}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.dietaryFeatures || []).includes(feature)}
                                onChange={(e) => handleArrayChange('dietaryFeatures', feature, e.target.checked)}
                              />
                            }
                            label={feature}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </FormGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Food Allergies"
                  value={profile.allergies?.join(', ') || ''}
                  onChange={(e) => handleInputChange('allergies', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  variant="outlined"
                  multiline
                  rows={2}
                  helperText="Separate multiple allergies with commas"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Food Items You Avoid"
                  value={profile.avoids?.join(', ') || ''}
                  onChange={(e) => handleInputChange('avoids', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  variant="outlined"
                  multiline
                  rows={2}
                  helperText="Separate multiple items with commas"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Strong Dislikes"
                  value={profile.strongDislikes?.join(', ') || ''}
                  onChange={(e) => handleInputChange('strongDislikes', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  variant="outlined"
                  multiline
                  rows={2}
                  helperText="Separate multiple dislikes with commas"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Physical Activity */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FitnessIcon />
              <Typography variant="h6">🏃 Physical Activity Profile</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Work Activity Level</FormLabel>
                  <RadioGroup
                    value={profile.workActivityLevel}
                    onChange={(e) => handleInputChange('workActivityLevel', e.target.value)}
                  >
                    <FormControlLabel value="Sedentary" control={<Radio />} label="Sedentary (e.g., desk work)" />
                    <FormControlLabel value="Moderately Active" control={<Radio />} label="Moderately Active (e.g., walking, light lifting)" />
                    <FormControlLabel value="Active" control={<Radio />} label="Active / Physical Labor" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Exercise Frequency</FormLabel>
                  <RadioGroup
                    value={profile.exerciseFrequency}
                    onChange={(e) => handleInputChange('exerciseFrequency', e.target.value)}
                  >
                    <FormControlLabel value="None" control={<Radio />} label="None" />
                    <FormControlLabel value="30-60 min/week" control={<Radio />} label="<30–60 min/week" />
                    <FormControlLabel value="60-150 min/week" control={<Radio />} label="60–150 min/week" />
                    <FormControlLabel value=">150 min/week" control={<Radio />} label=">150 min/week" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Type of Exercise (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {exerciseTypesOptions.map((exercise) => (
                        <Grid item xs={12} md={6} key={exercise}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.exerciseTypes || []).includes(exercise)}
                                onChange={(e) => handleArrayChange('exerciseTypes', exercise, e.target.checked)}
                              />
                            }
                            label={exercise}
                          />
                        </Grid>
                      ))}
                    </Grid>
                    {(profile.exerciseTypes || []).includes('Other') && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Please specify other exercise type"
                          value={otherValues.exerciseTypes}
                          onChange={(e) => handleOtherChange('exerciseTypes', e.target.value)}
                          variant="outlined"
                          sx={{ flexGrow: 1 }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.exerciseTypes?.trim()) {
                              addOtherOption('exerciseTypes', 'exerciseTypes');
                            }
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addOtherOption('exerciseTypes', 'exerciseTypes')}
                          disabled={!otherValues.exerciseTypes?.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                    )}
                    
                    {/* Show current custom exercise types */}
                    {(profile.exerciseTypes || []).filter(item => item.startsWith('Other:')).length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                        {(profile.exerciseTypes || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                          <Chip
                            key={index}
                            label={item.replace('Other: ', '')}
                            size="small"
                            onDelete={() => {
                              const newExerciseTypes = (profile.exerciseTypes || []).filter(e => e !== item);
                              handleInputChange('exerciseTypes', newExerciseTypes);
                            }}
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={profile.mobilityIssues || false}
                      onChange={(e) => handleInputChange('mobilityIssues', e.target.checked)}
                    />
                  }
                  label="I have mobility or joint issues"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Lifestyle & Preferences */}
        <Accordion sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HomeIcon />
              <Typography variant="h6">🧭 Lifestyle & Preferences</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Meal Prep Capability</FormLabel>
                  <RadioGroup
                    value={profile.mealPrepCapability}
                    onChange={(e) => handleInputChange('mealPrepCapability', e.target.value)}
                  >
                    <FormControlLabel value="Prepares own meals" control={<Radio />} label="Prepares own meals" />
                    <FormControlLabel value="Cooks with assistance" control={<Radio />} label="Cooks with assistance" />
                    <FormControlLabel value="Caregiver-prepared" control={<Radio />} label="Caregiver-prepared" />
                    <FormControlLabel value="Uses meal delivery service" control={<Radio />} label="Uses meal delivery service" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Eating Schedule Preference</FormLabel>
                  <RadioGroup
                    value={profile.eatingSchedule}
                    onChange={(e) => handleInputChange('eatingSchedule', e.target.value)}
                  >
                    <FormControlLabel value="3 meals/day" control={<Radio />} label="3 meals/day" />
                    <FormControlLabel value="2 meals + 1 snack" control={<Radio />} label="2 meals + 1 snack" />
                    <FormControlLabel value="Intermittent Fasting" control={<Radio />} label="Intermittent Fasting" />
                    <FormControlLabel value="Night Shift" control={<Radio />} label="Night Shift (11 pm–7 am)" />
                    <FormControlLabel value="Other" control={<Radio />} label="Other" />
                  </RadioGroup>
                  {profile.eatingSchedule === 'Other' && (
                    <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                      <TextField
                        size="small"
                        label="Please specify eating schedule"
                        value={otherValues.eatingSchedule}
                        onChange={(e) => handleOtherChange('eatingSchedule', e.target.value)}
                        variant="outlined"
                        sx={{ flexGrow: 1 }}
                        placeholder="e.g., 5 small meals, 16:8 fasting, etc."
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && otherValues.eatingSchedule?.trim()) {
                            handleInputChange('eatingSchedule', `Other: ${otherValues.eatingSchedule.trim()}`);
                            setOtherValues(prev => ({ ...prev, eatingSchedule: '' }));
                          }
                        }}
                      />
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          if (otherValues.eatingSchedule?.trim()) {
                            handleInputChange('eatingSchedule', `Other: ${otherValues.eatingSchedule.trim()}`);
                            setOtherValues(prev => ({ ...prev, eatingSchedule: '' }));
                          }
                        }}
                        disabled={!otherValues.eatingSchedule?.trim()}
                      >
                        Set
                      </Button>
                    </Box>
                  )}
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Appliances Available (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {appliancesOptions.map((appliance) => (
                        <Grid item xs={12} md={6} key={appliance}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.availableAppliances || []).includes(appliance)}
                                onChange={(e) => handleArrayChange('availableAppliances', appliance, e.target.checked)}
                              />
                            }
                            label={appliance}
                          />
                        </Grid>
                      ))}
                    </Grid>
                    {(profile.availableAppliances || []).includes('Other') && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Please specify other appliance"
                          value={otherValues.appliances}
                          onChange={(e) => handleOtherChange('appliances', e.target.value)}
                          variant="outlined"
                          sx={{ flexGrow: 1 }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.appliances?.trim()) {
                              addOtherOption('availableAppliances', 'appliances');
                            }
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addOtherOption('availableAppliances', 'appliances')}
                          disabled={!otherValues.appliances?.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                    )}
                    
                    {/* Show current custom appliances */}
                    {(profile.availableAppliances || []).filter(item => item.startsWith('Other:')).length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                        {(profile.availableAppliances || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                          <Chip
                            key={index}
                            label={item.replace('Other: ', '')}
                            size="small"
                            onDelete={() => {
                              const newAppliances = (profile.availableAppliances || []).filter(a => a !== item);
                              handleInputChange('availableAppliances', newAppliances);
                            }}
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Goals & Readiness */}
        <Accordion defaultExpanded sx={sectionStyle}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={sectionHeaderStyle}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrackChangesIcon />
              <Typography variant="h6">🎯 Goals & Readiness to Change</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <FormLabel component="legend">Primary Goals (select all that apply)</FormLabel>
                  <FormGroup>
                    <Grid container>
                      {primaryGoalsOptions.map((goal) => (
                        <Grid item xs={12} md={6} key={goal}>
                          <FormControlLabel
                            control={
                              <Checkbox
                                checked={(profile.primaryGoals || []).includes(goal)}
                                onChange={(e) => handleArrayChange('primaryGoals', goal, e.target.checked)}
                              />
                            }
                            label={goal}
                          />
                        </Grid>
                      ))}
                    </Grid>
                    {(profile.primaryGoals || []).includes('Other') && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Please specify other goal"
                          value={otherValues.goals}
                          onChange={(e) => handleOtherChange('goals', e.target.value)}
                          variant="outlined"
                          sx={{ flexGrow: 1 }}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.goals?.trim()) {
                              addOtherOption('primaryGoals', 'goals');
                            }
                          }}
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addOtherOption('primaryGoals', 'goals')}
                          disabled={!otherValues.goals?.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                    )}
                    
                    {/* Show current custom goals */}
                    {(profile.primaryGoals || []).filter(item => item.startsWith('Other:')).length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="textSecondary">Custom entries:</Typography>
                        {(profile.primaryGoals || []).filter(item => item.startsWith('Other:')).map((item, index) => (
                          <Chip
                            key={index}
                            label={item.replace('Other: ', '')}
                            size="small"
                            onDelete={() => {
                              const newGoals = (profile.primaryGoals || []).filter(g => g !== item);
                              handleInputChange('primaryGoals', newGoals);
                            }}
                            sx={{ mr: 1, mt: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </FormGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <FormLabel>Readiness to Change</FormLabel>
                  <RadioGroup
                    value={profile.readinessToChange}
                    onChange={(e) => handleInputChange('readinessToChange', e.target.value)}
                  >
                    <FormControlLabel value="Not ready" control={<Radio />} label="Not ready" />
                    <FormControlLabel value="Thinking about it" control={<Radio />} label="Thinking about it" />
                    <FormControlLabel value="Ready to take action" control={<Radio />} label="Ready to take action" />
                    <FormControlLabel value="Already making changes" control={<Radio />} label="Already making changes" />
                  </RadioGroup>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={profile.wantsWeightLoss || false}
                        onChange={(e) => handleInputChange('wantsWeightLoss', e.target.checked)}
                      />
                    }
                    label="Patient wants weight loss"
                  />
                  <FormControl fullWidth sx={{ mt: 2 }}>
                    <FormLabel>Suggested Calorie Target</FormLabel>
                    <RadioGroup
                      value={profile.calorieTarget}
                      onChange={(e) => handleInputChange('calorieTarget', e.target.value)}
                    >
                      <FormControlLabel value="1500" control={<Radio />} label="1500 kcal" />
                      <FormControlLabel value="1800" control={<Radio />} label="1800 kcal" />
                      <FormControlLabel value="2000" control={<Radio />} label="2000 kcal" />
                      <FormControlLabel value="2200" control={<Radio />} label="2200 kcal" />
                      <FormControlLabel value="Other" control={<Radio />} label="Custom calorie target" />
                    </RadioGroup>
                    {profile.calorieTarget === 'Other' && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <TextField
                          size="small"
                          label="Custom calorie target"
                          value={otherValues.calorieTarget}
                          onChange={(e) => handleOtherChange('calorieTarget', e.target.value)}
                          variant="outlined"
                          type="number"
                          inputProps={{ min: 1000, max: 5000 }}
                          sx={{ width: 200 }}
                          placeholder="e.g., 2500"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && otherValues.calorieTarget?.trim()) {
                              handleInputChange('calorieTarget', `${otherValues.calorieTarget.trim()}`);
                              setOtherValues(prev => ({ ...prev, calorieTarget: '' }));
                            }
                          }}
                        />
                        <Typography variant="body2" color="text.secondary">kcal/day</Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            if (otherValues.calorieTarget.trim()) {
                              handleInputChange('calorieTarget', `${otherValues.calorieTarget.trim()}`);
                              setOtherValues(prev => ({ ...prev, calorieTarget: '' }));
                            }
                          }}
                          disabled={!otherValues.calorieTarget?.trim()}
                        >
                          Set
                        </Button>
                      </Box>
                    )}
                  </FormControl>
                </Box>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit}
            sx={{
              px: 6,
              py: 2,
              fontSize: '1.2rem',
              fontWeight: 'bold',
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              '&:hover': {
                background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`,
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {submitButtonText}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default UserProfileForm; 