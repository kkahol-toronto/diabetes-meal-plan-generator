import React, { useState, useEffect, ReactNode } from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
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
  Checkbox,
  ListItemText,
  CircularProgress,
  Alert,
  FormControlLabel,
  SelectChangeEvent,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

// Comprehensive UserProfile interface with all requested fields
interface UserProfile {
  // Patient Demographics
  fullName: string;
  dateOfBirth: string;         // yyyy-MM-dd
  age: number;
  sex: 'Male' | 'Female' | 'Other' | '';
  ethnicity: string[];         // multi-select

  // Medical History (multi-select)
  medicalHistory: string[];

  // Current Medications (multi-select or free text for "Other")
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

  // Dietary Information
  typeOfDiet: string;          // single-select
  dietaryFeatures: string[];   // multi-select
  dietaryAllergies: string;    // free text for "Other" (if any)
  strongDislikes: string;      // free text

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

  // Goals & Readiness to Change
  primaryGoals: string[];      // multi-select
  readinessToChange: string;   // single-select

  // Meal Plan Targeting
  weightLossDesired: boolean;
  suggestedCalorieTarget: number | string | null;
  suggestedCalorieOther: number | null; // if "Other" chosen
}

const emptyProfile: UserProfile = {
  // Patient Demographics
  fullName: '',
  dateOfBirth: '',
  age: 0,
  sex: '',
  ethnicity: [],

  // Medical History
  medicalHistory: [],

  // Current Medications
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

  // Dietary Information
  typeOfDiet: '',
  dietaryFeatures: [],
  dietaryAllergies: '',
  strongDislikes: '',

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
  suggestedCalorieTarget: null,
  suggestedCalorieOther: null,
};

