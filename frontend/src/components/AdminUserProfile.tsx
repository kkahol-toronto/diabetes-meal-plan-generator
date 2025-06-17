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
import { getAdminUserProfile, saveAdminUserProfile } from '../utils/api';
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
      
      const userProfile = await getAdminUserProfile(userId);
      setProfile(userProfile as PatientProfile);
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

  const handleProfileSubmit = async (updatedProfile: PatientProfile) => {
    if (!userId) return;

    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);

      const success = await saveAdminUserProfile(userId, updatedProfile);
      
      if (success) {
        setSaveSuccess(true);
        setProfile(updatedProfile);
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
          onSubmit={handleProfileSubmit as any}
          initialProfile={profile as any || undefined}
        />
      </Paper>
    </Container>
  );
};

export default AdminUserProfile; 