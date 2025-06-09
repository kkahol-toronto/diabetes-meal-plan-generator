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

interface PatientProfileFormProps {
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
  ethnicity?: string;
  
  // Medical History
  medicalHistory?: string;
  medications?: string;
  
  // Lab Values
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
  
  // Vital Signs
  vitalSigns?: {
    heightCm?: string;
    weightKg?: string;
    bmi?: string;
    bloodPressureSystolic?: string;
    bloodPressureDiastolic?: string;
    heartRateBpm?: string;
  };
  
  // Dietary Info
  dietaryInfo?: {
    dietType?: string;
    dietFeatures?: string;
    allergies?: string;
    dislikes?: string;
  };
  
  // Physical Activity
  physicalActivity?: {
    workActivityLevel?: string;
    exerciseFrequency?: string;
    exerciseTypes?: string;
    mobilityIssues?: string;
  };
  
  // Lifestyle
  lifestyle?: {
    mealPrepMethod?: string;
    availableAppliances?: string;
    eatingSchedule?: string;
  };
  
  // Goals & Readiness
  goals?: string;
  readiness?: string;
  
  // Meal Plan Targeting
  mealPlanTargeting?: {
    wantsWeightLoss?: string;
    calorieTarget?: string;
  };
}

const PatientProfileForm: React.FC<PatientProfileFormProps> = ({ 
  onSubmit, 
  initialProfile,
  mode = 'user'
}) => {
  const [profile, setProfile] = useState<PatientProfile>({});
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    demographics: true,
    medical: false,
    labValues: false,
    vitals: false,
    dietary: false,
    physical: false,
    lifestyle: false,
    goals: false,
    targeting: false,
  });

  // Initialize profile with initial data
  useEffect(() => {
    if (initialProfile) {
      setProfile(initialProfile);
    }
  }, [initialProfile]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleInputChange = useCallback((field: string, value: any, nestedField?: string) => {
    setProfile(prev => {
      if (nestedField) {
        return {
          ...prev,
          [field]: {
            ...(prev[field as keyof PatientProfile] as object || {}),
            [nestedField]: value
          }
        };
      }
      return {
        ...prev,
        [field]: value
      };
    });

    // Clear error when user starts typing
    if (nestedField) {
      setErrors(prev => ({
        ...prev,
        [field]: {
          ...(prev[field as keyof FormErrors] as object || {}),
          [nestedField]: undefined
        }
      }));
    } else {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  }, []);

  const handleSubmit = async () => {
    try {
      setSaving(true);
      await onSubmit(profile);
    } catch (error) {
      console.error('Error submitting profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const calculateAge = (dateOfBirth: string): number | undefined => {
    if (!dateOfBirth) return undefined;
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  // Auto-calculate age when date of birth changes
  useEffect(() => {
    if (profile.dateOfBirth) {
      const calculatedAge = calculateAge(profile.dateOfBirth);
      if (calculatedAge !== undefined && calculatedAge !== profile.age) {
        handleInputChange('age', calculatedAge);
      }
    }
  }, [profile.dateOfBirth, profile.age, handleInputChange]);

  // Auto-calculate BMI when height or weight changes
  useEffect(() => {
    const height = profile.vitalSigns?.heightCm;
    const weight = profile.vitalSigns?.weightKg;
    
    if (height && weight && height > 0) {
      const heightInMeters = height / 100;
      const calculatedBMI = weight / (heightInMeters * heightInMeters);
      const roundedBMI = Math.round(calculatedBMI * 10) / 10;
      
      if (roundedBMI !== profile.vitalSigns?.bmi) {
        handleInputChange('vitalSigns', roundedBMI, 'bmi');
      }
    }
  }, [profile.vitalSigns?.heightCm, profile.vitalSigns?.weightKg, profile.vitalSigns?.bmi, handleInputChange]);

  return (
    <Container maxWidth="md">
      <Box sx={{ py: 2 }}>
        {/* Demographics Section */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" component="h2">
                Patient Demographics
              </Typography>
              <IconButton onClick={() => toggleSection('demographics')}>
                {expandedSections.demographics ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expandedSections.demographics}>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Full Name"
                    value={profile.fullName || ''}
                    onChange={(e) => handleInputChange('fullName', e.target.value)}
                    error={!!errors.fullName}
                    helperText={errors.fullName}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Date of Birth"
                    type="date"
                    value={profile.dateOfBirth || ''}
                    onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.dateOfBirth}
                    helperText={errors.dateOfBirth}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Age"
                    type="number"
                    value={profile.age || ''}
                    onChange={(e) => handleInputChange('age', parseInt(e.target.value) || undefined)}
                    error={!!errors.age}
                    helperText={errors.age || 'Auto-calculated from date of birth'}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth error={!!errors.sex}>
                    <InputLabel>Sex</InputLabel>
                    <Select
                      value={profile.sex || ''}
                      onChange={(e) => handleInputChange('sex', e.target.value)}
                      label="Sex"
                    >
                      <MenuItem value="Male">Male</MenuItem>
                      <MenuItem value="Female">Female</MenuItem>
                      <MenuItem value="Other">Other</MenuItem>
                    </Select>
                    {errors.sex && <FormHelperText>{errors.sex}</FormHelperText>}
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth error={!!errors.ethnicity}>
                    <InputLabel>Ethnicity</InputLabel>
                    <Select
                      multiple
                      value={profile.ethnicity || []}
                      onChange={(e) => handleInputChange('ethnicity', e.target.value)}
                      label="Ethnicity"
                      renderValue={(selected) => (selected as string[]).join(', ')}
                    >
                      {[
                        'White',
                        'Black or African American',
                        'Asian',
                        'Hispanic or Latino',
                        'Native American',
                        'Pacific Islander',
                        'Other'
                      ].map((ethnicity) => (
                        <MenuItem key={ethnicity} value={ethnicity}>
                          <Checkbox checked={(profile.ethnicity || []).includes(ethnicity)} />
                          <ListItemText primary={ethnicity} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.ethnicity && <FormHelperText>{errors.ethnicity}</FormHelperText>}
                  </FormControl>
                </Grid>
              </Grid>
            </Collapse>
          </CardContent>
        </Card>

        {/* Medical History Section */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" component="h2">
                Medical History
              </Typography>
              <IconButton onClick={() => toggleSection('medical')}>
                {expandedSections.medical ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expandedSections.medical}>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <FormControl fullWidth error={!!errors.medicalHistory}>
                    <InputLabel>Medical Conditions</InputLabel>
                    <Select
                      multiple
                      value={profile.medicalHistory || []}
                      onChange={(e) => handleInputChange('medicalHistory', e.target.value)}
                      label="Medical Conditions"
                      renderValue={(selected) => (selected as string[]).join(', ')}
                    >
                      {[
                        'Type 1 Diabetes',
                        'Type 2 Diabetes',
                        'Prediabetes',
                        'Hypertension',
                        'High Cholesterol',
                        'Heart Disease',
                        'Kidney Disease',
                        'Obesity',
                        'Other'
                      ].map((condition) => (
                        <MenuItem key={condition} value={condition}>
                          <Checkbox checked={(profile.medicalHistory || []).includes(condition)} />
                          <ListItemText primary={condition} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.medicalHistory && <FormHelperText>{errors.medicalHistory}</FormHelperText>}
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth error={!!errors.medications}>
                    <InputLabel>Current Medications</InputLabel>
                    <Select
                      multiple
                      value={profile.medications || []}
                      onChange={(e) => handleInputChange('medications', e.target.value)}
                      label="Current Medications"
                      renderValue={(selected) => (selected as string[]).join(', ')}
                    >
                      {[
                        'Metformin',
                        'Insulin',
                        'Sulfonylureas',
                        'DPP-4 inhibitors',
                        'GLP-1 agonists',
                        'SGLT-2 inhibitors',
                        'ACE inhibitors',
                        'Statins',
                        'Other'
                      ].map((medication) => (
                        <MenuItem key={medication} value={medication}>
                          <Checkbox checked={(profile.medications || []).includes(medication)} />
                          <ListItemText primary={medication} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.medications && <FormHelperText>{errors.medications}</FormHelperText>}
                  </FormControl>
                </Grid>
              </Grid>
            </Collapse>
          </CardContent>
        </Card>

        {/* Vital Signs Section */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" component="h2">
                Vital Signs
              </Typography>
              <IconButton onClick={() => toggleSection('vitals')}>
                {expandedSections.vitals ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expandedSections.vitals}>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Height (cm)"
                    type="number"
                    value={profile.vitalSigns?.heightCm || ''}
                    onChange={(e) => handleInputChange('vitalSigns', parseFloat(e.target.value) || undefined, 'heightCm')}
                    error={!!errors.vitalSigns?.heightCm}
                    helperText={errors.vitalSigns?.heightCm}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Weight (kg)"
                    type="number"
                    value={profile.vitalSigns?.weightKg || ''}
                    onChange={(e) => handleInputChange('vitalSigns', parseFloat(e.target.value) || undefined, 'weightKg')}
                    error={!!errors.vitalSigns?.weightKg}
                    helperText={errors.vitalSigns?.weightKg}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="BMI"
                    type="number"
                    value={profile.vitalSigns?.bmi || ''}
                    onChange={(e) => handleInputChange('vitalSigns', parseFloat(e.target.value) || undefined, 'bmi')}
                    error={!!errors.vitalSigns?.bmi}
                    helperText={errors.vitalSigns?.bmi || 'Auto-calculated from height and weight'}
                    InputProps={{ readOnly: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Systolic BP (mmHg)"
                    type="number"
                    value={profile.vitalSigns?.bloodPressureSystolic || ''}
                    onChange={(e) => handleInputChange('vitalSigns', parseFloat(e.target.value) || undefined, 'bloodPressureSystolic')}
                    error={!!errors.vitalSigns?.bloodPressureSystolic}
                    helperText={errors.vitalSigns?.bloodPressureSystolic}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Diastolic BP (mmHg)"
                    type="number"
                    value={profile.vitalSigns?.bloodPressureDiastolic || ''}
                    onChange={(e) => handleInputChange('vitalSigns', parseFloat(e.target.value) || undefined, 'bloodPressureDiastolic')}
                    error={!!errors.vitalSigns?.bloodPressureDiastolic}
                    helperText={errors.vitalSigns?.bloodPressureDiastolic}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Heart Rate (bpm)"
                    type="number"
                    value={profile.vitalSigns?.heartRateBpm || ''}
                    onChange={(e) => handleInputChange('vitalSigns', parseFloat(e.target.value) || undefined, 'heartRateBpm')}
                    error={!!errors.vitalSigns?.heartRateBpm}
                    helperText={errors.vitalSigns?.heartRateBpm}
                  />
                </Grid>
              </Grid>
            </Collapse>
          </CardContent>
        </Card>

        {/* Physical Activity Section */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" component="h2">
                Physical Activity
              </Typography>
              <IconButton onClick={() => toggleSection('physical')}>
                {expandedSections.physical ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expandedSections.physical}>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth error={!!errors.physicalActivity?.workActivityLevel}>
                    <InputLabel>Work Activity Level</InputLabel>
                    <Select
                      value={profile.physicalActivity?.workActivityLevel || ''}
                      onChange={(e) => handleInputChange('physicalActivity', e.target.value, 'workActivityLevel')}
                      label="Work Activity Level"
                    >
                      <MenuItem value="Sedentary">Sedentary</MenuItem>
                      <MenuItem value="Light">Light</MenuItem>
                      <MenuItem value="Moderate">Moderate</MenuItem>
                      <MenuItem value="Heavy">Heavy</MenuItem>
                    </Select>
                    {errors.physicalActivity?.workActivityLevel && (
                      <FormHelperText>{errors.physicalActivity.workActivityLevel}</FormHelperText>
                    )}
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth error={!!errors.physicalActivity?.exerciseFrequency}>
                    <InputLabel>Exercise Frequency</InputLabel>
                    <Select
                      value={profile.physicalActivity?.exerciseFrequency || ''}
                      onChange={(e) => handleInputChange('physicalActivity', e.target.value, 'exerciseFrequency')}
                      label="Exercise Frequency"
                    >
                      <MenuItem value="None">None</MenuItem>
                      <MenuItem value="1-2 times/week">1-2 times/week</MenuItem>
                      <MenuItem value="3-4 times/week">3-4 times/week</MenuItem>
                      <MenuItem value="5+ times/week">5+ times/week</MenuItem>
                    </Select>
                    {errors.physicalActivity?.exerciseFrequency && (
                      <FormHelperText>{errors.physicalActivity.exerciseFrequency}</FormHelperText>
                    )}
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth error={!!errors.physicalActivity?.exerciseTypes}>
                    <InputLabel>Exercise Types</InputLabel>
                    <Select
                      multiple
                      value={profile.physicalActivity?.exerciseTypes || []}
                      onChange={(e) => handleInputChange('physicalActivity', e.target.value, 'exerciseTypes')}
                      label="Exercise Types"
                      renderValue={(selected) => (selected as string[]).join(', ')}
                    >
                      {[
                        'Walking',
                        'Running',
                        'Swimming',
                        'Cycling',
                        'Weight Training',
                        'Yoga',
                        'Other'
                      ].map((type) => (
                        <MenuItem key={type} value={type}>
                          <Checkbox checked={(profile.physicalActivity?.exerciseTypes || []).includes(type)} />
                          <ListItemText primary={type} />
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.physicalActivity?.exerciseTypes && (
                      <FormHelperText>{errors.physicalActivity.exerciseTypes}</FormHelperText>
                    )}
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={profile.physicalActivity?.mobilityIssues || false}
                        onChange={(e) => handleInputChange('physicalActivity', e.target.checked, 'mobilityIssues')}
                      />
                    }
                    label="Has mobility issues"
                  />
                </Grid>
              </Grid>
            </Collapse>
          </CardContent>
        </Card>

        {/* Meal Plan Targeting Section */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" component="h2">
                Meal Plan Targeting
              </Typography>
              <IconButton onClick={() => toggleSection('targeting')}>
                {expandedSections.targeting ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
            <Collapse in={expandedSections.targeting}>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={profile.mealPlanTargeting?.wantsWeightLoss || false}
                        onChange={(e) => handleInputChange('mealPlanTargeting', e.target.checked, 'wantsWeightLoss')}
                      />
                    }
                    label="Wants weight loss"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Calorie Target"
                    type="number"
                    value={profile.mealPlanTargeting?.calorieTarget || ''}
                    onChange={(e) => handleInputChange('mealPlanTargeting', parseInt(e.target.value) || undefined, 'calorieTarget')}
                    error={!!errors.mealPlanTargeting?.calorieTarget}
                    helperText={errors.mealPlanTargeting?.calorieTarget}
                  />
                </Grid>
              </Grid>
            </Collapse>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleSubmit}
            disabled={saving}
            sx={{ minWidth: 200 }}
          >
            {saving ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Saving...
              </>
            ) : (
              `${mode === 'admin' ? 'Save Profile' : 'Update Profile'}`
            )}
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default PatientProfileForm; 