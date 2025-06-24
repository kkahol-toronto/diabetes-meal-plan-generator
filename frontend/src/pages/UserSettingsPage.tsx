import React, { useState } from 'react';
import { Container, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { deleteUserData } from '../utils/api';

const UserSettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showNotification } = useApp();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteData = async () => {
    if (window.confirm('Are you sure you want to delete all your data? This cannot be undone.')) {
      setIsDeleting(true);
      try {
        await deleteUserData();
        showNotification('Your account and data are permanently deleted.', 'success');
        localStorage.removeItem('token');
        navigate('/register');
      } catch (error) {
        console.error('Failed to delete user data:', error);
        showNotification('Failed to delete your data. Please try again later.', 'error');
        setIsDeleting(false);
      }
    }
  };

  return (
    <Container>
      <Typography variant="h4">Settings</Typography>
      <Box mt={4}>
        <Typography variant="h6">Data & Privacy</Typography>
        <Typography>
          Your privacy and data security are important to us. You have the right to delete all your personal information.
        </Typography>
        <Button 
          variant="contained" 
          color="error" 
          onClick={handleDeleteData}
          disabled={isDeleting}
        >
          {isDeleting ? 'Deleting...' : 'Delete My Data'}
        </Button>
      </Box>
    </Container>
  );
};

export default UserSettingsPage; 