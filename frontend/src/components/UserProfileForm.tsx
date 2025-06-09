import React, { useState, useEffect, ChangeEvent, useCallback } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Checkbox,
  ListItemText,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Collapse,
  Grid,
  IconButton,
} from '@mui/material';
import { getPatientProfile, savePatientProfile } from '../services/api';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import {
  PatientProfile,
  DietaryInfo,
  PhysicalActivity,
  Lifestyle
} from '../types/PatientProfile';

interface UserProfileFormProps {
  onSubmit: (profile: PatientProfile) => Promise<void>;
  initialProfile?: PatientProfile;
  mode?: 'user' | 'admin';
}

// Define the structure for form errors, mirroring PatientProfile structure where fields can have errors
interface FormErrors {
  // Patient Demographics
  fullName?: string;
  intakeDate?: string;
  dateOfBirth?: string;
  age?: string;
  sex?: string;
  ethnicity?: string; // For multi-select, maybe just a general error?
  ethnicityOther?: string;

  // Medical History
  medicalHistory?: string; // For multi-select
  medicalHistoryOther?: string;
  medications?: string; // For multi-select
  medicationsOther?: string; // For the 'Other' medication text field

  // Most Recent Lab Values - Nested structure
  labValues?: {
    a1c?: string;
    fastingGlucose?: string;
    ldlC?: string;
    hdlC?: string;
    triglycerides?: string;
    totalCholesterol?: string;
    egfr?: string;
    creatinine?: string;
    potassium?: string;
    uacr?: string;
    alt?: string;
    ast?: string;
    vitaminD?: string;
    vitaminB12?: string;
  };

  // Vital Signs - Nested structure
  vitalSigns?: {
    heightCm?: string;
    weightKg?: string;
    bmi?: string; // Added bmi error type
    bloodPressureSystolic?: string;
    bloodPressureDiastolic?: string;
    heartRateBpm?: string;
  };

  // Dietary Information - Nested structure
  dietaryInfo?: {
    dietType?: string;
    dietFeatures?: string; // For multi-select
    allergies?: string; // String type error
    dislikes?: string; // String type error
  };

  // Physical Activity - Nested structure
  physicalActivity?: {
    workActivityLevel?: string; // Corrected property name
    exerciseFrequency?: string; // Corrected property name
    exerciseTypes?: string; // For multi-select
    exerciseTypesOther?: string; // Add this for the 'Other' text field
    exerciseTypesOtherUpdatedBy?: string; // Add this for the updatedBy helper text
    mobilityIssues?: string; // Boolean, but error can be string
  };

  // Lifestyle Factors - Nested structure
  lifestyle?: {
    mealPrepMethod?: string; // Corrected property name
    availableAppliances?: string; // For multi-select
    eatingSchedule?: string; // Corrected property name
    eatingScheduleOther?: string; // Corrected property name
  };

  // Goals & Readiness to Change - Not nested in type
   goals?: string; // For multi-select
   goalsOther?: string; // For 'Other' goals text field
   readiness?: string; // Corrected property name

  // Meal Plan Targeting - Nested structure
  mealPlanTargeting?: {
    wantsWeightLoss?: string; // Boolean, but error can be string
    calorieTarget?: string; // Number in type, but error can be string
  };
}

interface SectionProps {
    title: string;
    children: React.ReactNode;
    expanded: boolean;
    onToggle: () => void;
    sx?: any;
}

