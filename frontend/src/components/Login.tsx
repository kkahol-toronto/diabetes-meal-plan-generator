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
  InputLabel,
  Stack,
  Divider,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import config from '../config/environment';
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
  const [needsConsent, setNeedsConsent] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Reset consent requirement when username changes
    if (name === 'username') {
      setNeedsConsent(false);
      setConsentChecked(false);
      setError(null);
    }
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

  const handleAcceptConsent = (signature: any) => {
    setConsentChecked(true);
    setShowConsentForm(false);
    
    // Store signature data for login request
    const signatureData = {
      electronic_signature: signature.signature,
      signature_timestamp: signature.timestamp,
      research_consent: signature.researchConsent
    };
    
    // Automatically retry login with signature data
    retryLoginWithSignature(signatureData);
  };

  const retryLoginWithSignature = async (signatureData: any) => {
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('username', formData.username);
      formDataToSend.append('password', formData.password);
      formDataToSend.append('consent_given', 'true');
      formDataToSend.append('consent_timestamp', signatureData.signature_timestamp);
      formDataToSend.append('policy_version', CURRENT_POLICY_VERSION);
      formDataToSend.append('electronic_signature', signatureData.electronic_signature);
      formDataToSend.append('signature_timestamp', signatureData.signature_timestamp);
      formDataToSend.append('research_consent', signatureData.research_consent.toString());

      const response = await fetch(`${config.API_URL}/login`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formDataToSend,
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
        if (tokenPayload.is_admin) {
          localStorage.setItem('isAdmin', 'true');
        }
        navigate('/');
        window.location.reload();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed after consent signing');
      }
    } catch (err) {
      setError('An error occurred during login');
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // If consent is needed but not checked, show error
    if (needsConsent && !consentChecked) {
      setError('You must agree to the Privacy Policy to login');
      return;
    }

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('username', formData.username);
      formDataToSend.append('password', formData.password);
      
      // Only add consent data if needed and provided
      if (needsConsent && consentChecked) {
        formDataToSend.append('consent_given', 'true');
        formDataToSend.append('consent_timestamp', new Date().toISOString());
        formDataToSend.append('policy_version', CURRENT_POLICY_VERSION);
      }

      const response = await fetch(`${config.API_URL}/login`, {
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
        
        // If error is about missing consent/signature, show consent form
        if (errorData.detail === 'Electronic signature and consent are required to access services') {
          setNeedsConsent(true);
          setShowConsentForm(true);
          setError('Please sign the consent agreement to continue');
          return;
        }
        
        // Handle other errors
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
    <Container maxWidth="sm" sx={{ 
      py: { xs: 3, sm: 6 }, 
      px: { xs: 2, sm: 3 },
      display: 'flex', 
      alignItems: 'center', 
      minHeight: '100vh' 
    }}>
      <Paper 
        elevation={8} 
        sx={{ 
          p: { xs: 3, sm: 5 },
          width: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: { xs: 2, sm: 3 },
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
        }}
      >
        {/* Header Section */}
        <Box sx={{ textAlign: 'center', mb: { xs: 3, sm: 4 } }}>
          <Typography 
            variant="h3" 
            component="h1" 
            sx={{ 
              color: 'white',
              fontWeight: 'bold',
              letterSpacing: '2px',
              mb: 1,
              textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
              fontSize: { xs: '1.8rem', sm: '2.5rem', md: '3rem' }
            }}
          >
            YOUR DIET MANAGER
          </Typography>
          <Typography 
            variant="subtitle1" 
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              fontWeight: 300,
              letterSpacing: '0.5px',
              fontSize: { xs: '0.9rem', sm: '1rem' }
            }}
          >
            Welcome back! Please sign in to your account
          </Typography>
        </Box>

        <Divider sx={{ mb: { xs: 3, sm: 4 }, borderColor: 'rgba(255,255,255,0.2)' }} />

        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              mb: 3,
              bgcolor: 'rgba(211, 47, 47, 0.1)',
              color: 'white',
              border: '1px solid rgba(211, 47, 47, 0.3)'
            }}
          >
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack spacing={3}>
            {/* Username Field */}
            <Box>
              <InputLabel 
                sx={{ 
                  color: 'white', 
                  mb: 1, 
                  fontSize: '1rem',
                  fontWeight: 500,
                  display: 'block'
                }}
              >
                Username
              </InputLabel>
              <TextField
                fullWidth
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                placeholder="Enter your username"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'rgba(255,255,255,0.15)',
                    color: 'white',
                    borderRadius: 2,
                    fontSize: '1.1rem',
                    '& fieldset': { 
                      borderColor: 'rgba(255,255,255,0.3)',
                      borderWidth: 2
                    },
                    '&:hover fieldset': { 
                      borderColor: 'rgba(255,255,255,0.6)' 
                    },
                    '&.Mui-focused fieldset': { 
                      borderColor: 'white',
                      borderWidth: 2
                    }
                  },
                  '& .MuiOutlinedInput-input': {
                    padding: '14px 16px'
                  },
                  '& .MuiInputBase-input::placeholder': {
                    color: 'rgba(255,255,255,0.6)',
                    opacity: 1
                  }
                }}
              />
            </Box>

            {/* Password Field */}
            <Box>
              <InputLabel 
                sx={{ 
                  color: 'white', 
                  mb: 1, 
                  fontSize: '1rem',
                  fontWeight: 500,
                  display: 'block'
                }}
              >
                Password
              </InputLabel>
              <TextField
                fullWidth
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="Enter your password"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'rgba(255,255,255,0.15)',
                    color: 'white',
                    borderRadius: 2,
                    fontSize: '1.1rem',
                    '& fieldset': { 
                      borderColor: 'rgba(255,255,255,0.3)',
                      borderWidth: 2
                    },
                    '&:hover fieldset': { 
                      borderColor: 'rgba(255,255,255,0.6)' 
                    },
                    '&.Mui-focused fieldset': { 
                      borderColor: 'white',
                      borderWidth: 2
                    }
                  },
                  '& .MuiOutlinedInput-input': {
                    padding: '14px 16px'
                  },
                  '& .MuiInputBase-input::placeholder': {
                    color: 'rgba(255,255,255,0.6)',
                    opacity: 1
                  }
                }}
              />
            </Box>

            {/* Consent Checkbox - Only show when needed */}
            {needsConsent && (
              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={consentChecked}
                      onChange={handleConsentCheck}
                      sx={{ 
                        color: 'rgba(255,255,255,0.8)',
                        '&.Mui-checked': { color: 'white' }
                      }}
                    />
                  }
                  label={
                    <Box component="span" sx={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.95rem', lineHeight: 1.4 }}>
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
                          fontWeight: 500,
                          '&:hover': {
                            backgroundColor: 'transparent',
                            textDecoration: 'underline'
                          }
                        }}
                      >
                        Privacy Policy
                      </MuiButton>
                    </Box>
                  }
                />
              </Box>
            )}

            {/* Action Buttons */}
            <Box sx={{ mt: 4 }}>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ 
                  bgcolor: 'rgba(255,255,255,0.2)', 
                  color: 'white',
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  borderRadius: 2,
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  border: '2px solid rgba(255,255,255,0.3)',
                  '&:hover': { 
                    bgcolor: 'rgba(255,255,255,0.3)',
                    borderColor: 'rgba(255,255,255,0.5)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                  },
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                Sign In
              </Button>
            </Box>

            {/* Register Link */}
            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Don't have an account?{' '}
                <Link
                  component="button"
                  variant="body2"
                  onClick={() => navigate('/register')}
                  sx={{ 
                    color: 'white', 
                    fontWeight: 600,
                    textDecoration: 'underline',
                    '&:hover': { 
                      color: 'rgba(255,255,255,0.8)' 
                    }
                  }}
                >
                  Register here
                </Link>
              </Typography>
            </Box>
          </Stack>
        </form>
      </Paper>

      <ConsentForm
        open={showConsentForm}
        onClose={handleCloseConsentForm}
        onAccept={handleAcceptConsent}
        mode="login"
      />
    </Container>
  );
};

export default Login; 