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
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import CloudOffIcon from '@mui/icons-material/CloudOff';
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

const AdminPatientProfile = () => {
  const navigate = useNavigate();
  const { registrationCode } = useParams<{ registrationCode: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [databaseSaveStatus, setDatabaseSaveStatus] = useState<'pending' | 'saved' | 'failed' | 'checking'>('pending');
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
      setDatabaseSaveStatus('pending');
      setLastSaveTime(null);
    };
  }, [registrationCode]);

  const fetchPatientData = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      setDatabaseSaveStatus('checking');
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
          
          // Use enhanced status information from backend
          if (profileData.profile && Object.keys(profileData.profile).length > 0) {
            setDatabaseSaveStatus('saved');
            setLastSaveTime(profileData.last_updated ? new Date(profileData.last_updated).toLocaleString() : new Date().toLocaleString());
            
            // Log profile info for admin debugging
            console.log('[AdminPatientProfile] Profile loaded:', {
              hasUserAccount: profileData.has_user_account,
              profileCompleteness: profileData.profile_completeness,
              profileStatus: profileData.profile_status,
              lastUpdated: profileData.last_updated
            });
          } else {
            setDatabaseSaveStatus('pending');
          }
        } else if (profileResponse.status === 404) {
          // Patient hasn't created a profile yet - that's ok
          setUserProfile(null);
          setDatabaseSaveStatus('pending');
        } else {
          console.warn('Failed to fetch patient profile');
          setUserProfile(null);
          setDatabaseSaveStatus('failed');
        }
      } catch (profileError) {
        console.warn('Error fetching patient profile:', profileError);
        // Continue without profile - admin can create one
        setUserProfile(null);
        setDatabaseSaveStatus('failed');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patient data');
      setDatabaseSaveStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  const verifyDatabaseSave = async () => {
    try {
      setDatabaseSaveStatus('checking');
      
      // Verify the profile is saved and accessible
      const response = await fetch(`${config.API_URL}/admin/patient-profile/${registrationCode}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        
        // Check if we received a valid profile
        if (data.profile && typeof data.profile === 'object') {
          setDatabaseSaveStatus('saved');
          setLastSaveTime(new Date().toLocaleString());
          return true;
        } else {
          setDatabaseSaveStatus('failed');
          console.error('Invalid profile data received');
          return false;
        }
      } else {
        setDatabaseSaveStatus('failed');
        console.error('Failed to fetch patient profile');
        return false;
      }
    } catch (error) {
      console.error('Error verifying database save:', error);
      setDatabaseSaveStatus('failed');
      return false;
    }
  };

  const handleProfileSubmit = async (profile: UserProfile) => {
    try {
      setSaving(true);
      setError(null);
      setDatabaseSaveStatus('checking');

      // Use the enhanced admin profile saving endpoint
      const response = await fetch(`${config.API_URL}/admin/patient-profile/${registrationCode}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ profile }),
      });

      if (response.ok) {
        const result = await response.json();
        
        // Enhanced success message with completeness info
        const completenessText = result.profile_completeness ? ` (${result.profile_completeness}% complete)` : '';
        setSuccess(`✅ Patient profile saved successfully${completenessText}! The patient can continue filling out any missing information.`);
        
        // Update profile with the saved data from backend
        setUserProfile(result.profile || profile);
        setDatabaseSaveStatus('saved');
        setLastSaveTime(new Date().toLocaleString());
        
        // Log success details for admin debugging
        console.log('[AdminPatientProfile] Profile saved successfully:', {
          message: result.message,
          completeness: result.profile_completeness,
          attempt: result.attempt,
          timestamp: result.timestamp,
          user_save: result.user_save,
          profile_save: result.profile_save
        });
        
        setTimeout(() => setSuccess(null), 8000);
      } else {
        const errorData = await response.json();
        setDatabaseSaveStatus('failed');
        throw new Error(errorData.detail || 'Failed to save patient profile');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save patient profile';
      setError(errorMessage);
      setDatabaseSaveStatus('failed');
      
      // Enhanced error logging for admin debugging
      console.error('[AdminPatientProfile] Profile save error:', {
        error: err,
        registrationCode,
        profileData: profile
      });
    } finally {
      setSaving(false);
    }
  };

  const getDatabaseStatusDisplay = () => {
    switch (databaseSaveStatus) {
      case 'saved':
        return {
          icon: <CloudDoneIcon sx={{ color: 'success.main' }} />,
          text: 'Profile Saved Successfully',
          subtext: lastSaveTime ? `Admin updated profile verified: ${lastSaveTime}` : 'Profile saved and accessible to both admin and patient',
          color: '#1b5e20', // Dark green for better readability
          bgColor: '#f1f8e9', // Very light green background
          borderColor: '#4caf50'
        };
      case 'failed':
        return {
          icon: <CloudOffIcon sx={{ color: 'error.main' }} />,
          text: 'Database Save Failed',
          subtext: 'Profile not saved properly - patient will not see changes',
          color: '#b71c1c', // Dark red for better readability
          bgColor: '#ffebee', // Very light red background
          borderColor: '#f44336'
        };
      case 'checking':
        return {
          icon: <CircularProgress size={20} sx={{ color: 'info.main' }} />,
          text: 'Saving Profile...',
          subtext: 'Using robust admin profile system with retry logic...',
          color: '#0d47a1', // Dark blue for better readability
          bgColor: '#e3f2fd', // Very light blue background
          borderColor: '#2196f3'
        };
      default:
        return {
          icon: <ErrorIcon sx={{ color: 'warning.main' }} />,
          text: 'Profile Not Saved',
          subtext: 'Profile has not been saved to patient\'s account yet',
          color: '#e65100', // Dark orange for better readability
          bgColor: '#fff3e0', // Very light orange background
          borderColor: '#ff9800'
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
        fields: ['primaryGoals', 'calorieTarget', 'readinessToChange'],
        arrayFields: ['primaryGoals'], // Only primaryGoals is an array
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
        if ('arrayFields' in section && Array.isArray(section.arrayFields) && section.arrayFields.includes(field)) {
          // For array fields, check if array exists and has items
          if (Array.isArray(value) && value.length > 0) {
            sectionCompletedFields++;
          }
        } else if ('arrayFields' in section && section.arrayFields === true) {
          // For sections where all fields are arrays (old logic)
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
  const dbStatus = getDatabaseStatusDisplay();

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
          key={`patient-profile-${registrationCode}`}
          onSubmit={handleProfileSubmit}
          initialProfile={userProfile || undefined}
          submitButtonText="💾 Save Patient Profile"
          isAdminMode={true}
        />

        {/* Database Save Status Indicator */}
        <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Paper
            elevation={2}
            sx={{
              p: 2,
              border: 2,
              borderColor: dbStatus.borderColor,
              backgroundColor: dbStatus.bgColor,
              borderRadius: 2,
              flex: 1
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              {dbStatus.icon}
              <Box>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    fontWeight: 'bold',
                    color: dbStatus.color,
                    fontSize: '1rem'
                  }}
                >
                  {dbStatus.text}
                </Typography>
                {dbStatus.subtext && (
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      color: dbStatus.color,
                      fontSize: '0.9rem',
                      fontWeight: 500
                    }}
                  >
                    {dbStatus.subtext}
                  </Typography>
                )}
              </Box>
            </Box>
          </Paper>

          {/* Manual Verification Button */}
          <Button
            variant="outlined"
            size="small"
            onClick={verifyDatabaseSave}
            disabled={databaseSaveStatus === 'checking'}
            sx={{ minWidth: 120 }}
          >
            {databaseSaveStatus === 'checking' ? 'Checking...' : 'Verify Save'}
          </Button>
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