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
        setSuccess('Patient profile saved successfully!');
        setUserProfile(profile);
        setTimeout(() => setSuccess(null), 3000);
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
    
    const requiredFields = ['name', 'age', 'gender', 'height', 'weight'];
    const completedFields = requiredFields.filter(field => userProfile[field as keyof UserProfile]);
    const percentage = Math.round((completedFields.length / requiredFields.length) * 100);
    
    let status = 'Incomplete';
    let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'warning';
    
    if (percentage === 100) {
      status = 'Complete';
      color = 'success';
    } else if (percentage >= 50) {
      status = 'In Progress';
      color = 'info';
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
          <Alert severity="success" sx={{ mb: 2 }}>
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
        />

        {saving && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 1 }}>
              Saving profile...
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default AdminPatientProfile; 