interface UserProfileFormProps {
  onSubmit?: (profile: UserProfile) => Promise<void>;
  initialProfile?: Partial<UserProfile>;
  mode?: 'user' | 'admin';
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ 
  onSubmit, 
  initialProfile, 
  mode = 'user' 
}) => {
  const [formData, setFormData] = useState<UserProfile>(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Generic handleChange function for all inputs
  function handleChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | { name?: string; value: unknown }> | SelectChangeEvent<unknown>,
    child?: ReactNode
  ) {
    const target = event.target as HTMLInputElement & { name?: keyof UserProfile; value: unknown };
    const name = target.name as keyof UserProfile;
    let value: unknown = target.value;

    // Special cases:
    // 1) For checkboxes (like mobilityIssues), you will get event.target.checked instead of event.target.value.
    // 2) For the "weightLossDesired" boolean checkbox:
    if (name === 'mobilityIssues' || name === 'weightLossDesired') {
      value = (event.target as HTMLInputElement).checked;
    }

    // 3) Automatically recalc age when dateOfBirth changes:
    if (name === 'dateOfBirth') {
      const dob = (event.target as HTMLInputElement).value as string;
      const birthDate = new Date(dob);
      const today = new Date();
      let computedAge = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        computedAge--;
      }
      setFormData((prev) => ({
        ...prev,
        dateOfBirth: dob,
        age: computedAge,
      }));
      return;
    }

    // 4) Automatically recalc BMI when both height & weight are set:
    if (name === 'height' || name === 'weight') {
      const newHeight = name === 'height' ? Number(value) : (formData.height ?? 0);
      const newWeight = name === 'weight' ? Number(value) : (formData.weight ?? 0);
      let newBmi: number | null = null;
      if (newHeight && newWeight) {
        // BMI formula: weight(kg) / [height(m)]^2
        const heightM = newHeight / 100;
        newBmi = parseFloat((newWeight / (heightM * heightM)).toFixed(1));
      }
      setFormData((prev) => ({
        ...prev,
        [name]: Number(value),
        bmi: newBmi,
      }));
      return;
    }

    // 5) For any multi-select (string[]), MUI will pass an array of values:
    //    No extra handling needed; just store it.
    // 6) For number fields (lab values, blood pressures, heartRate, suggestedCalorieTarget, etc.),
    //    coerce value to Number or null if empty string.
    let coercedValue: any = value;
    const numericFields: (keyof UserProfile)[] = [
      'a1c','fastingGlucose','ldl','hdl','triglycerides','totalCholesterol',
      'egfr','creatinine','potassium','uacr','altAst','vitaminD','b12',
      'bloodPressureSys','bloodPressureDia','heartRate','suggestedCalorieTarget','suggestedCalorieOther'
    ];
    if (numericFields.includes(name)) {
      // If user leaves the field blank, store null
      coercedValue = (value === '' || value === null) ? null : Number(value);
    }

    setFormData((prev) => ({
      ...prev,
      [name]: coercedValue,
    }));
  }

  // Load profile data on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        if (mode === 'admin' && initialProfile) {
          setFormData({ ...emptyProfile, ...initialProfile });
        } else if (mode === 'user') {
          const response = await fetch('http://localhost:8000/api/profile/get', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          });
          
          if (response.status === 404) {
            // No existing profile, keep empty form
            console.log('No existing profile found');
          } else if (response.ok) {
            const data = await response.json();
            setFormData({ ...emptyProfile, ...data });
          } else {
            throw new Error(`Failed to load profile: ${response.status}`);
          }
        }
      } catch (err) {
        console.error('Error loading profile:', err);
        setError('Failed to load profile data');
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, [mode, initialProfile]);

  // Handle form submission
  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      if (onSubmit) {
        await onSubmit(formData);
        setSuccess('Profile saved successfully!');
      } else {
        const res = await fetch('http://localhost:8000/api/profile/save', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify(formData),
        });
        if (res.status === 422) {
          const errJson = await res.json();
          setError('Validation error: ' + JSON.stringify(errJson));
          return;
        }
        if (!res.ok) {
          throw new Error(`Status ${res.status}`);
        }
        setSuccess('Profile saved successfully!');
      }
    } catch (err) {
      console.error('Error saving profile:', err);
      setError('Error saving profile: ' + err);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return (
    <Container maxWidth="md">
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading...</Typography>
      </Box>
    </Container>
  );

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" gutterBottom>
          Comprehensive Patient Profile
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <form onSubmit={handleSave} style={{ maxWidth: 800, margin: 'auto' }}>
          {/* 1. Patient Demographics */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Patient Demographics</Typography>
          <TextField
            fullWidth
            label="Full Name"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Date of Birth"
            name="dateOfBirth"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={formData.dateOfBirth}
            onChange={handleChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Age"
            name="age"
            type="number"
            value={formData.age}
            disabled
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel id="sex-label">Sex</InputLabel>
            <Select
              labelId="sex-label"
              id="sex"
              name="sex"
              value={formData.sex}
              onChange={handleChange}
              label="Sex"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="Male">Male</MenuItem>
              <MenuItem value="Female">Female</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="ethnicity-label">Ethnicity (select all that apply)</InputLabel>
            <Select
              labelId="ethnicity-label"
              id="ethnicity"
              name="ethnicity"
              multiple
              value={formData.ethnicity}
              onChange={handleChange}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
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
                'Other',
              ].map((opt) => (
                <MenuItem key={opt} value={opt}>
                  <Checkbox checked={formData.ethnicity.indexOf(opt) > -1} />
                  <ListItemText primary={opt} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* 2. Medical History */}
          <Accordion sx={{ mt: 4 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h5">Medical History (check all that apply)</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <FormControl component="fieldset">
                {[
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
                  'Other',
                ].map((item) => (
                  <FormControlLabel
                    key={item}
                    control={
                      <Checkbox
                        checked={formData.medicalHistory.indexOf(item) > -1}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          setFormData((prev) => {
                            const mh = new Set(prev.medicalHistory);
                            if (checked) mh.add(item);
                            else mh.delete(item);
                            return { ...prev, medicalHistory: Array.from(mh) };
                          });
                        }}
                        name="medicalHistory"
                        value={item}
                      />
                    }
                    label={item}
                  />
                ))}
              </FormControl>
            </AccordionDetails>
          </Accordion>

          {/* 3. Current Medications */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Current Medications</Typography>
          <FormControl component="fieldset" margin="normal">
            {[
              'Metformin',
              'Insulin',
              'GLP-1 agonist (e.g., Ozempic, Trulicity)',
              'SGLT2 inhibitor (e.g., Jardiance, Farxiga)',
              'Statin',
              'Diuretic',
              'Thyroid hormone',
              'Antihypertensives',
              'Anticoagulants (e.g., Aspirin, Eliquis)',
              'Other',
            ].map((med) => (
              <FormControlLabel
                key={med}
                control={
                  <Checkbox
                    checked={formData.currentMedications.indexOf(med) > -1}
                    onChange={(e) => {
                      const checked = e.target.checked;
                      setFormData((prev) => {
                        const meds = new Set(prev.currentMedications);
                        if (checked) meds.add(med);
                        else meds.delete(med);
                        return { ...prev, currentMedications: Array.from(meds) };
                      });
                    }}
                    name="currentMedications"
                    value={med}
                  />
                }
                label={med}
              />
            ))}
          </FormControl>

          {/* 4. Most Recent Lab Values */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Most Recent Lab Values (Optional)</Typography>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <TextField
              label="A1C (%)"
              name="a1c"
              type="number"
              value={formData.a1c ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="Fasting Glucose (mmol/L)"
              name="fastingGlucose"
              type="number"
              value={formData.fastingGlucose ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="LDL-C (mmol/L)"
              name="ldl"
              type="number"
              value={formData.ldl ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="HDL-C (mmol/L)"
              name="hdl"
              type="number"
              value={formData.hdl ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="Triglycerides (mmol/L)"
              name="triglycerides"
              type="number"
              value={formData.triglycerides ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="Total Cholesterol (mmol/L)"
              name="totalCholesterol"
              type="number"
              value={formData.totalCholesterol ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="eGFR"
              name="egfr"
              type="number"
              value={formData.egfr ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="Creatinine (µmol/L)"
              name="creatinine"
              type="number"
              value={formData.creatinine ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="Potassium (mmol/L)"
              name="potassium"
              type="number"
              value={formData.potassium ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="uACR / proteinuria"
              name="uacr"
              type="number"
              value={formData.uacr ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="ALT / AST"
              name="altAst"
              type="number"
              value={formData.altAst ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="Vitamin D (nmol/L)"
              name="vitaminD"
              type="number"
              value={formData.vitaminD ?? ''}
              onChange={handleChange}
              margin="normal"
            />
            <TextField
              label="B12 (pmol/L)"
              name="b12"
              type="number"
              value={formData.b12 ?? ''}
              onChange={handleChange}
              margin="normal"
            />
          </div>

          {/* 5. Vital Signs */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Vital Signs</Typography>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <TextField
              label="Height (cm)"
              name="height"
              type="number"
              value={formData.height ?? ''}
              onChange={handleChange}
              margin="normal"
              style={{ flex: 1 }}
            />
            <TextField
              label="Weight (kg)"
              name="weight"
              type="number"
              value={formData.weight ?? ''}
              onChange={handleChange}
              margin="normal"
              style={{ flex: 1 }}
            />
            <TextField
              label="BMI"
              name="bmi"
              type="number"
              value={formData.bmi ?? ''}
              disabled
              margin="normal"
              style={{ flex: 1 }}
            />
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <TextField
              label="Blood Pressure (Sys)"
              name="bloodPressureSys"
              type="number"
              value={formData.bloodPressureSys ?? ''}
              onChange={handleChange}
              margin="normal"
              style={{ flex: 1 }}
            />
            <TextField
              label="Blood Pressure (Dia)"
              name="bloodPressureDia"
              type="number"
              value={formData.bloodPressureDia ?? ''}
              onChange={handleChange}
              margin="normal"
              style={{ flex: 1 }}
            />
            <TextField
              label="Heart Rate (bpm)"
              name="heartRate"
              type="number"
              value={formData.heartRate ?? ''}
              onChange={handleChange}
              margin="normal"
              style={{ flex: 1 }}
            />
          </div>

          {/* 6. Dietary Information */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Dietary Information</Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel id="typeOfDiet-label">Type of Diet</InputLabel>
            <Select
              labelId="typeOfDiet-label"
              id="typeOfDiet"
              name="typeOfDiet"
              value={formData.typeOfDiet}
              onChange={handleChange}
              label="Type of Diet"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="Western">Western</MenuItem>
              <MenuItem value="Mediterranean">Mediterranean</MenuItem>
              <MenuItem value="South Asian – North Indian">South Asian – North Indian</MenuItem>
              <MenuItem value="South Asian – Pakistani">South Asian – Pakistani</MenuItem>
              <MenuItem value="South Asian – Sri Lankan">South Asian – Sri Lankan</MenuItem>
              <MenuItem value="South Asian – South Indian">South Asian – South Indian</MenuItem>
              <MenuItem value="East Asian – Chinese / Korean">East Asian – Chinese / Korean</MenuItem>
              <MenuItem value="Caribbean – Jamaican / Guyanese">Caribbean – Jamaican / Guyanese</MenuItem>
              <MenuItem value="Filipino">Filipino</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="dietaryFeatures-label">Current Dietary Features</InputLabel>
            <Select
              labelId="dietaryFeatures-label"
              id="dietaryFeatures"
              name="dietaryFeatures"
              multiple
              value={formData.dietaryFeatures}
              onChange={handleChange}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
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
                'Food Allergies',
                'Strong Dislikes',
              ].map((opt) => (
                <MenuItem key={opt} value={opt}>
                  <Checkbox checked={formData.dietaryFeatures.indexOf(opt) > -1} />
                  <ListItemText primary={opt} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Food Allergies (if any)"
            name="dietaryAllergies"
            value={formData.dietaryAllergies}
            onChange={handleChange}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Strong Dislikes"
            name="strongDislikes" 
            value={formData.strongDislikes}
            onChange={handleChange}
            margin="normal"
          />

          {/* 7. Physical Activity Profile */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Physical Activity Profile</Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel id="workActivity-label">Work Activity Level</InputLabel>
            <Select
              labelId="workActivity-label"
              id="workActivity"
              name="workActivity"
              value={formData.workActivity}
              onChange={handleChange}
              label="Work Activity Level"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="Sedentary">Sedentary (e.g., desk work)</MenuItem>
              <MenuItem value="Moderately Active">Moderately Active (e.g., walking, light lifting)</MenuItem>
              <MenuItem value="Active">Active / Physical Labor</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="exerciseFrequency-label">Exercise Frequency</InputLabel>
            <Select
              labelId="exerciseFrequency-label"
              id="exerciseFrequency"
              name="exerciseFrequency"
              value={formData.exerciseFrequency}
              onChange={handleChange}
              label="Exercise Frequency"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="None">None</MenuItem>
              <MenuItem value="<30–60">&lt;30–60 min/week</MenuItem>
              <MenuItem value="60–150">60–150 min/week</MenuItem>
              <MenuItem value=">150">&gt;150 min/week</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="exerciseTypes-label">Type of Exercise (select all that apply)</InputLabel>
            <Select
              labelId="exerciseTypes-label"
              id="exerciseTypes"
              name="exerciseTypes"
              multiple
              value={formData.exerciseTypes}
              onChange={handleChange}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Walking',
                'Jogging',
                'Resistance training / weights',
                'Yoga / Pilates',
                'Swimming',
                'Cycling (indoor/outdoor)',
                'Fitness classes (e.g., Zumba, aerobics)',
                'Home workouts',
                'Other',
              ].map((opt) => (
                <MenuItem key={opt} value={opt}>
                  <Checkbox checked={formData.exerciseTypes.indexOf(opt) > -1} />
                  <ListItemText primary={opt} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.mobilityIssues}
                onChange={handleChange}
                name="mobilityIssues"
              />
            }
            label="Mobility / Joint Issues"
          />

          {/* 8. Lifestyle & Preferences */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Lifestyle & Preferences</Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel id="mealPrepCapability-label">Meal Prep Capability</InputLabel>
            <Select
              labelId="mealPrepCapability-label"
              id="mealPrepCapability"
              name="mealPrepCapability"
              value={formData.mealPrepCapability}
              onChange={handleChange}
              label="Meal Prep Capability"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="Prepares own meals">Prepares own meals</MenuItem>
              <MenuItem value="Cooks with assistance">Cooks with assistance</MenuItem>
              <MenuItem value="Caregiver-prepared">Caregiver-prepared</MenuItem>
              <MenuItem value="Uses meal delivery service">Uses meal delivery service</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="appliances-label">Appliances Available (select all that apply)</InputLabel>
            <Select
              labelId="appliances-label"
              id="appliances"
              name="appliances"
              multiple
              value={formData.appliances}
              onChange={handleChange}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {['Fridge & Freezer', 'Microwave', 'Instant Pot', 'Air Fryer', 'Blender', 'Other'].map((opt) => (
                <MenuItem key={opt} value={opt}>
                  <Checkbox checked={formData.appliances.indexOf(opt) > -1} />
                  <ListItemText primary={opt} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="eatingSchedule-label">Eating Schedule Preference</InputLabel>
            <Select
              labelId="eatingSchedule-label"
              id="eatingSchedule"
              name="eatingSchedule"
              value={formData.eatingSchedule}
              onChange={handleChange}
              label="Eating Schedule Preference"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="3 meals/day">3 meals/day</MenuItem>
              <MenuItem value="2 meals + 1 snack">2 meals + 1 snack</MenuItem>
              <MenuItem value="Intermittent Fasting">Intermittent Fasting</MenuItem>
              <MenuItem value="Night Shift (11 pm–7 am)">Night Shift (11 pm–7 am)</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>
          {formData.eatingSchedule === 'Other' && (
            <TextField
              fullWidth
              label="If Other, specify"
              name="eatingScheduleOther"
              value={formData.eatingScheduleOther}
              onChange={handleChange}
              margin="normal"
            />
          )}

          {/* 9. Goals & Readiness to Change */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Goals & Readiness to Change</Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel id="primaryGoals-label">Primary Goals (select all that apply)</InputLabel>
            <Select
              labelId="primaryGoals-label"
              id="primaryGoals"
              name="primaryGoals"
              multiple
              value={formData.primaryGoals}
              onChange={handleChange}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Weight loss',
                'Improve A1C',
                'Lower cholesterol / triglycerides',
                'Improve energy / stamina',
                'Reduce blood pressure',
                'Improve digestion',
                'General wellness',
                'Other',
              ].map((opt) => (
                <MenuItem key={opt} value={opt}>
                  <Checkbox checked={formData.primaryGoals.indexOf(opt) > -1} />
                  <ListItemText primary={opt} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel id="readinessToChange-label">Readiness to Change</InputLabel>
            <Select
              labelId="readinessToChange-label"
              id="readinessToChange"
              name="readinessToChange"
              value={formData.readinessToChange}
              onChange={handleChange}
              label="Readiness to Change"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value="Not ready">Not ready</MenuItem>
              <MenuItem value="Thinking about it">Thinking about it</MenuItem>
              <MenuItem value="Ready to take action">Ready to take action</MenuItem>
              <MenuItem value="Already making changes">Already making changes</MenuItem>
            </Select>
          </FormControl>

          {/* 10. Meal Plan Targeting */}
          <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Meal Plan Targeting</Typography>
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.weightLossDesired}
                onChange={handleChange}
                name="weightLossDesired"
              />
            }
            label="Patient wants weight loss"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel id="suggestedCalorieTarget-label">Suggested Calorie Target</InputLabel>
            <Select
              labelId="suggestedCalorieTarget-label"
              id="suggestedCalorieTarget"
              name="suggestedCalorieTarget"
              value={formData.suggestedCalorieTarget ?? ''}
              onChange={handleChange}
              label="Suggested Calorie Target"
            >
              <MenuItem value=""><em>None</em></MenuItem>
              <MenuItem value={1500}>1500 kcal</MenuItem>
              <MenuItem value={1800}>1800 kcal</MenuItem>
              <MenuItem value={2000}>2000 kcal</MenuItem>
              <MenuItem value={2200}>2200 kcal</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>
          {formData.suggestedCalorieTarget === 'Other' && (
            <TextField
              fullWidth
              label="If Other, specify calorie target"
              name="suggestedCalorieOther"
              type="number"
              value={formData.suggestedCalorieOther ?? ''}
              onChange={handleChange}
              margin="normal"
            />
          )}

          {/* Save Button */}
          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
            <Button 
              type="submit" 
              variant="contained" 
              size="large"
              disabled={saving}
              sx={{ minWidth: 200 }}
            >
              {saving ? <CircularProgress size={24} /> : 'Save Profile'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Container>
  );
};

export default UserProfileForm;
