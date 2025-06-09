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
      
      const patientProfile = await getAdminUserProfile(userId);
      setProfile(patientProfile);
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

  const handleProfileSubmit = async (profileData: PatientProfile) => {
    if (!userId) return;

    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);

      const success = await saveAdminUserProfile(userId, profileData);
      
      if (success) {
        setSaveSuccess(true);
        // Refresh the profile data
        await fetchUserProfile();
        
        // Clear success message after 3 seconds
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        setError('Failed to save profile');
      }
    } catch (err) {
      console.error('Error saving profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleGoBack = () => {
    navigate('/admin');
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box display="flex" alignItems="center" mb={3}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={handleGoBack}
            sx={{ mr: 2 }}
          >
            Back to Admin Panel
          </Button>
          <Typography variant="h4" component="h1">
            User Profile - {userId}
          </Typography>
        </Box>

        {/* Status Messages */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {saveSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Profile saved successfully!
          </Alert>
        )}

        {saving && (
          <Box display="flex" alignItems="center" mb={2}>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            <Typography variant="body2">Saving profile...</Typography>
          </Box>
        )}

        {/* Profile Status */}
        {profile ? (
          <Box mb={2}>
            <Chip 
              label="Profile Exists" 
              color="success" 
              variant="outlined" 
              sx={{ mr: 1 }} 
            />
            <Typography variant="body2" color="text.secondary" component="span">
              Last updated: {profile.intakeDate || 'Unknown'}
            </Typography>
          </Box>
        ) : (
          <Box mb={2}>
            <Chip 
              label="New Profile" 
              color="warning" 
              variant="outlined" 
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              This user hasn't filled out their profile yet. You can create it here.
            </Typography>
          </Box>
        )}

        {/* Profile Form */}
        <UserProfileForm
          onSubmit={handleProfileSubmit}
          initialProfile={profile || undefined}
          mode="admin"
        />
      </Paper>
    </Container>
  );
};

export default AdminUserProfile; 