import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Button,
  Chip,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import UserProfileForm from './UserProfileForm';
import { getAdminUserProfile, saveAdminUserProfile } from '../services/api';
import { PatientProfile } from '../types/PatientProfile';
import { UserProfile } from '../types';

const AdminUserProfile: React.FC = () => {
  console.log('AdminUserProfile component rendered');
  const { userId } = useParams<{ userId: string }>();
  console.log("userId param:", userId);
  const navigate = useNavigate();
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  console.log('AdminUserProfile - Component loaded, userId:', userId); // Debug log

  useEffect(() => {
    if (!userId) {
      setError('No user ID provided');
      setLoading(false);
      return;
    }

    fetchUserProfile();
  }, [userId]);

  const fetchUserProfile = async () => {
    if (!userId) return;

    try {
      setLoading(true);
      setError(null);
      
      const userProfile = await getAdminUserProfile(userId);
      setProfile(userProfile);
    } catch (err) {
      console.error('Error fetching user profile:', err);
      
      // Check if it's a 404 error (profile doesn't exist yet)
      if (err instanceof Error && err.message.includes('404')) {
        // This is normal for new patients who haven't filled out their profile yet
        console.log('No profile found for user - showing empty form');
        setProfile(null); // This will show an empty form
        setError(null); // Don't show an error for missing profiles
      } else {
        // This is a real error (network, auth, etc.)
        setError(err instanceof Error ? err.message : 'Failed to load user profile');
      }
    } finally {
      setLoading(false);
    }
  };

  // Convert UserProfile to PatientProfile for saving
  const convertUserProfileToPatientProfile = (userProfile: UserProfile): PatientProfile => {
    return {
      // Demographics
      fullName: userProfile.name,
      fullNameUpdatedBy: 'admin',
      dateOfBirth: userProfile.dateOfBirth,
      dateOfBirthUpdatedBy: 'admin',
      age: userProfile.age,
      ageUpdatedBy: 'admin',
      sex: userProfile.gender as 'Male' | 'Female' | 'Other',
      sexUpdatedBy: 'admin',
      ethnicity: userProfile.ethnicity,
      ethnicityUpdatedBy: 'admin',
      
      // Medical History
      medicalHistory: userProfile.medicalConditions,
      medicalHistoryUpdatedBy: 'admin',
      
      // Medications
      medications: userProfile.currentMedications,
      medicationsUpdatedBy: 'admin',
      
      // Lab Values - convert flat structure to nested
      labValues: userProfile.labValues ? {
        a1c: userProfile.labValues.a1c ? parseFloat(userProfile.labValues.a1c) : undefined,
        fastingGlucose: userProfile.labValues.fastingGlucose ? parseFloat(userProfile.labValues.fastingGlucose) : undefined,
        ldlC: userProfile.labValues.ldlCholesterol ? parseFloat(userProfile.labValues.ldlCholesterol) : undefined,
        hdlC: userProfile.labValues.hdlCholesterol ? parseFloat(userProfile.labValues.hdlCholesterol) : undefined,
        triglycerides: userProfile.labValues.triglycerides ? parseFloat(userProfile.labValues.triglycerides) : undefined,
      } : undefined,
      labValuesUpdatedBy: 'admin',
      
      // Vital Signs
      vitalSigns: {
        heightCm: userProfile.height,
        weightKg: userProfile.weight,
        bmi: userProfile.bmi,
        bloodPressureSystolic: userProfile.systolicBP,
        bloodPressureDiastolic: userProfile.diastolicBP,
        heartRateBpm: userProfile.heartRate,
      },
      vitalSignsUpdatedBy: 'admin',
      
      // Dietary Info
      dietaryInfo: {
        dietType: userProfile.dietType?.join(', '),
        dietFeatures: userProfile.dietaryFeatures,
        allergies: userProfile.allergies?.join(', '),
        dislikes: userProfile.strongDislikes?.join(', '),
      },
      dietaryInfoUpdatedBy: 'admin',
      
      // Physical Activity
      physicalActivity: {
        workActivityLevel: userProfile.workActivityLevel as any,
        exerciseFrequency: userProfile.exerciseFrequency as any,
        exerciseTypes: userProfile.exerciseTypes,
        mobilityIssues: userProfile.mobilityIssues,
      },
      physicalActivityUpdatedBy: 'admin',
      
      // Lifestyle
      lifestyle: {
        mealPrepMethod: userProfile.mealPrepCapability as any,
        availableAppliances: userProfile.availableAppliances,
        eatingSchedule: userProfile.eatingSchedule as any,
      },
      lifestyleUpdatedBy: 'admin',
      
      // Goals
      goals: userProfile.primaryGoals,
      goalsUpdatedBy: 'admin',
      readiness: userProfile.readinessToChange as any,
      readinessUpdatedBy: 'admin',
      
      // Meal Plan Targeting
      mealPlanTargeting: {
        wantsWeightLoss: userProfile.wantsWeightLoss,
        calorieTarget: userProfile.calorieTarget ? parseInt(userProfile.calorieTarget) : undefined,
      },
      mealPlanTargetingUpdatedBy: 'admin',
      
      // Set intake date if not already set
      intakeDate: new Date().toISOString().split('T')[0],
      intakeDateUpdatedBy: 'admin',
    };
  };

  // Convert PatientProfile to UserProfile for display
  const convertPatientProfileToUserProfile = (patientProfile: PatientProfile): UserProfile => {
    return {
      name: patientProfile.fullName || '',
      dateOfBirth: patientProfile.dateOfBirth || '',
      age: patientProfile.age,
      gender: patientProfile.sex || '',
      ethnicity: patientProfile.ethnicity || [],
      medicalConditions: patientProfile.medicalHistory || [],
      currentMedications: patientProfile.medications || [],
      labValues: patientProfile.labValues ? {
        a1c: patientProfile.labValues.a1c?.toString(),
        fastingGlucose: patientProfile.labValues.fastingGlucose?.toString(),
        ldlCholesterol: patientProfile.labValues.ldlC?.toString(),
        hdlCholesterol: patientProfile.labValues.hdlC?.toString(),
        triglycerides: patientProfile.labValues.triglycerides?.toString(),
      } : {},
      height: patientProfile.vitalSigns?.heightCm || 0,
      weight: patientProfile.vitalSigns?.weightKg || 0,
      bmi: patientProfile.vitalSigns?.bmi,
      waistCircumference: undefined,
      systolicBP: patientProfile.vitalSigns?.bloodPressureSystolic,
      diastolicBP: patientProfile.vitalSigns?.bloodPressureDiastolic,
      heartRate: patientProfile.vitalSigns?.heartRateBpm,
      dietType: patientProfile.dietaryInfo?.dietType ? [patientProfile.dietaryInfo.dietType] : [],
      dietaryFeatures: patientProfile.dietaryInfo?.dietFeatures || [],
      dietaryRestrictions: [],
      foodPreferences: [],
      allergies: patientProfile.dietaryInfo?.allergies ? [patientProfile.dietaryInfo.allergies] : [],
      strongDislikes: patientProfile.dietaryInfo?.dislikes ? [patientProfile.dietaryInfo.dislikes] : [],
      workActivityLevel: patientProfile.physicalActivity?.workActivityLevel || '',
      exerciseFrequency: patientProfile.physicalActivity?.exerciseFrequency || '',
      exerciseTypes: patientProfile.physicalActivity?.exerciseTypes || [],
      mobilityIssues: patientProfile.physicalActivity?.mobilityIssues || false,
      mealPrepCapability: patientProfile.lifestyle?.mealPrepMethod || '',
      availableAppliances: patientProfile.lifestyle?.availableAppliances || [],
      eatingSchedule: patientProfile.lifestyle?.eatingSchedule || '',
      primaryGoals: patientProfile.goals || [],
      readinessToChange: patientProfile.readiness || '',
      wantsWeightLoss: patientProfile.mealPlanTargeting?.wantsWeightLoss || false,
      calorieTarget: patientProfile.mealPlanTargeting?.calorieTarget?.toString() || '',
    };
  };

  const handleProfileSubmit = async (updatedProfile: UserProfile) => {
    if (!userId) return;

    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);

      // Convert UserProfile to PatientProfile for saving
      const patientProfile = convertUserProfileToPatientProfile(updatedProfile);
      const success = await saveAdminUserProfile(userId, patientProfile);
      
      if (success) {
        setSaveSuccess(true);
        setProfile(patientProfile);
        // Clear success message after 3 seconds
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        setError('Failed to save profile');
      }
    } catch (err) {
      console.error('Error saving user profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to save user profile');
    } finally {
      setSaving(false);
    }
  };

  const handleGoBack = () => {
    navigate('/admin');
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading user profile...
          </Typography>
        </Paper>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={handleGoBack}
              sx={{ mr: 2 }}
            >
              Back to Admin Panel
            </Button>
          </Box>
          <Alert severity="error">
            {error}
          </Alert>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={handleGoBack}
              sx={{ mr: 2 }}
            >
              Back to Admin Panel
            </Button>
            <Box>
              <Typography variant="h4" component="h1">
                User Profile
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="subtitle1" color="text.secondary">
                  User ID: {userId}
                </Typography>
                <Chip
                  label="Admin View"
                  color="primary"
                  size="small"
                  sx={{ ml: 2 }}
                />
              </Box>
              {profile?.fullName ? (
                <Typography variant="subtitle1" color="text.secondary">
                  Name: {profile.fullName}
                </Typography>
              ) : (
                <Typography variant="subtitle1" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No profile data yet - creating new profile
                </Typography>
              )}
            </Box>
          </Box>
        </Box>

        {/* Success/Error Messages */}
        {saveSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Profile saved successfully!
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Info message for new profiles */}
        {!profile && !error && (
          <Alert severity="info" sx={{ mb: 2 }}>
            This patient hasn't filled out their profile yet. You can create their initial profile below.
          </Alert>
        )}

        {/* Loading Indicator for Save */}
        {saving && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Saving profile...
            </Typography>
          </Box>
        )}

        {/* Profile Form */}
        <UserProfileForm
          onSubmit={handleProfileSubmit}
          initialProfile={profile ? convertPatientProfileToUserProfile(profile) : undefined}
          mode="admin"
        />
      </Paper>
    </Container>
  );
};

export default AdminUserProfile; 