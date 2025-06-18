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
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import UserProfileForm from './UserProfileForm';
import { UserProfile } from '../types';
import { adminApi } from '../utils/api';

const AdminUserProfile: React.FC = () => {
  const { userId } = useParams();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!userId) return;
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const data = await adminApi.getUserProfile(userId);
        setProfile(data.profile as UserProfile);
        setError(null);
      } catch (err: any) {
        if (err?.status === 404) {
          // no profile yet
          setProfile(null);
          setError(null);
        } else {
          setError(err.message || 'Failed to load profile');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [userId]);

  const handleProfileSubmit = async (updated: UserProfile) => {
    if (!userId) return;
    try {
      setSaving(true);
      await adminApi.saveUserProfile(userId, updated);
      setProfile(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const goBack = () => navigate('/admin');

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>Loading user profile…</Typography>
        </Paper>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Button startIcon={<ArrowBackIcon />} onClick={goBack} sx={{ mr: 2 }}>
              Back to Admin Panel
            </Button>
          </Box>
          <Alert severity="error">{error}</Alert>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button startIcon={<ArrowBackIcon />} onClick={goBack} sx={{ mr: 2 }}>
              Back to Admin Panel
            </Button>
            <Box>
              <Typography variant="h4">User Profile</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="subtitle1" color="text.secondary">
                  User ID: {userId}
                </Typography>
                <Chip label="Admin View" color="primary" size="small" sx={{ ml: 2 }} />
              </Box>
            </Box>
          </Box>
        </Box>

        {saveSuccess && <Alert severity="success" sx={{ mb: 2 }}>Profile saved successfully!</Alert>}
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {!profile && <Alert severity="info" sx={{ mb: 2 }}>No profile yet – fill in the details below.</Alert>}
        {saving && <CircularProgress size={20} sx={{ mb: 2 }} />}

        <UserProfileForm onSubmit={handleProfileSubmit} initialProfile={profile || undefined} isAdminView={true} />
      </Paper>
    </Container>
  );
};

export default AdminUserProfile; 