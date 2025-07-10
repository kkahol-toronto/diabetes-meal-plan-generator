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
  LinearProgress,
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PersonIcon from '@mui/icons-material/Person';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import StorageIcon from '@mui/icons-material/Storage';
import UserProfileForm from './UserProfileForm';
import { UserProfile } from '../types';
import config from '../config/environment';

interface Patient {
  id: string;
  name: string;
  phone: string;
  condition: string;
  registration_code: string;
  created_at: string;
}

type SaveStatus = 'unsaved' | 'saving' | 'saved' | 'error';

const AdminPatientProfile = () => {
  const navigate = useNavigate();
  const { registrationCode } = useParams<{ registrationCode: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('unsaved');
  const [lastSaveTime, setLastSaveTime] = useState<string | null>(null);

  useEffect(() => {
    if (registrationCode) {
      fetchPatientData();
    }
  }, [registrationCode]);

  // Cleanup effect to reset state when component unmounts or registration code changes
  useEffect(() => {
    return () => {
      // Clear state when component unmounts or registration code changes
      setPatient(null);
      setUserProfile(null);
      setError(null);
      setSuccess(null);
      setSaveStatus('unsaved');
      setLastSaveTime(null);
    };
  }, [registrationCode]);

  const fetchPatientData = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      setSaveStatus('unsaved');
      setLastSaveTime(null);
      // Clear previous data immediately when switching patients
      setPatient(null);
      setUserProfile(null);

      // Fetch patient info
      const patientResponse = await fetch(`${config.API_URL}/admin/patient/${registrationCode}`, {
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
        const profileResponse = await fetch(`${config.API_URL}/admin/patient-profile/${registrationCode}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (profileResponse.ok) {
          const profileData = await profileResponse.json();
          setUserProfile(profileData.profile);
          setSaveStatus('saved');
          // Set last save time if available
          if (profileData.profile.updated_at || profileData.profile.created_at) {
            const saveTime = profileData.profile.updated_at || profileData.profile.created_at;
            setLastSaveTime(new Date(saveTime).toLocaleString());
          }
        } else if (profileResponse.status === 404) {
          // Patient hasn't created a profile yet - that's ok
          setUserProfile(null);
          setSaveStatus('unsaved');
        } else {
          console.warn('Failed to fetch patient profile');
          setUserProfile(null);
          setSaveStatus('unsaved');
        }
      } catch (profileError) {
        console.warn('Error fetching patient profile:', profileError);
        // Continue without profile - admin can create one
        setUserProfile(null);
        setSaveStatus('unsaved');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patient data');
      setSaveStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const verifyDatabaseSave = async () => {
    try {
      // Verify the profile is actually saved by fetching it again
      const verifyResponse = await fetch(`${config.API_URL}/admin/patient-profile/${registrationCode}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (verifyResponse.ok) {
        const verifyData = await verifyResponse.json();
        if (verifyData.profile) {
          setSaveStatus('saved');
          setLastSaveTime(new Date().toLocaleString());
          return true;
        }
      }
      
      setSaveStatus('error');
      return false;
    } catch (err) {
      setSaveStatus('error');
      return false;
    }
  };

  const handleProfileSubmit = async (profile: UserProfile) => {
    try {
      setSaving(true);
      setSaveStatus('saving');
      setError(null);

      const response = await fetch(`${config.API_URL}/admin/patient-profile/${registrationCode}`, {
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
        
        // Verify the save was successful in the database
        const isVerified = await verifyDatabaseSave();
        if (isVerified) {
          setSaveStatus('saved');
          setLastSaveTime(new Date().toLocaleString());
        } else {
          setSaveStatus('error');
          setError('❌ Profile save could not be verified in database. Please try again.');
        }
        
        setTimeout(() => setSuccess(null), 6000);
      } else {
        const errorData = await response.json();
        setSaveStatus('error');
        throw new Error(errorData.detail || 'Failed to save patient profile');
      }
    } catch (err) {
      setSaveStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to save patient profile');
    } finally {
      setSaving(false);
    }
  };

  const getSaveStatusDisplay = () => {
    switch (saveStatus) {
      case 'saved':
        return {
          icon: <CheckCircleIcon sx={{ color: 'success.main' }} />,
          text: 'Profile Saved in Database',
          color: 'success.main',
          bgColor: 'success.light',
          subtitle: lastSaveTime ? `Last saved: ${lastSaveTime}` : 'Successfully saved'
        };
      case 'saving':
        return {
          icon: <CircularProgress size={20} sx={{ color: 'info.main' }} />,
          text: 'Saving to Database...',
          color: 'info.main',
          bgColor: 'info.light',
          subtitle: 'Please wait while we save your changes'
        };
      case 'error':
        return {
          icon: <ErrorIcon sx={{ color: 'error.main' }} />,
          text: 'Profile Not Saved',
          color: 'error.main',
          bgColor: 'error.light',
          subtitle: 'There was an error saving to the database'
        };
      default: // 'unsaved'
        return {
          icon: <PendingIcon sx={{ color: 'warning.main' }} />,
          text: 'Profile Not Saved',
          color: 'warning.main',
          bgColor: 'warning.light',
          subtitle: 'Profile has not been saved to the database yet'
        };
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
  const saveStatusDisplay = getSaveStatusDisplay();

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
            <Grid item xs={12} md={6}>
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
            <Grid item xs={12} md={3}>
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
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <StorageIcon fontSize="small" />
                    <Typography variant="h6" sx={{ fontSize: '1rem' }}>
                      Database Status
                    </Typography>
                  </Box>
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 1,
                    p: 1,
                    bgcolor: saveStatusDisplay.bgColor,
                    borderRadius: 1,
                    mb: 1
                  }}>
                    {saveStatusDisplay.icon}
                    <Box>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 'bold',
                          color: saveStatusDisplay.color,
                          fontSize: '0.875rem'
                        }}
                      >
                        {saveStatusDisplay.text}
                      </Typography>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          color: 'text.secondary',
                          fontSize: '0.75rem'
                        }}
                      >
                        {saveStatusDisplay.subtitle}
                      </Typography>
                    </Box>
                  </Box>
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
          key={`patient-profile-${registrationCode}`}
          onSubmit={handleProfileSubmit}
          initialProfile={userProfile || undefined}
          submitButtonText="💾 Save Patient Profile"
          isAdminMode={true}
        />

        {/* Enhanced Save Status Display */}
        <Box sx={{ mt: 3 }}>
          <Paper 
            elevation={2} 
            sx={{ 
              p: 2,
              border: `2px solid ${saveStatusDisplay.color}`,
              bgcolor: saveStatusDisplay.bgColor,
              borderRadius: 2
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {saveStatusDisplay.icon}
              <Box sx={{ flex: 1 }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    color: saveStatusDisplay.color,
                    fontWeight: 'bold',
                    mb: 0.5
                  }}
                >
                  {saveStatusDisplay.text}
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ color: 'text.secondary' }}
                >
                  {saveStatusDisplay.subtitle}
                </Typography>
                {saveStatus === 'saving' && (
                  <LinearProgress 
                    sx={{ mt: 1, borderRadius: 1, height: 6 }}
                    color="info"
                  />
                )}
              </Box>
            </Box>
          </Paper>
        </Box>

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