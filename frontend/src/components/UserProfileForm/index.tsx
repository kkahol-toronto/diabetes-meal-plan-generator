import React, { useState, useEffect } from 'react';
import {
  TextField,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  Checkbox,
  ListItemText,
  FormControlLabel,
  Box,
  Typography,
  SelectChangeEvent,
  Button,
  Grid,
  OutlinedInput,
  Switch,
} from '@mui/material';
import { UserProfile, emptyProfile } from '../../types/UserProfile';
import { UserProfileFormProps } from '../../types/UserProfileForm';
import { getPatientProfile, savePatientProfile } from '../../api';

interface FormErrors {
  height?: string;
  weight?: string;
  [key: string]: string | undefined;
}

export default function UserProfileForm({ onSubmit, initialProfile }: UserProfileFormProps) {
  const [formData, setFormData] = useState<UserProfile>(initialProfile || emptyProfile);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<FormErrors>({});

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await getPatientProfile();
        if (response.status === 404) {
          setFormData(emptyProfile);
        } else if (response.ok) {
          const data = await response.json();
          setFormData({ ...emptyProfile, ...data });
        } else {
          throw new Error(`Status ${response.status}`);
        }
      } catch (error) {
        console.error('Error loading profile:', error);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  function handleChange(
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | { name?: string; value: unknown }> | SelectChangeEvent<unknown>
  ) {
    const target = event.target as HTMLInputElement & { name?: keyof UserProfile; value: unknown };
    const name = target.name as keyof UserProfile;
    let value: any = target.value;

    // Special cases:
    // 1) For checkboxes (like mobilityIssues), you will get event.target.checked instead of event.target.value.
    if (name === 'mobilityIssues' || name === 'weightLossDesired' || name === 'wantsWeightLoss') {
      value = (event.target as HTMLInputElement).checked;
    }

    // 2) Automatically recalc age when dateOfBirth changes:
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

    // 3) Automatically recalc BMI when both height & weight are set:
    if (name === 'height' || name === 'weight') {
      const newHeight = name === 'height' ? Number(value) : (formData.height ?? 0);
      const newWeight = name === 'weight' ? Number(value) : (formData.weight ?? 0);
      let newBmi: number | null = null;
      
      // Validate height and weight
      let newErrors = { ...errors };
      if (name === 'height') {
        if (Number(value) < 100 || Number(value) > 250) {
          newErrors.height = 'Height must be between 100cm and 250cm';
        } else {
          delete newErrors.height;
        }
      }
      if (name === 'weight') {
        if (Number(value) < 30 || Number(value) > 300) {
          newErrors.weight = 'Weight must be between 30kg and 300kg';
        } else {
          delete newErrors.weight;
        }
      }
      setErrors(newErrors);

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

    // 4) For any multi-select (string[]), MUI will pass an array of values
    if (Array.isArray(value)) {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
      return;
    }

    // 5) For number fields, coerce value to Number or null if empty string.
    const numericFields: (keyof UserProfile)[] = [
      'a1c','fastingGlucose','ldl','hdl','triglycerides','totalCholesterol',
      'egfr','creatinine','potassium','uacr','altAst','vitaminD','b12',
      'bloodPressureSys','bloodPressureDia','heartRate','suggestedCalorieTarget','suggestedCalorieOther',
      'systolicBP', 'diastolicBP', 'waistCircumference'
    ];
    if (numericFields.includes(name)) {
      value = (value === '' || value === null) ? null : Number(value);
    }

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await savePatientProfile(formData);
      if (res.status === 422) {
        const errJson = await res.json();
        alert('Validation error: ' + JSON.stringify(errJson));
        return;
      }
      if (!res.ok) {
        throw new Error(`Status ${res.status}`);
      }
      if (onSubmit) {
        await onSubmit(formData);
      }
      alert('Profile saved successfully!');
    } catch (err) {
      console.error('Error saving profile:', err);
      alert('Error saving profile: ' + err);
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <Box component="form" onSubmit={handleSave} sx={{ maxWidth: 800, margin: 'auto', p: 2 }}>
      <Grid container spacing={2}>
        {/* 1. Patient Demographics */}
        <Grid item xs={12}>
          <Typography variant="h6">Patient Demographics</Typography>
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            required
            label="Name"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            margin="normal"
          />
        </Grid>
        <Grid item xs={12}>
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
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Age"
            name="age"
            type="number"
            value={formData.age}
            disabled
            margin="normal"
          />
        </Grid>
        <Grid item xs={12}>
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
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth margin="normal">
            <InputLabel id="ethnicity-label">Ethnicity (select all that apply)</InputLabel>
            <Select
              labelId="ethnicity-label"
              id="ethnicity"
              name="ethnicity"
              multiple
              value={formData.ethnicity}
              onChange={handleChange}
              input={<OutlinedInput label="Ethnicity (select all that apply)" />}
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
        </Grid>

        {/* Health Measurements */}
        <Grid item xs={12}>
          <Typography variant="h6">Health Measurements</Typography>
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Height (cm)"
            name="height"
            type="number"
            value={formData.height ?? ''}
            onChange={handleChange}
            error={!!errors.height}
            helperText={errors.height}
            InputProps={{ inputProps: { min: 100, max: 250 } }}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Weight (kg)"
            name="weight"
            type="number"
            value={formData.weight ?? ''}
            onChange={handleChange}
            error={!!errors.weight}
            helperText={errors.weight}
            InputProps={{ inputProps: { min: 30, max: 300 } }}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Waist Circumference (cm)"
            name="waistCircumference"
            type="number"
            value={formData.waistCircumference ?? ''}
            onChange={handleChange}
            InputProps={{ inputProps: { min: 40, max: 200 } }}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Systolic BP"
            name="systolicBP"
            type="number"
            value={formData.systolicBP ?? ''}
            onChange={handleChange}
            InputProps={{ inputProps: { min: 60, max: 250 } }}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Diastolic BP"
            name="diastolicBP"
            type="number"
            value={formData.diastolicBP ?? ''}
            onChange={handleChange}
            InputProps={{ inputProps: { min: 40, max: 150 } }}
          />
        </Grid>

        {/* Medical Information */}
        <Grid item xs={12}>
          <Typography variant="h6">Medical Information</Typography>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Medical Conditions</InputLabel>
            <Select
              multiple
              name="medicalConditions"
              value={formData.medicalConditions}
              onChange={handleChange}
              input={<OutlinedInput label="Medical Conditions" />}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Type 2 Diabetes',
                'Type 1 Diabetes',
                'Hypertension',
                'High Cholesterol',
                'Heart Disease',
                'Other'
              ].map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={formData.medicalConditions.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Dietary Restrictions</InputLabel>
            <Select
              multiple
              name="dietaryRestrictions"
              value={formData.dietaryRestrictions}
              onChange={handleChange}
              input={<OutlinedInput label="Dietary Restrictions" />}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Vegetarian',
                'Vegan',
                'Gluten-Free',
                'Dairy-Free',
                'Kosher',
                'Halal',
                'Other'
              ].map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={formData.dietaryRestrictions.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Food Preferences</InputLabel>
            <Select
              multiple
              name="foodPreferences"
              value={formData.foodPreferences}
              onChange={handleChange}
              input={<OutlinedInput label="Food Preferences" />}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Low Carb',
                'High Protein',
                'Low Fat',
                'Mediterranean',
                'Asian Cuisine',
                'Other'
              ].map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={formData.foodPreferences.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Allergies</InputLabel>
            <Select
              multiple
              name="allergies"
              value={formData.allergies}
              onChange={handleChange}
              input={<OutlinedInput label="Allergies" />}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Peanuts',
                'Tree Nuts',
                'Shellfish',
                'Fish',
                'Eggs',
                'Dairy',
                'Soy',
                'Wheat',
                'Other'
              ].map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={formData.allergies.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Diet Information */}
        <Grid item xs={12}>
          <Typography variant="h6">Diet Information</Typography>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Diet Type</InputLabel>
            <Select
              multiple
              name="dietType"
              value={formData.dietType}
              onChange={handleChange}
              input={<OutlinedInput label="Diet Type" />}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {[
                'Standard',
                'Vegetarian',
                'Vegan',
                'Keto',
                'Paleo',
                'Mediterranean',
                'Other'
              ].map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={formData.dietType.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Calorie Target</InputLabel>
            <Select
              name="calorieTarget"
              value={formData.calorieTarget}
              onChange={handleChange}
              label="Calorie Target"
            >
              <MenuItem value="">Select Calorie Target</MenuItem>
              <MenuItem value="1500">1500 calories</MenuItem>
              <MenuItem value="1800">1800 calories</MenuItem>
              <MenuItem value="2000">2000 calories</MenuItem>
              <MenuItem value="2200">2200 calories</MenuItem>
              <MenuItem value="2500">2500 calories</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.wantsWeightLoss}
                onChange={(e) => setFormData(prev => ({ ...prev, wantsWeightLoss: e.target.checked }))}
                name="wantsWeightLoss"
              />
            }
            label="Weight Loss Goal"
          />
        </Grid>

        {/* 4. Most Recent Lab Values */}
        <Grid item xs={12}>
          <Typography variant="h6">Most Recent Lab Values (Optional)</Typography>
        </Grid>
        <Grid item xs={12}>
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
        </Grid>

        {/* 5. Vital Signs */}
        <Grid item xs={12}>
          <Typography variant="h6">Vital Signs</Typography>
        </Grid>
        <Grid item xs={12}>
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
        </Grid>
        <Grid item xs={12}>
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
        </Grid>
      </Grid>
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading}
        >
          Save Profile
        </Button>
      </Box>
    </Box>
  );
} 