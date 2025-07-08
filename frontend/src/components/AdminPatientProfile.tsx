import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link,
  Chip,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PersonIcon from '@mui/icons-material/Person';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import UserProfileForm from './UserProfileForm';
import { UserProfile } from '../types';

interface Patient {
  id: string;
  name: string;
  phone: string;
  condition: string;
  registration_code: string;
  created_at: string;
}

const AdminPatientProfile = () => {
  const navigate = useNavigate();
  const { registrationCode } = useParams<{ registrationCode: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (registrationCode) {
      fetchPatientData();
    }
  }, [registrationCode]);

  const fetchPatientData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch patient info
      const patientResponse = await fetch(`http://localhost:8000/admin/patient/${registrationCode}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!patientResponse.ok) {
        throw new Error('Failed to fetch patient data');
      }

      const patientData = await patientResponse.json();
      setPatient(patientData);

      // Try to fetch existing profile if patient has registered
      try {
        const profileResponse = await fetch(`http://localhost:8000/admin/patient-profile/${registrationCode}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (profileResponse.ok) {
          const profileData = await profileResponse.json();
          setUserProfile(profileData.profile);
        } else if (profileResponse.status === 404) {
          // Patient hasn't created a profile yet - that's ok
          setUserProfile(null);
        } else {
          console.warn('Failed to fetch patient profile');
        }
      } catch (profileError) {
        console.warn('Error fetching patient profile:', profileError);
        // Continue without profile - admin can create one
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patient data');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (profile: UserProfile) => {
    try {
      setSaving(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/admin/patient-profile/${registrationCode}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ profile }),
      });

      if (response.ok) {
        setSuccess('✅ Patient profile saved successfully! The patient can continue filling out any missing information.');
        setUserProfile(profile);
        setTimeout(() => setSuccess(null), 6000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save patient profile');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save patient profile');
    } finally {
      setSaving(false);
    }
  };

  const getProfileCompletionStatus = () => {
    if (!userProfile) return { percentage: 0, status: 'Not Started', color: 'default' as const };
    
    // Comprehensive profile completion checking
    const profileSections = {
      demographics: {
        fields: ['name', 'age', 'gender'],
        weight: 0.2
      },
      vitals: {
        fields: ['height', 'weight'],
        weight: 0.15
      },
      medical: {
        fields: ['medicalConditions', 'currentMedications'],
        arrayFields: true,
        weight: 0.25
      },
      dietary: {
        fields: ['dietType', 'dietaryRestrictions', 'allergies', 'foodPreferences'],
        arrayFields: true,
        weight: 0.2
      },
      lifestyle: {
        fields: ['exerciseFrequency', 'mealPrepCapability'],
        weight: 0.1
      },
      goals: {
        fields: ['primaryGoals', 'calorieTarget'],
        arrayFields: true,
        weight: 0.1
      }
    };

    let totalScore = 0;
    let maxScore = 0;

    Object.entries(profileSections).forEach(([sectionName, section]) => {
      const sectionWeight = section.weight;
      maxScore += sectionWeight;
      
      let sectionCompletedFields = 0;
      const totalFields = section.fields.length;
      
      section.fields.forEach(field => {
        const value = userProfile[field as keyof UserProfile];
        if ('arrayFields' in section && section.arrayFields) {
          // For array fields, check if array exists and has items
          if (Array.isArray(value) && value.length > 0) {
            sectionCompletedFields++;
          }
        } else {
          // For regular fields, check if value exists and is not empty
          if (value && value !== '' && value !== 0) {
            sectionCompletedFields++;
          }
        }
      });
      
      const sectionCompletion = totalFields > 0 ? sectionCompletedFields / totalFields : 0;
      totalScore += sectionCompletion * sectionWeight;
    });

    const percentage = Math.round((totalScore / maxScore) * 100);
    
    let status = 'Incomplete';
    let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'error';
    
    if (percentage === 100) {
      status = 'Complete';
      color = 'success';
    } else if (percentage >= 80) {
      status = 'Nearly Complete';
      color = 'info';
    } else if (percentage >= 50) {
      status = 'In Progress';
      color = 'warning';
    } else if (percentage > 0) {
      status = 'Started';
      color = 'warning';
    }
    
    return { percentage, status, color };
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading patient data...
        </Typography>
      </Container>
    );
  }

  if (error && !patient) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/admin')}
        >
          Back to Admin Panel
        </Button>
      </Container>
    );
  }

  const completionStatus = getProfileCompletionStatus();

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/admin')}
            sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
          >
            <AdminPanelSettingsIcon fontSize="small" />
            Admin Panel
          </Link>
          <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <PersonIcon fontSize="small" />
            Patient Profile
          </Typography>
        </Breadcrumbs>

        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={8}>
              <Typography variant="h4" component="h1" gutterBottom>
                Patient Profile Management
              </Typography>
              {patient && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Chip label={`Name: ${patient.name}`} color="primary" />
                  <Chip label={`Phone: ${patient.phone}`} color="default" />
                  <Chip label={`Condition: ${patient.condition}`} color="info" />
                  <Chip label={`Code: ${patient.registration_code}`} color="secondary" />
                </Box>
              )}
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" gutterBottom>
                    Profile Status
                  </Typography>
                  <Chip 
                    label={`${completionStatus.status} (${completionStatus.percentage}%)`}
                    color={completionStatus.color}
                    size="medium"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>

        {success && (
          <Alert 
            severity="success" 
            sx={{ 
              mb: 2,
              '& .MuiAlert-icon': {
                fontSize: '1.5rem',
              },
              fontWeight: 'bold',
            }}
          >
            {success}
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
      </Box>

      {/* Profile Form */}
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            {userProfile ? 'Edit Patient Profile' : 'Create Patient Profile'}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {userProfile 
              ? 'This profile can be completed by either the doctor\'s office or the patient. Any changes made here will be saved to the patient\'s account.'
              : 'Start filling out the patient\'s profile. The patient can complete any missing information later using their registration code.'
            }
          </Typography>
        </Box>

        <UserProfileForm
          onSubmit={handleProfileSubmit}
          initialProfile={userProfile || undefined}
          submitButtonText="💾 Save Patient Profile"
          isAdminMode={true}
        />

        {saving && (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            mt: 2,
            p: 2,
            bgcolor: 'primary.main',
            color: 'white',
            borderRadius: 2,
            boxShadow: 3
          }}>
            <CircularProgress size={24} sx={{ color: 'white' }} />
            <Typography variant="body1" sx={{ ml: 2, fontWeight: 'bold' }}>
              💾 Saving patient profile...
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default AdminPatientProfile; 