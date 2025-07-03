import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Link,
  Alert,
  FormControlLabel,
  Checkbox,
  Button as MuiButton,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ConsentForm from './ConsentForm';

const CURRENT_POLICY_VERSION = '1.0.0';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [consentChecked, setConsentChecked] = useState(false);
  const [showConsentForm, setShowConsentForm] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleConsentCheck = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConsentChecked(event.target.checked);
  };

  const handleOpenConsentForm = () => {
    setShowConsentForm(true);
  };

  const handleCloseConsentForm = () => {
    setShowConsentForm(false);
  };

  const handleAcceptConsent = () => {
    setConsentChecked(true);
    setShowConsentForm(false);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!consentChecked) {
      setError('You must agree to the Privacy Policy to login');
      return;
    }

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('username', formData.username);
      formDataToSend.append('password', formData.password);
      formDataToSend.append('consent_given', consentChecked.toString());
      formDataToSend.append('consent_timestamp', new Date().toISOString());
      formDataToSend.append('policy_version', CURRENT_POLICY_VERSION);

      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formDataToSend,
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        // Check if the token contains admin status
        const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
        if (tokenPayload.is_admin) {
          localStorage.setItem('isAdmin', 'true');
        }
        navigate('/');
        window.location.reload();
      } else {
        const errorData = await response.json();
        // Handle FastAPI validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `${err.loc[1]}: ${err.msg}`).join(', ');
          setError(errorMessages);
        } else {
          setError(errorData.detail || 'Invalid credentials');
        }
      }
    } catch (err) {
      setError('An error occurred during login');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ color: 'white' }}>
          Login
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            margin="normal"
            required
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'rgba(255,255,255,0.1)',
                color: 'white',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                '&.Mui-focused fieldset': { borderColor: 'white' }
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.8)' },
              '& .MuiInputLabel-root.Mui-focused': { color: 'white' }
            }}
          />
          <TextField
            fullWidth
            label="Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
            required
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'rgba(255,255,255,0.1)',
                color: 'white',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                '&.Mui-focused fieldset': { borderColor: 'white' }
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.8)' },
              '& .MuiInputLabel-root.Mui-focused': { color: 'white' }
            }}
          />

          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={consentChecked}
                  onChange={handleConsentCheck}
                  sx={{ color: 'white' }}
                />
              }
              label={
                <Box component="span" sx={{ color: 'white', fontSize: '0.9rem' }}>
                  I agree to the collection and use of my health information as described in the{' '}
                  <MuiButton
                    onClick={handleOpenConsentForm}
                    sx={{
                      color: 'white',
                      textDecoration: 'underline',
                      p: 0,
                      minWidth: 'auto',
                      textTransform: 'none',
                      verticalAlign: 'baseline',
                      fontSize: 'inherit',
                    }}
                  >
                    Privacy Policy
                  </MuiButton>
                </Box>
              }
            />
          </Box>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/register')}
              sx={{ color: 'rgba(255,255,255,0.8)', '&:hover': { color: 'white' } }}
            >
              Don't have an account? Register
            </Link>
            <Button
              type="submit"
              variant="contained"
              size="large"
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.2)', 
                color: 'white',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
              }}
            >
              Login
            </Button>
          </Box>
        </form>
      </Paper>

      <ConsentForm
        open={showConsentForm}
        onClose={handleCloseConsentForm}
        onAccept={handleAcceptConsent}
      />
    </Container>
  );
};

export default Login; 