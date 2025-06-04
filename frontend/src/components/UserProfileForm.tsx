import React, { useState, useEffect, ChangeEvent } from 'react';
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
  Grid,
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
  Radio,
  RadioGroup,
  Switch,
  Collapse,
  IconButton,
} from '@mui/material';
import { PatientProfile, LabValues, VitalSigns, DietaryInfo, PhysicalActivity, Lifestyle, MealPlanTargeting } from '../types/PatientProfile'; // Corrected import path and imported nested types
import { getPatientProfile } from '../services/api'; // Add this import
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface UserProfileFormProps {
  onSubmit: (profile: PatientProfile) => Promise<void>;
  initialProfile?: PatientProfile;
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

const UserProfileForm: React.FC<UserProfileFormProps> = ({ onSubmit, initialProfile }) => {
  const [formData, setFormData] = useState<Partial<PatientProfile>>(() => {
    if (initialProfile) {
      // Ensure nested objects exist if initialProfile is provided and handle array/string types
      return {
        ...initialProfile,
        vitalSigns: initialProfile.vitalSigns || {},
        labValues: initialProfile.labValues || {},
        dietaryInfo: {
           ...initialProfile.dietaryInfo,
           dietFeatures: initialProfile.dietaryInfo?.dietFeatures || [],
           allergies: initialProfile.dietaryInfo?.allergies || '', // Initialize as string
           dislikes: initialProfile.dietaryInfo?.dislikes || '', // Initialize as string
        } as DietaryInfo, // Cast to DietaryInfo
        physicalActivity: {
          ...initialProfile.physicalActivity,
          exerciseTypes: initialProfile.physicalActivity?.exerciseTypes || [],
        } as PhysicalActivity, // Cast to PhysicalActivity
        lifestyle: {
          ...initialProfile.lifestyle,
          availableAppliances: initialProfile.lifestyle?.availableAppliances || [],
        } as Lifestyle, // Cast to Lifestyle
        mealPlanTargeting: initialProfile.mealPlanTargeting || {},
        // Ensure top-level array fields are arrays
        ethnicity: initialProfile.ethnicity || [],
        medicalHistory: initialProfile.medicalHistory || [],
        medications: initialProfile.medications || [],
        goals: initialProfile.goals || [], // Goals is an array
      };
    }
    return {
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
        allergies: '', // Initialize as string
        dislikes: '', // Initialize as string
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

      goals: [], // Goals is an array
      goalsOther: undefined,
      readiness: undefined,

      mealPlanTargeting: {
        wantsWeightLoss: undefined,
        calorieTarget: undefined,
      },
    };
  });


  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({
    demographics: true,
    medical: true,
    vitals: true,
    dietary: true,
    activity: true,
    lifestyle: true,
    goals: true,
  });

  // State for unit selection
  const [heightUnit, setHeightUnit] = useState('cm');
  const [weightUnit, setWeightUnit] = useState('kg');

  // Helper functions for unit conversion
  const cmToInches = (cm: number) => cm / 2.54;
  const inchesToCm = (inches: number) => inches * 2.54;
  const kgToLbs = (kg: number) => kg * 2.20462;
  const lbsToKg = (lbs: number) => lbs / 2.20462;

  // Handlers for nested state - Simplified field type to string
  const handleNestedInputChange = (section: keyof PatientProfile, field: string, value: any) => {
     setFormData(prev => {
        const sectionData = prev?.[section] as Record<string, any> | undefined;
        return {
          ...prev,
          [section]: {
            ...sectionData,
            [field]: value,
          },
        } as Partial<PatientProfile>; // Cast the result back to Partial<PatientProfile>
     });
  };

  const handleNestedSelectChange = (section: keyof PatientProfile, field: string, value: any) => {
     setFormData(prev => {
        const sectionData = prev?.[section] as Record<string, any> | undefined;
        return {
          ...prev,
          [section]: {
            ...sectionData,
            [field]: value,
          },
        } as Partial<PatientProfile>; // Cast the result back to Partial<PatientProfile>
     });
  };


  const handleNestedMultiSelectChange = (section: keyof PatientProfile, field: string, value: string[]) => {
    setFormData(prev => {
        const sectionData = prev?.[section] as Record<string, any> | undefined;
        return {
          ...prev,
          [section]: {
            ...sectionData,
            [field]: value,
          },
        } as Partial<PatientProfile>; // Cast the result back to Partial<PatientProfile>
     });
  };


    // Handler for top-level state (like fullName, ethnicity, goals, readiness)
  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSelectChange = (e: any) => { // Use 'any' for now due to complex event types
    const { name, value } = e.target;
     setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  }

   const handleMultiSelectChange = (e: any) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value, // Value is expected to be an array for multi-select
    }) as Partial<PatientProfile>);
  };


    const handleOtherEthnicityChange = (e: ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            ethnicityOther: e.target.value
        }));
    };

     const handleOtherMedicalHistoryChange = (e: ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            medicalHistoryOther: e.target.value
        }));
    };

    const handleOtherMedicationChange = (e: ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            medicationsOther: e.target.value
        }));
    };

    const handleOtherGoalsChange = (e: ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            goalsOther: e.target.value
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

    setErrors(newErrors); // Use setErrors instead of setError
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (validateForm()) {
      setLoading(true);
      setErrors({}); // Clear previous errors // Use setErrors instead of setError
      try {
        // Ensure all nested objects and arrays are initialized before submitting
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
                mobilityIssues: formData.physicalActivity?.mobilityIssues || undefined,
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
                wantsWeightLoss: formData.mealPlanTargeting?.wantsWeightLoss || undefined,
                calorieTarget: formData.mealPlanTargeting?.calorieTarget || undefined,
            },
         };


        await onSubmit(profileToSubmit);
        setAlert({ type: 'success', message: 'Profile saved successfully!' });
      } catch (err: any) {
        setErrors({}); // Clear errors on successful submission, but this is error case
        setAlert({ type: 'error', message: err.message || 'An error occurred while saving the profile.' });
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

    // Options based on PhysicalActivity type
   const workActivityLevelOptions = ['Sedentary', 'Moderate', 'Physical Labor'];
   const exerciseFrequencyOptions = ['None', '<60min', '60–150min', '>150min'];

    // Options based on Lifestyle type
    const mealPrepMethodOptions = ['Own', 'Assisted', 'Caregiver', 'Delivery'];
    const eatingScheduleOptions = ['3 meals', '2 meals + snack', 'Fasting', 'Night Shift', 'Other'];
    const availableAppliancesOptions = ['Stove', 'Oven', 'Microwave', 'Blender', 'Toaster']; // Example appliances


    // Options based on Goals type (string array)
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


    // Check if 'Other:' is selected in a multi-select string array
    const isOtherSelected = (selectedItems: any) => {
      return Array.isArray(selectedItems) && selectedItems.includes('Other:');
    };

    // Check if 'Other' is selected in a string field (like dietaryInfo.allergies)
     const isOtherSelectedString = (selectedItem: string | undefined, options: string[]) => {
        // This check might need refinement based on how "Other" is handled in the string fields
        // For now, assuming "Other" is an exact match if selected from a single-select list or typed.
        return selectedItem === 'Other';
     };

  // Add these helper functions at the top level of the component
  const ensureArray = (value: any): any[] => {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'string') return [value];
    return [];
  };

  const safeJoinArray = (selected: any): string => {
    if (!selected) return '';
    if (Array.isArray(selected)) return selected.join(', ');
    if (typeof selected === 'string') return selected;
    return '';
  };

  // Update the useEffect that loads saved data
  useEffect(() => {
    const loadSavedProfile = async () => {
      try {
        const savedProfile = await getPatientProfile();
        if (savedProfile) {
          // Ensure all multi-select fields are arrays
          const processedProfile = {
            ...savedProfile,
            ethnicity: ensureArray(savedProfile.ethnicity),
            medicalHistory: ensureArray(savedProfile.medicalHistory),
            medications: ensureArray(savedProfile.medications),
            dietaryInfo: {
              ...savedProfile.dietaryInfo,
              dietFeatures: ensureArray(savedProfile.dietaryInfo?.dietFeatures),
            },
            physicalActivity: {
              ...savedProfile.physicalActivity,
              exerciseTypes: ensureArray(savedProfile.physicalActivity?.exerciseTypes),
            },
            lifestyle: {
              ...savedProfile.lifestyle,
              availableAppliances: ensureArray(savedProfile.lifestyle?.availableAppliances),
            },
            goals: ensureArray(savedProfile.goals),
          };
          setFormData(processedProfile);
        }
      } catch (error) {
        console.error('Error loading saved profile:', error);
        setAlert({
          type: 'error',
          message: 'Failed to load saved profile'
        });
      }
    };

    loadSavedProfile();
  }, []);

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
                            onChange={handleInputChange}
                            InputLabelProps={{ shrink: true }}
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
                            onChange={handleInputChange} // Age is a number in type, but input value is string
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
                                onChange={handleOtherEthnicityChange}
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
                                                        : currentHistory.filter(c => c !== condition);
                                                    setFormData(prev => ({ // Update directly
                                                        ...prev,
                                                        medicalHistory: newHistory,
                                                    }));
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
                                onChange={handleOtherMedicalHistoryChange}
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
                    {isOtherSelected(formData.medications) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Medications"
                                name="medicationsOther"
                                value={formData.medicationsOther || ''}
                                onChange={handleOtherMedicationChange}
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
                                    handleNestedInputChange('vitalSigns', 'heightCm', isNaN(cmValue) ? undefined : cmValue);
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
                                    handleNestedInputChange('vitalSigns', 'weightKg', isNaN(kgValue) ? undefined : kgValue);
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
                            onChange={(e) => handleNestedInputChange('vitalSigns', 'bloodPressureSystolic', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('vitalSigns', 'bloodPressureDiastolic', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('vitalSigns', 'heartRateBpm', parseFloat(e.target.value))} // Store as number
                             error={!!errors.vitalSigns?.heartRateBpm}
                            helperText={`Last updated by: ${formData.vitalSignsUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Lab Values Section */}
            <Section
                title="Lab Values"
                expanded={expandedSections.vitals}
                onToggle={() => handleSectionToggle('vitals')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="A1C (%)"
                            type="number"
                            name="a1c"
                            value={formData.labValues?.a1c || ''}
                            onChange={(e) => handleNestedInputChange('labValues', 'a1c', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'fastingGlucose', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'ldlC', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'hdlC', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'triglycerides', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'totalCholesterol', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'egfr', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'creatinine', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'potassium', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'uacr', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'alt', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'ast', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'vitaminD', parseFloat(e.target.value))} // Store as number
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
                            onChange={(e) => handleNestedInputChange('labValues', 'vitaminB12', parseFloat(e.target.value))} // Store as number
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
                                onChange={(e) => handleNestedInputChange('dietaryInfo', 'dietType', e.target.value)} // dietType is string
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
                                onChange={(e) => handleNestedMultiSelectChange('dietaryInfo', 'dietFeatures', e.target.value as string[])}
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
                            onChange={(e) => handleNestedInputChange('dietaryInfo', 'allergies', e.target.value)} // allergies is string
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
                            onChange={(e) => handleNestedInputChange('dietaryInfo', 'dislikes', e.target.value)} // dislikes is string
                            error={!!errors.dietaryInfo?.dislikes}
                            helperText={`Last updated by: ${formData.dietaryInfoUpdatedBy || 'Not set'}`}
                        />
                    </Grid>
                </Grid>
            </Section>

            {/* Physical Activity Section */}
            <Section
                title="Physical Activity"
                expanded={expandedSections.activity}
                onToggle={() => handleSectionToggle('activity')}
            >
                <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth error={!!errors.physicalActivity?.workActivityLevel}>
                            <FormLabel>Work Activity Level</FormLabel>
                            <Select
                                name="workActivityLevel"
                                value={formData.physicalActivity?.workActivityLevel || ''}
                                label="Work Activity Level"
                                onChange={(e) => handleNestedSelectChange('physicalActivity', 'workActivityLevel', e.target.value)} // workActivityLevel is enum
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
                                onChange={(e) => handleNestedSelectChange('physicalActivity', 'exerciseFrequency', e.target.value)} // exerciseFrequency is enum
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
                                onChange={(e) => handleNestedMultiSelectChange('physicalActivity', 'exerciseTypes', e.target.value as string[])}
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
                                onChange={(e) => handleNestedInputChange('physicalActivity', 'exerciseTypesOther', e.target.value)}
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
                                value={formData.physicalActivity?.mobilityIssues === undefined ? '' : formData.physicalActivity.mobilityIssues}
                                label="Mobility Issues"
                                onChange={(e) => handleNestedInputChange('physicalActivity', 'mobilityIssues', e.target.value === '' ? undefined : e.target.value)} // mobilityIssues is boolean
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                <MenuItem value={true as any}>Yes</MenuItem> {/* Use any for boolean value in Select */}
                                <MenuItem value={false as any}>No</MenuItem> {/* Use any for boolean value in Select */}
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
                                onChange={(e) => handleNestedSelectChange('lifestyle', 'mealPrepMethod', e.target.value)} // mealPrepMethod is enum
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
                                onChange={(e) => handleNestedMultiSelectChange('lifestyle', 'availableAppliances', e.target.value as string[])}
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
                                onChange={(e) => handleNestedSelectChange('lifestyle', 'eatingSchedule', e.target.value)} // eatingSchedule is enum
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
                                onChange={(e) => handleNestedInputChange('lifestyle', 'eatingScheduleOther', e.target.value)} // eatingScheduleOther is string
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
                    {isOtherSelected(formData.goals) && (
                        <Grid item xs={12}>
                            <TextField
                                fullWidth
                                label="Specify Other Goals"
                                name="goalsOther"
                                value={formData.goalsOther || ''}
                                onChange={handleOtherGoalsChange} // goalsOther is string
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
                                onChange={(e) => handleSelectChange(e)} // readiness is enum
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                {readinessOptions.map((option) => (
                                    <MenuItem key={option} value={option}>{option}</MenuItem>
                                ))}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.goalsUpdatedBy || 'Not set'}
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
                                value={formData.mealPlanTargeting?.wantsWeightLoss === undefined ? '' : formData.mealPlanTargeting.wantsWeightLoss}
                                label="Wants Weight Loss"
                                onChange={(e) => handleNestedInputChange('mealPlanTargeting', 'wantsWeightLoss', e.target.value === '' ? undefined : e.target.value)} // wantsWeightLoss is boolean
                            >
                                <MenuItem value=""><em>None</em></MenuItem>
                                <MenuItem value={true as any}>Yes</MenuItem> {/* Use any for boolean value in Select */}
                                <MenuItem value={false as any}>No</MenuItem> {/* Use any for boolean value in Select */}
                            </Select>
                            <FormHelperText>
                                Last updated by: {formData.goalsUpdatedBy || 'Not set'}
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
                            onChange={(e) => handleNestedInputChange('mealPlanTargeting', 'calorieTarget', parseFloat(e.target.value))} // Store as number
                            error={!!errors.mealPlanTargeting?.calorieTarget}
                            helperText={`Last updated by: ${formData.goalsUpdatedBy || 'Not set'}`}
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