const Section: React.FC<SectionProps> = ({ title, children, expanded, onToggle, sx }) => (
    <Card sx={{ mb: 3, ...sx }}>
        <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6">{title}</Typography>
                <IconButton onClick={onToggle}>
                    {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
            </Box>
            <Collapse in={expanded}>
                <Box mt={2}>{children}</Box>
            </Collapse>
        </CardContent>
    </Card>
);

const UserProfileForm: React.FC<UserProfileFormProps> = ({ onSubmit, initialProfile, mode = 'user' }) => {
  // Constants and options
  const sexOptions = ['Male', 'Female', 'Other', 'Prefer not to say'];
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
    'Other:',
  ];
  const medicalHistoryOptions = [
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
    'Other:',
  ];
  const medicationOptions = [
    'Metformin',
    'Insulin',
    'GLP-1 agonist (e.g., Ozempic, Trulicity)',
    'SGLT2 inhibitor (e.g., Jardiance, Farxiga)',
    'Statin',
    'Diuretic',
    'Thyroid hormone',
    'Antihypertensives',
    'Anticoagulants (e.g., Aspirin, Eliquis)',
    'Other:',
  ];
  const dietTypeOptions = [
    'Standard',
    'Vegetarian',
    'Vegan',
    'Pescatarian',
    'Keto',
    'Low Carb',
    'Paleo',
    'Mediterranean',
    'DASH',
    'Gluten-Free',
    'Dairy-Free',
    'Other',
  ];
  const dietFeaturesOptions = [
    'High Protein', 'Low Fat', 'Low Sodium', 'High Fiber', 'Sugar-Free', 'Organic', 'Local Produce', 'Seasonal Eating'
  ];
  const workActivityLevelOptions = ['Sedentary', 'Light', 'Moderate', 'Heavy'];
  const exerciseFrequencyOptions = ['None', '1-2 times/week', '3-4 times/week', '5+ times/week'];
  const mealPrepMethodOptions = ['Own', 'Assisted', 'Caregiver', 'Delivery'];
  const eatingScheduleOptions = ['3 meals', '2 meals + snack', 'Fasting', 'Night Shift', 'Other'];
  const availableAppliancesOptions = ['Stove', 'Oven', 'Microwave', 'Blender', 'Toaster'];
  const goalsOptions = [
    'Weight Loss',
    'Improved Blood Sugar Control',
    'Lower Cholesterol',
    'Lower Blood Pressure',
    'Increased Energy Levels',
    'Better Digestion',
    'Reduced Inflammation',
    'Improved Sleep',
    'Increased Physical Activity',
    'Better Stress Management',
    'Learn Healthy Cooking Skills',
    'Meal Planning',
    'Mindful Eating',
    'Manage Food Cravings',
    'Navigate Social Eating Situations',
    'Reduce Processed Foods',
    'Increase Fruits and Vegetables',
    'Increase Fiber Intake',
    'Reduce Sugar Intake',
    'Reduce Sodium Intake',
    'Increase Protein Intake',
    'Increase Healthy Fats',
    'Understand Food Labels',
    'Grocery Shopping Strategies',
    'Eating Out Strategies',
    'Managing Hunger and Fullness',
    'Other:',
  ];
  const readinessOptions = ['Not ready', 'Thinking about it', 'Getting started', 'Already making changes'];

  // Helper functions
  const calculateAge = (dob: string): number => {
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const isOtherSelected = (selectedItems: any) => {
    return Array.isArray(selectedItems) && selectedItems.includes('Other:');
  };

  const ensureArray = (value: any): any[] => {
    if (!value) return [];
    if (Array.isArray(value)) {
      // Filter out undefined/null values
      return value.filter(item => item !== undefined && item !== null);
    }
    if (typeof value === 'string') return [value];
    return [];
  };

  const safeJoinArray = (selected: any): string => {
    if (!selected) return '';
    if (Array.isArray(selected)) {
      // Filter out undefined/null values and join
      const validItems = selected.filter(item => item !== undefined && item !== null && item !== '');
      return validItems.join(', ');
    }
    if (typeof selected === 'string') return selected;
    return '';
  };

  // Initialize form data with proper defaults
  const initializeFormData = (profile: PatientProfile): Partial<PatientProfile> => ({
    ...profile,
    // Properly initialize nested objects with default values
    vitalSigns: {
      heightCm: undefined,
      weightKg: undefined,
      bmi: undefined,
      bloodPressureSystolic: undefined,
      bloodPressureDiastolic: undefined,
      heartRateBpm: undefined,
      ...profile.vitalSigns,
    },
    labValues: {
      a1c: undefined,
      fastingGlucose: undefined,
      ldlC: undefined,
      hdlC: undefined,
      triglycerides: undefined,
      totalCholesterol: undefined,
      egfr: undefined,
      creatinine: undefined,
      potassium: undefined,
      uacr: undefined,
      alt: undefined,
      ast: undefined,
      vitaminD: undefined,
      vitaminB12: undefined,
      ...profile.labValues,
    },
    dietaryInfo: {
      dietType: undefined,
      dietFeatures: [],
      allergies: '',
      dislikes: '',
      ...profile.dietaryInfo,
    },
    physicalActivity: {
      workActivityLevel: undefined,
      exerciseFrequency: undefined,
      exerciseTypes: [],
      exerciseTypesOther: undefined,
      exerciseTypesOtherUpdatedBy: undefined,
      mobilityIssues: undefined,
      ...profile.physicalActivity,
    },
    lifestyle: {
      mealPrepMethod: undefined,
      availableAppliances: [],
      eatingSchedule: undefined,
      eatingScheduleOther: undefined,
      ...profile.lifestyle,
    },
    mealPlanTargeting: {
      wantsWeightLoss: undefined,
      calorieTarget: undefined,
      ...profile.mealPlanTargeting,
    },
    // Ensure arrays are properly initialized
    ethnicity: profile.ethnicity || [],
    medicalHistory: profile.medicalHistory || [],
    medications: profile.medications || [],
    goals: profile.goals || [],
  });

  // Get empty form data with proper defaults
  const getEmptyFormData = (): Partial<PatientProfile> => ({
    fullName: '',
    intakeDate: undefined,
    dateOfBirth: undefined,
    age: undefined,
    sex: undefined,
    ethnicity: [],
    ethnicityOther: undefined,
    medicalHistory: [],
    medicalHistoryOther: undefined,
    medications: [],
    medicationsOther: undefined,
    labValues: {
      a1c: undefined,
      fastingGlucose: undefined,
      ldlC: undefined,
      hdlC: undefined,
      triglycerides: undefined,
      totalCholesterol: undefined,
      egfr: undefined,
      creatinine: undefined,
      potassium: undefined,
      uacr: undefined,
      alt: undefined,
      ast: undefined,
      vitaminD: undefined,
      vitaminB12: undefined,
    },
    vitalSigns: {
      heightCm: undefined,
      weightKg: undefined,
      bmi: undefined,
      bloodPressureSystolic: undefined,
      bloodPressureDiastolic: undefined,
      heartRateBpm: undefined,
    },
    dietaryInfo: {
      dietType: undefined,
      dietFeatures: [],
      allergies: '',
      dislikes: '',
    },
    physicalActivity: {
      workActivityLevel: undefined,
      exerciseFrequency: undefined,
      exerciseTypes: [],
      exerciseTypesOther: undefined,
      exerciseTypesOtherUpdatedBy: undefined,
      mobilityIssues: undefined,
    },
    lifestyle: {
      mealPrepMethod: undefined,
      availableAppliances: [],
      eatingSchedule: undefined,
      eatingScheduleOther: undefined,
    },
    goals: [],
    goalsOther: undefined,
    readiness: undefined,
    mealPlanTargeting: {
      wantsWeightLoss: undefined,
      calorieTarget: undefined,
    },
  });

  // State declarations
  const [formData, setFormData] = useState<Partial<PatientProfile>>(() => {
    if (initialProfile) {
      return initializeFormData(initialProfile);
    }
    return getEmptyFormData();
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [ageManuallyEdited, setAgeManuallyEdited] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    demographics: true,
    medical: false,
    medications: false,
    vitals: false,
    labs: false,
    dietary: false,
    physical: false,
    lifestyle: false,
    goals: false,
  });
  const [formDataLoaded, setFormDataLoaded] = useState(false);
  const [heightUnit, setHeightUnit] = useState('cm');
  const [weightUnit, setWeightUnit] = useState('kg');

  // Unit conversion helpers
  const cmToInches = (cm: number) => cm / 2.54;
  const inchesToCm = (inches: number) => inches * 2.54;
  const kgToLbs = (kg: number) => kg * 2.20462;
  const lbsToKg = (lbs: number) => lbs / 2.20462;

  // Form data handlers
  const updateFormData = useCallback((updates: Partial<PatientProfile>) => {
    setFormData((prev: Partial<PatientProfile>) => ({
      ...prev,
      ...updates
    }));
  }, []);

  const handleInputChange = useCallback((e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { name: string; value: string } }) => {
    const name = e?.target?.name;
    const value = e?.target?.value;
    
    if (!name) {
      console.warn('Input change event missing name property');
      return;
    }
    
    if (name === 'dateOfBirth' && value) {
      const age = calculateAge(value);
      updateFormData({
        [name]: value,
        age: age
      });
    } else {
      updateFormData({ [name]: value });
    }
  }, [updateFormData]);

  const handleSelectChange = useCallback((e: any) => {
    const name = e?.target?.name;
    const value = e?.target?.value;
    
    if (!name) {
      console.warn('Select change event missing name property');
      return;
    }

    updateFormData({ [name]: value });
  }, [updateFormData]);

  const handleMultiSelectChange = useCallback((e: any) => {
    const name = e?.target?.name;
    const value = e?.target?.value;
    
    if (!name) {
      console.warn('Multi-select change event missing name property');
      return;
    }

    // Handle nested object updates
    if (name === 'dietFeatures') {
      updateFormData({ 
        dietaryInfo: { 
          ...formData.dietaryInfo, 
          dietFeatures: value as string[] 
        } 
      });
    } else if (name === 'exerciseTypes') {
      updateFormData({ 
        physicalActivity: { 
          ...formData.physicalActivity, 
          exerciseTypes: value as string[] 
        } 
      });
    } else if (name === 'availableAppliances') {
      updateFormData({ 
        lifestyle: { 
          ...formData.lifestyle, 
          availableAppliances: value as string[] 
        } 
      });
    } else {
      // Handle regular fields
      updateFormData({ [name]: value });
    }
  }, [updateFormData, formData.dietaryInfo, formData.physicalActivity, formData.lifestyle]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (validateForm()) {
      setLoading(true);
      setErrors({});
      try {
        const profileToSubmit: PatientProfile = {
          fullName: formData.fullName || '',
          intakeDate: formData.intakeDate || undefined,
          dateOfBirth: formData.dateOfBirth || undefined,
          age: formData.age || undefined,
          sex: formData.sex || undefined,
          ethnicity: formData.ethnicity || [],
          ethnicityOther: formData.ethnicityOther || undefined,
          medicalHistory: formData.medicalHistory || [],
          medicalHistoryOther: formData.medicalHistoryOther || undefined,
          medications: formData.medications || [],
          medicationsOther: formData.medicationsOther || undefined,
          labValues: {
              a1c: formData.labValues?.a1c || undefined,
              fastingGlucose: formData.labValues?.fastingGlucose || undefined,
              ldlC: formData.labValues?.ldlC || undefined,
              hdlC: formData.labValues?.hdlC || undefined,
              triglycerides: formData.labValues?.triglycerides || undefined,
              totalCholesterol: formData.labValues?.totalCholesterol || undefined,
              egfr: formData.labValues?.egfr || undefined,
              creatinine: formData.labValues?.creatinine || undefined,
              potassium: formData.labValues?.potassium || undefined,
              uacr: formData.labValues?.uacr || undefined,
              alt: formData.labValues?.alt || undefined,
              ast: formData.labValues?.ast || undefined,
              vitaminD: formData.labValues?.vitaminD || undefined,
              vitaminB12: formData.labValues?.vitaminB12 || undefined,
          },
          vitalSigns: {
              heightCm: formData.vitalSigns?.heightCm || undefined,
              weightKg: formData.vitalSigns?.weightKg || undefined,
              bmi: formData.vitalSigns?.bmi || undefined,
              bloodPressureSystolic: formData.vitalSigns?.bloodPressureSystolic || undefined,
              bloodPressureDiastolic: formData.vitalSigns?.bloodPressureDiastolic || undefined,
              heartRateBpm: formData.vitalSigns?.heartRateBpm || undefined,
          },
          dietaryInfo: {
              dietType: formData.dietaryInfo?.dietType || undefined,
              dietFeatures: formData.dietaryInfo?.dietFeatures || [],
              allergies: formData.dietaryInfo?.allergies || '', // Initialize as string
              dislikes: formData.dietaryInfo?.dislikes || '', // Initialize as string
          },
          physicalActivity: {
              workActivityLevel: formData.physicalActivity?.workActivityLevel || undefined,
              exerciseFrequency: formData.physicalActivity?.exerciseFrequency || undefined,
              exerciseTypes: formData.physicalActivity?.exerciseTypes || [],
              exerciseTypesOther: formData.physicalActivity?.exerciseTypesOther || undefined,
              exerciseTypesOtherUpdatedBy: formData.physicalActivity?.exerciseTypesOtherUpdatedBy || undefined,
              mobilityIssues: formData.physicalActivity?.mobilityIssues !== undefined ? formData.physicalActivity.mobilityIssues : undefined,
          },
          lifestyle: {
              mealPrepMethod: formData.lifestyle?.mealPrepMethod || undefined,
              availableAppliances: formData.lifestyle?.availableAppliances || [],
              eatingSchedule: formData.lifestyle?.eatingSchedule || undefined,
              eatingScheduleOther: formData.lifestyle?.eatingScheduleOther || undefined,
          },
          goals: formData.goals || [], // Goals is an array
          goalsOther: formData.goalsOther || undefined,
          readiness: formData.readiness || undefined,

          mealPlanTargeting: {
              wantsWeightLoss: formData.mealPlanTargeting?.wantsWeightLoss !== undefined ? formData.mealPlanTargeting.wantsWeightLoss : undefined,
              calorieTarget: formData.mealPlanTargeting?.calorieTarget || undefined,
          },
        };

        // Debug logging for wantsWeightLoss
        console.log('🔍 DEBUG wantsWeightLoss:', {
          formDataValue: formData.mealPlanTargeting?.wantsWeightLoss,
          submittedValue: profileToSubmit.mealPlanTargeting?.wantsWeightLoss,
          type: typeof formData.mealPlanTargeting?.wantsWeightLoss
        });

        await onSubmit(profileToSubmit);
        setAlert({ type: 'success', message: 'Profile saved successfully!' });
      } catch (err: any) {
        setErrors({});
        setAlert({ 
          type: 'error', 
          message: err.message || 'An error occurred while saving the profile. Please log in again.' 
        });
      } finally {
        setLoading(false);
      }
    }
  };

  const handleSectionToggle = (section: string) => {
    setExpandedSections(prev => ({
        ...prev,
        [section]: !prev[section]
    }));
  };

  const validateForm = () => {
    const newErrors: FormErrors = {};
    let isValid = true;

    // Basic validation examples (expand as needed)
    if (!formData.fullName) {
      newErrors.fullName = 'Full Name is required';
      isValid = false;
    }

     if (!formData.sex) {
      newErrors.sex = 'Sex is required';
      isValid = false;
    }

    if (!formData.vitalSigns?.heightCm) {
        if (!newErrors.vitalSigns) newErrors.vitalSigns = {};
        newErrors.vitalSigns.heightCm = 'Height is required';
        isValid = false;
    }
     if (!formData.vitalSigns?.weightKg) {
        if (!newErrors.vitalSigns) newErrors.vitalSigns = {};
        newErrors.vitalSigns.weightKg = 'Weight is required';
        isValid = false;
    }

    // Add more validation for other required fields and nested structures

    setErrors(newErrors);
    return isValid;
  };

  // Load saved profile on component mount
  useEffect(() => {
    const loadSavedProfile = async () => {
      try {
        // In admin mode, use the initialProfile passed as prop instead of fetching
        if (mode === 'admin' && initialProfile) {
          setFormData(initializeFormData(initialProfile));
        } else if (mode === 'user') {
          const savedProfile = await getPatientProfile();
          if (savedProfile) {
            setFormData(initializeFormData(savedProfile));
          }
        } else {
          // Initialize with empty form data if no profile available
          setFormData(getEmptyFormData());
        }
      } catch (error) {
        console.error('Error loading saved profile:', error);
        setAlert({
          type: 'error',
          message: 'Failed to load saved profile. Please log in again.'
        });
      } finally {
        setFormDataLoaded(true);
      }
    };

    loadSavedProfile();
  }, [mode, initialProfile]);

  // Auto-save form data when it changes (only in user mode)
  useEffect(() => {
    if (formDataLoaded && mode === 'user') {
      const saveData = async () => {
        try {
          const success = await savePatientProfile(formData);
          if (!success) {
            console.warn('Failed to auto-save form data');
            setAlert({
              type: 'error',
              message: 'Failed to save changes. Please log in again.'
            });
          }
        } catch (error) {
          console.error('Error auto-saving form data:', error);
          setAlert({
            type: 'error',
            message: 'Failed to save changes. Please log in again.'
          });
        }
      };
      saveData();
    }
  }, [formData, formDataLoaded, mode]);

  // Auto-calculate age when dateOfBirth changes, but only if age hasn't been manually edited
  useEffect(() => {
    if (formData.dateOfBirth && !ageManuallyEdited) {
      const calculatedAge = calculateAge(formData.dateOfBirth);
      if (calculatedAge !== formData.age) {
        updateFormData({ age: calculatedAge });
      }
    }
  }, [formData.dateOfBirth, formData.age, updateFormData, ageManuallyEdited]);

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Patient Profile
        </Typography>
        {alert && (
          <Alert severity={alert.type} sx={{ mb: 2 }}>
            {alert.message}
          </Alert>
        )}
        {loading && (
          <Box display="flex" justifyContent="center" my={2}>
            <CircularProgress />
          </Box>
        )}
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Demographics Section */}
            <Section
                title="Demographics"
                expanded={expandedSections.demographics}
                onToggle={() => handleSectionToggle('demographics')}
                sx={{ mt: 2 }}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Full Name"
                            name="fullName"
                            value={formData.fullName || ''}
                            onChange={handleInputChange}
                            error={!!errors.fullName}
                            helperText={`Last updated by: ${formData.fullNameUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Date of Birth"
                            type="date"
                            name="dateOfBirth"
                            value={formData.dateOfBirth || ''}
                            onChange={(e) => {
                                setAgeManuallyEdited(false);
                                updateFormData({ dateOfBirth: e.target.value });
                            }}
                            InputLabelProps={{
                                shrink: true,
                            }}
                            error={!!errors.dateOfBirth}
                            helperText={`Last updated by: ${formData.dateOfBirthUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Age"
                            type="number"
                            name="age"
                            value={formData.age || ''}
                            onChange={(e) => {
                                setAgeManuallyEdited(true);
                                updateFormData({ age: parseInt(e.target.value) || undefined });
                            }}
                            error={!!errors.age}
                            helperText={`Last updated by: ${formData.ageUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.sex}>
                            <InputLabel>Sex</InputLabel>
                            <Select
                                name="sex"
                                value={formData.sex || ''}
                                label="Sex"
                                onChange={handleSelectChange}
                            >
                                {sexOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                             {errors.sex && <FormHelperText>{errors.sex}</FormHelperText>}
                        </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.ethnicity}>
                            <InputLabel>Ethnicity (check all that apply)</InputLabel>
                             <Select
                                multiple
                                name="ethnicity"
                                value={ensureArray(formData.ethnicity)}
                                onChange={handleMultiSelectChange}
                                label="Ethnicity (check all that apply)"
                                renderValue={safeJoinArray}
                            >
                                {ethnicityOptions.map((option) => (
                                    <MenuItem key={option} value={option}>
                                        <Checkbox checked={(formData.ethnicity || []).includes(option)} />
                                        <ListItemText primary={option} />
                                    </MenuItem>
                                ))}
                            </Select>
                             {errors.ethnicity && <FormHelperText>{errors.ethnicity}</FormHelperText>}
                        </FormControl>
                    </Grid>
                    {isOtherSelected(ensureArray(formData.ethnicity)) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Ethnicity"
                                name="ethnicityOther"
                                value={formData.ethnicityOther || ''}
                                onChange={(e) => updateFormData({ ethnicityOther: e.target.value })}
                                error={!!errors.ethnicityOther}
                                helperText={`Last updated by: ${formData.ethnicityUpdatedBy || 'Not set'}`}
                            />
                        </Grid>
                    )}
                </Grid>
            </Section>

            {/* Medical History Section */}
            <Section
                title="Medical History"
                expanded={expandedSections.medical}
                onToggle={() => handleSectionToggle('medical')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl component="fieldset">
                            <FormLabel>Medical Conditions</FormLabel>
                            <FormGroup>
                                {medicalHistoryOptions.map((condition) => (
                                    <FormControlLabel
                                        key={condition}
                                        control={
                                            <Checkbox
                                                checked={Array.isArray(formData.medicalHistory) ? formData.medicalHistory.includes(condition) : false}
                                                onChange={(e) => {
                                                    const currentHistory = Array.isArray(formData.medicalHistory) ? formData.medicalHistory : [];
                                                    const newHistory = e.target.checked
                                                        ? [...currentHistory, condition]
                                                        : currentHistory.filter((c: string) => c !== condition);
                                                    updateFormData({ // Update directly
                                                        medicalHistory: newHistory,
                                                    });
                                                }}
                                            />
                                        }
                                        label={condition}
                                    />
                                ))}
                            </FormGroup>
                            <FormHelperText>
                                Last updated by: {formData.medicalHistoryUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    {isOtherSelected(ensureArray(formData.medicalHistory)) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Medical History"
                                name="medicalHistoryOther"
                                value={formData.medicalHistoryOther || ''}
                                onChange={(e) => updateFormData({ medicalHistoryOther: e.target.value })}
                                error={!!errors.medicalHistoryOther}
                                helperText={`Last updated by: ${formData.medicalHistoryUpdatedBy || 'Not set'}`}
                            />
                        </Grid>
                    )}
                </Grid>
            </Section>

            {/* Current Medications Section */}
            <Section
                title="Current Medications"
                expanded={expandedSections.medical}
                onToggle={() => handleSectionToggle('medical')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.medications}>
                            <FormLabel>Medications</FormLabel>
                            <Select
                                multiple
                                name="medications"
                                value={ensureArray(formData.medications)}
                                onChange={handleMultiSelectChange}
                                label="Medications"
                                renderValue={safeJoinArray}
                            >
                                {medicationOptions.map((option) => (
                                    <MenuItem key={option} value={option}>
                                        <Checkbox checked={(formData.medications || []).includes(option)} />
                                        <ListItemText primary={option} />
                                    </MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.medicationsUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    {isOtherSelected(ensureArray(formData.medications)) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Medications"
                                name="medicationsOther"
                                value={formData.medicationsOther || ''}
                                onChange={(e) => updateFormData({ medicationsOther: e.target.value })}
                                 error={!!errors.medicationsOther}
                                helperText={`Last updated by: ${formData.medicationsUpdatedBy || 'Not set'}`}
                            />
                        </Grid>
                    )}
                </Grid>
            </Section>

            {/* Vital Signs Section */}
            <Section
                title="Vital Signs"
                expanded={expandedSections.vitals}
                onToggle={() => handleSectionToggle('vitals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}> {/* Use Box for flex layout */}
                            <TextField
                                fullWidth
                                label={`Height (${heightUnit})`}
                                type="number"
                                name="heightCm"
                                value={
                                    formData.vitalSigns?.heightCm === undefined || formData.vitalSigns.heightCm === null
                                        ? ''
                                        : heightUnit === 'cm' ? formData.vitalSigns.heightCm : cmToInches(formData.vitalSigns.heightCm)
                                }
                                onChange={(e) => {
                                    const inputValue = parseFloat(e.target.value);
                                    const cmValue = heightUnit === 'cm' ? inputValue : inchesToCm(inputValue);
                                    updateFormData({ vitalSigns: { ...formData.vitalSigns, heightCm: isNaN(cmValue) ? undefined : cmValue } });
                                }}
                                error={!!errors.vitalSigns?.heightCm}
                                helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                            />
                            <FormControl size="small">
                                <Select
                                    value={heightUnit}
                                    onChange={(e) => {
                                        const newUnit = e.target.value as 'cm' | 'inches';
                                        const currentCmValue = formData.vitalSigns?.heightCm;
                                        if (currentCmValue !== undefined && currentCmValue !== null) {
                                            // Convert current value to the new unit for display consistency
                                            const displayValue = newUnit === 'cm' ? currentCmValue : cmToInches(currentCmValue);
                                             // The actual state remains in cm, only the display unit changes
                                            setHeightUnit(newUnit);
                                        } else {
                                            setHeightUnit(newUnit);
                                        }
                                    }}
                                    displayEmpty
                                >
                                    <MenuItem value="cm">cm</MenuItem>
                                    <MenuItem value="inches">inches</MenuItem>
                                </Select>
                            </FormControl>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                         <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}> {/* Use Box for flex layout */}
                            <TextField
                                fullWidth
                                label={`Weight (${weightUnit})`}
                                type="number"
                                name="weightKg"
                                value={
                                     formData.vitalSigns?.weightKg === undefined || formData.vitalSigns.weightKg === null
                                        ? ''
                                        : weightUnit === 'kg' ? formData.vitalSigns.weightKg : kgToLbs(formData.vitalSigns.weightKg)
                                }
                                onChange={(e) => {
                                    const inputValue = parseFloat(e.target.value);
                                    const kgValue = weightUnit === 'kg' ? inputValue : lbsToKg(inputValue);
                                    updateFormData({ vitalSigns: { ...formData.vitalSigns, weightKg: isNaN(kgValue) ? undefined : kgValue } });
                                }}
                                error={!!errors.vitalSigns?.weightKg}
                                helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                            />
                             <FormControl size="small">
                                <Select
                                    value={weightUnit}
                                    onChange={(e) => {
                                        const newUnit = e.target.value as 'kg' | 'lbs';
                                        const currentKgValue = formData.vitalSigns?.weightKg;
                                         if (currentKgValue !== undefined && currentKgValue !== null) {
                                            // Convert current value to the new unit for display consistency
                                            const displayValue = newUnit === 'kg' ? currentKgValue : kgToLbs(currentKgValue);
                                            // The actual state remains in kg, only the display unit changes
                                            setWeightUnit(newUnit);
                                        } else {
                                            setWeightUnit(newUnit);
                                        }
                                    }}
                                    displayEmpty
                                >
                                    <MenuItem value="kg">kg</MenuItem>
                                    <MenuItem value="lbs">lbs</MenuItem>
                                </Select>
                            </FormControl>
                        </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        {/* BMI is calculated, not input */}
                        <TextField
                            fullWidth
                            label="BMI"
                            name="bmi"
                            value={
                              formData.vitalSigns?.heightCm && formData.vitalSigns?.weightKg
                                ? (formData.vitalSigns.weightKg / ((formData.vitalSigns.heightCm / 100) ** 2)).toFixed(2)
                                : ''
                            }
                            InputProps={{
                              readOnly: true,
                            }}
                             error={!!errors.vitalSigns?.bmi}
                            helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Blood Pressure Systolic (mmHg)"
                            type="number"
                            name="bloodPressureSystolic"
                            value={formData.vitalSigns?.bloodPressureSystolic || ''}
                            onChange={(e) => updateFormData({ vitalSigns: { ...formData.vitalSigns, bloodPressureSystolic: parseFloat(e.target.value) } })} // Store as number
                             error={!!errors.vitalSigns?.bloodPressureSystolic}
                            helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Blood Pressure Diastolic (mmHg)"
                            type="number"
                            name="bloodPressureDiastolic"
                            value={formData.vitalSigns?.bloodPressureDiastolic || ''}
                            onChange={(e) => updateFormData({ vitalSigns: { ...formData.vitalSigns, bloodPressureDiastolic: parseFloat(e.target.value) } })} // Store as number
                             error={!!errors.vitalSigns?.bloodPressureDiastolic}
                            helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Heart Rate (bpm)"
                            type="number"
                            name="heartRateBpm"
                            value={formData.vitalSigns?.heartRateBpm || ''}
                            onChange={(e) => updateFormData({ vitalSigns: { ...formData.vitalSigns, heartRateBpm: parseFloat(e.target.value) } })} // Store as number
                             error={!!errors.vitalSigns?.heartRateBpm}
                            helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Lab Values Section */}
            <Section
                title="Lab Values"
                expanded={expandedSections.labs}
                onToggle={() => handleSectionToggle('labs')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="A1C (%)"
                            type="number"
                            name="a1c"
                            value={formData.labValues?.a1c || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, a1c: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.a1c}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Fasting Glucose (mg/dL)"
                            type="number"
                            name="fastingGlucose"
                            value={formData.labValues?.fastingGlucose || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, fastingGlucose: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.fastingGlucose}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="LDL-C (mg/dL)"
                            type="number"
                            name="ldlC"
                            value={formData.labValues?.ldlC || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, ldlC: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.ldlC}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="HDL-C (mg/dL)"
                            type="number"
                            name="hdlC"
                            value={formData.labValues?.hdlC || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, hdlC: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.hdlC}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Triglycerides (mg/dL)"
                            type="number"
                            name="triglycerides"
                            value={formData.labValues?.triglycerides || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, triglycerides: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.triglycerides}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Total Cholesterol (mg/dL)"
                            type="number"
                            name="totalCholesterol"
                            value={formData.labValues?.totalCholesterol || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, totalCholesterol: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.totalCholesterol}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="eGFR (mL/min/1.73 m²)"
                            type="number"
                            name="egfr"
                            value={formData.labValues?.egfr || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, egfr: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.egfr}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Creatinine (mg/dL)"
                            type="number"
                            name="creatinine"
                            value={formData.labValues?.creatinine || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, creatinine: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.creatinine}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Potassium (mEq/L)"
                            type="number"
                            name="potassium"
                            value={formData.labValues?.potassium || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, potassium: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.potassium}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="UACR (mg/g)"
                            type="number"
                            name="uacr"
                            value={formData.labValues?.uacr || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, uacr: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.uacr}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="ALT (U/L)"
                            type="number"
                            name="alt"
                            value={formData.labValues?.alt || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, alt: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.alt}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="AST (U/L)"
                            type="number"
                            name="ast"
                            value={formData.labValues?.ast || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, ast: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.ast}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Vitamin D (nmol/L)"
                            type="number"
                            name="vitaminD"
                            value={formData.labValues?.vitaminD || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, vitaminD: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.vitaminD}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Vitamin B12 (pmol/L)"
                            type="number"
                            name="vitaminB12"
                            value={formData.labValues?.vitaminB12 || ''}
                            onChange={(e) => updateFormData({ labValues: { ...formData.labValues, vitaminB12: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.labValues?.vitaminB12}
                            helperText={`Last updated by: ${formData.labValuesUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Dietary Information Section */}
            <Section
                title="Dietary Information"
                expanded={expandedSections.dietary}
                onToggle={() => handleSectionToggle('dietary')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.dietaryInfo?.dietType}>
                            <FormLabel>Diet Type</FormLabel>
                            <Select
                                name="dietType"
                                value={formData.dietaryInfo?.dietType || ''}
                                label="Diet Type"
                                onChange={(e) => updateFormData({ dietaryInfo: { ...formData.dietaryInfo, dietType: e.target.value } })} // dietType is string
                            >
                                 <MenuItem value=""><em>None</em></MenuItem>
                                {dietTypeOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.dietaryInfoUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.dietaryInfo?.dietFeatures}>
                            <FormLabel>Dietary Features</FormLabel>
                            <Select
                                multiple
                                name="dietFeatures"
                                value={ensureArray(formData.dietaryInfo?.dietFeatures)}
                                onChange={handleMultiSelectChange}
                                label="Dietary Features"
                                renderValue={safeJoinArray}
                            >
                                {dietFeaturesOptions.map((option) => (
                                    <MenuItem key={option} value={option}>
                                        <Checkbox checked={(formData.dietaryInfo?.dietFeatures || []).includes(option)} />
                                        <ListItemText primary={option} />
                                    </MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.dietaryInfoUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Food Allergies"
                            name="allergies"
                            value={formData.dietaryInfo?.allergies || ''}
                            onChange={(e) => updateFormData({ dietaryInfo: { ...formData.dietaryInfo, allergies: e.target.value } })} // allergies is string
                            error={!!errors.dietaryInfo?.allergies}
                            helperText={`Last updated by: ${formData.dietaryInfoUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            label="Food Dislikes"
                            name="dislikes"
                            value={formData.dietaryInfo?.dislikes || ''}
                            onChange={(e) => updateFormData({ dietaryInfo: { ...formData.dietaryInfo, dislikes: e.target.value } })} // dislikes is string
                            error={!!errors.dietaryInfo?.dislikes}
                            helperText={`Last updated by: ${formData.dietaryInfoUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Physical Activity Section */}
            <Section
                title="Physical Activity"
                expanded={expandedSections.physical}
                onToggle={() => handleSectionToggle('physical')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.physicalActivity?.workActivityLevel}>
                            <FormLabel>Work Activity Level</FormLabel>
                            <Select
                                name="workActivityLevel"
                                value={formData.physicalActivity?.workActivityLevel || ''}
                                label="Work Activity Level"
                                onChange={(e) => updateFormData({ 
                                    physicalActivity: { 
                                        ...formData.physicalActivity, 
                                        workActivityLevel: e.target.value as 'Sedentary' | 'Light' | 'Moderate' | 'Heavy' | undefined 
                                    } 
                                })} // workActivityLevel is enum
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                {workActivityLevelOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.physicalActivityUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.physicalActivity?.exerciseFrequency}>
                            <FormLabel>Exercise Frequency</FormLabel>
                            <Select
                                name="exerciseFrequency"
                                value={formData.physicalActivity?.exerciseFrequency || ''}
                                label="Exercise Frequency"
                                onChange={(e) => updateFormData({ 
                                    physicalActivity: { 
                                        ...formData.physicalActivity, 
                                        exerciseFrequency: e.target.value as 'None' | '1-2 times/week' | '3-4 times/week' | '5+ times/week' | undefined 
                                    } 
                                })} // exerciseFrequency is enum
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                {exerciseFrequencyOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.physicalActivityUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.physicalActivity?.exerciseTypes}>
                            <FormLabel>Exercise Types</FormLabel>
                            <Select
                                multiple
                                name="exerciseTypes"
                                value={ensureArray(formData.physicalActivity?.exerciseTypes)}
                                onChange={handleMultiSelectChange}
                                label="Exercise Types"
                                renderValue={safeJoinArray}
                            >
                                <MenuItem value="Walking"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Walking')} /> <ListItemText primary="Walking" /></MenuItem>
                                <MenuItem value="Jogging"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Jogging')} /> <ListItemText primary="Jogging" /></MenuItem>
                                <MenuItem value="Resistance training / weights"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Resistance training / weights')} /> <ListItemText primary="Resistance training / weights" /></MenuItem>
                                <MenuItem value="Yoga / Pilates"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Yoga / Pilates')} /> <ListItemText primary="Yoga / Pilates" /></MenuItem>
                                <MenuItem value="Swimming"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Swimming')} /> <ListItemText primary="Swimming" /></MenuItem>
                                <MenuItem value="Cycling (indoor/outdoor)"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Cycling (indoor/outdoor)')} /> <ListItemText primary="Cycling (indoor/outdoor)" /></MenuItem>
                                <MenuItem value="Fitness classes (e.g., Zumba, aerobics)"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Fitness classes (e.g., Zumba, aerobics)')} /> <ListItemText primary="Fitness classes (e.g., Zumba, aerobics)" /></MenuItem>
                                <MenuItem value="Home workouts"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Home workouts')} /> <ListItemText primary="Home workouts" /></MenuItem>
                                <MenuItem value="Other"><Checkbox checked={(formData.physicalActivity?.exerciseTypes || []).includes('Other')} /> <ListItemText primary="Other" /></MenuItem>
                            </Select>
                            {errors.physicalActivity?.exerciseTypes && <FormHelperText>{errors.physicalActivity.exerciseTypes}</FormHelperText>}
                        </FormControl>
                    </Grid>
                    {/* Conditional text field for "Other" exercise type */}
                    {isOtherSelected(ensureArray(formData.physicalActivity?.exerciseTypes)) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Exercise Type"
                                name="exerciseTypesOther"
                                value={formData.physicalActivity?.exerciseTypesOther || ''}
                                onChange={(e) => updateFormData({ physicalActivity: { ...formData.physicalActivity, exerciseTypesOther: e.target.value } })}
                                error={!!errors.physicalActivity?.exerciseTypesOther}
                                helperText={`Last updated by: ${formData.physicalActivity?.exerciseTypesOtherUpdatedBy || 'Not set'}`}
                            />
                        </Grid>
                    )}
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.physicalActivity?.mobilityIssues}>
                            <FormLabel>Mobility Issues</FormLabel>
                            <Select
                                name="mobilityIssues"
                                value={formData.physicalActivity?.mobilityIssues === undefined ? '' : formData.physicalActivity.mobilityIssues.toString()}
                                label="Mobility Issues"
                                onChange={(e) => {
                                    const value = e.target.value;
                                    updateFormData({ 
                                        physicalActivity: { 
                                            ...formData.physicalActivity, 
                                            mobilityIssues: value === '' ? undefined : value === 'true' 
                                        } 
                                    });
                                }}
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                <MenuItem value="true">Yes</MenuItem>
                                <MenuItem value="false">No</MenuItem>
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.physicalActivityUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Lifestyle Section */}
            <Section
                title="Lifestyle"
                expanded={expandedSections.lifestyle}
                onToggle={() => handleSectionToggle('lifestyle')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.lifestyle?.mealPrepMethod}>
                            <FormLabel>Meal Preparation Method</FormLabel>
                            <Select
                                name="mealPrepMethod"
                                value={formData.lifestyle?.mealPrepMethod || ''}
                                label="Meal Preparation Method"
                                onChange={(e) => updateFormData({ 
                                    lifestyle: { 
                                        ...formData.lifestyle, 
                                        mealPrepMethod: e.target.value as 'Own' | 'Assisted' | 'Caregiver' | 'Delivery' | undefined 
                                    } 
                                })} // mealPrepMethod is enum
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                {mealPrepMethodOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.lifestyleUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.lifestyle?.availableAppliances}>
                            <FormLabel>Available Appliances</FormLabel>
                            <Select
                                multiple
                                name="availableAppliances"
                                value={ensureArray(formData.lifestyle?.availableAppliances)}
                                onChange={handleMultiSelectChange}
                                label="Available Appliances"
                                renderValue={safeJoinArray}
                            >
                                {availableAppliancesOptions.map((option) => (
                                    <MenuItem key={option} value={option}>
                                        <Checkbox checked={(formData.lifestyle?.availableAppliances || []).includes(option)} />
                                        <ListItemText primary={option} />
                                    </MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.lifestyleUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.lifestyle?.eatingSchedule}>
                            <FormLabel>Eating Schedule</FormLabel>
                            <Select
                                name="eatingSchedule"
                                value={formData.lifestyle?.eatingSchedule || ''}
                                label="Eating Schedule"
                                onChange={(e) => updateFormData({ 
                                    lifestyle: { 
                                        ...formData.lifestyle, 
                                        eatingSchedule: e.target.value as '3 meals' | '2 meals + snack' | 'Fasting' | 'Night Shift' | 'Other' | undefined 
                                    } 
                                })} // eatingSchedule is enum
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                {eatingScheduleOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.lifestyleUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    {(formData.lifestyle?.eatingSchedule === 'Other') && (
                        <Grid item xs={12} sm={6}>
                            <TextField
                                fullWidth
                                label="Specify Other Eating Schedule"
                                name="eatingScheduleOther"
                                value={formData.lifestyle?.eatingScheduleOther || ''}
                                onChange={(e) => updateFormData({ lifestyle: { ...formData.lifestyle, eatingScheduleOther: e.target.value } })} // eatingScheduleOther is string
                                error={!!errors.lifestyle?.eatingScheduleOther}
                                helperText={`Last updated by: ${formData.lifestyleUpdatedBy || 'Not set'}`}
                            />
                        </Grid>
                    )}
                </Grid>
            </Section>

            {/* Goals Section */}
            <Section
                title="Goals"
                expanded={expandedSections.goals}
                onToggle={() => handleSectionToggle('goals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <FormControl fullWidth error={!!errors.goals}>
                            <FormLabel>Goals</FormLabel>
                            <Select
                                multiple
                                name="goals"
                                value={ensureArray(formData.goals)}
                                onChange={handleMultiSelectChange}
                                label="Goals"
                                renderValue={safeJoinArray}
                            >
                                {goalsOptions.map((option) => (
                                    <MenuItem key={option} value={option}>
                                        <Checkbox checked={(formData.goals || []).includes(option)} />
                                        <ListItemText primary={option} />
                                    </MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.goalsUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    {isOtherSelected(ensureArray(formData.goals)) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Goals"
                                name="goalsOther"
                                value={formData.goalsOther || ''}
                                onChange={(e) => updateFormData({ goalsOther: e.target.value })} // goalsOther is string
                                error={!!errors.goalsOther}
                                helperText={`Last updated by: ${formData.goalsUpdatedBy || 'Not set'}`}
                            />
                        </Grid>
                    )}
                </Grid>
            </Section>

            {/* Readiness Section */}
            <Section
                title="Readiness"
                expanded={expandedSections.goals}
                onToggle={() => handleSectionToggle('goals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.readiness}>
                            <FormLabel>Readiness</FormLabel>
                            <Select
                                name="readiness"
                                value={formData.readiness || ''}
                                label="Readiness"
                                onChange={(e) => updateFormData({ 
                                    readiness: e.target.value as 'Not ready' | 'Thinking about it' | 'Getting started' | 'Already making changes' | undefined 
                                })} // readiness is enum
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                {readinessOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.readinessUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                </Grid>
            </Section>

            {/* Meal Plan Targeting Section */}
            <Section
                title="Meal Plan Targeting"
                expanded={expandedSections.goals}
                onToggle={() => handleSectionToggle('goals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.mealPlanTargeting?.wantsWeightLoss}>
                            <FormLabel>Wants Weight Loss</FormLabel>
                            <Select
                                name="wantsWeightLoss"
                                value={formData.mealPlanTargeting?.wantsWeightLoss === undefined ? '' : formData.mealPlanTargeting.wantsWeightLoss.toString()}
                                label="Wants Weight Loss"
                                onChange={(e) => {
                                    const value = e.target.value;
                                    updateFormData({ 
                                        mealPlanTargeting: { 
                                            ...formData.mealPlanTargeting, 
                                            wantsWeightLoss: value === '' ? undefined : value === 'true' 
                                        } 
                                    });
                                }}
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                <MenuItem value="true">Yes</MenuItem>
                                <MenuItem value="false">No</MenuItem>
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.mealPlanTargetingUpdatedBy || 'Not set'}
                            </FormHelperText>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Calorie Target"
                            type="number"
                            name="calorieTarget"
                            value={formData.mealPlanTargeting?.calorieTarget || ''}
                            onChange={(e) => updateFormData({ mealPlanTargeting: { ...formData.mealPlanTargeting, calorieTarget: parseFloat(e.target.value) } })} // Store as number
                            error={!!errors.mealPlanTargeting?.calorieTarget}
                            helperText={`Last updated by: ${formData.mealPlanTargetingUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                </Grid>
            </Section>

            <Grid item xs={12}>
                <Button type="submit" variant="contained" color="primary" disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Save Profile'}
                </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Container>
  );
};

export default UserProfileForm;
