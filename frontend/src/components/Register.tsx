import React, { useState, useEffect } from 'react';
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

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    registrationCode: '',
    email: '',
    password: '',
    confirmPassword: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  });
  const [error, setError] = useState<string | null>(null);
  const [consentChecked, setConsentChecked] = useState(false);
  const [showConsentForm, setShowConsentForm] = useState(false);
  const [signatureData, setSignatureData] = useState<{
    requiredConsent: boolean;
    researchConsent: boolean;
    signature: string;
    timestamp: string;
    ipAddress?: string;
  } | null>(null);

  useEffect(() => {
    setFormData(f => ({ ...f, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' }));
  }, []);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleOpenConsentForm = () => {
    setShowConsentForm(true);
  };

  const handleCloseConsentForm = () => {
    setShowConsentForm(false);
  };

  const handleAcceptConsent = (signature: any) => {
    setSignatureData(signature);
    setConsentChecked(true);
    setShowConsentForm(false);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!signatureData) {
      setError('You must sign the consent form to register');
      setShowConsentForm(true);
      return;
    }

    try {
      const payload = {
        ...formData,
        timezone: formData.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
      };

      const response = await fetch(`${config.API_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          registration_code: payload.registrationCode,
          email: payload.email,
          password: payload.password,
          consent_given: signatureData.requiredConsent,
          consent_timestamp: signatureData.timestamp,
          policy_version: CURRENT_POLICY_VERSION,
          electronic_signature: signatureData.signature,
          signature_timestamp: signatureData.timestamp,
          signature_ip_address: signatureData.ipAddress,
          research_consent: signatureData.researchConsent,
        }),
      });

      if (response.ok) {
        navigate('/login');
      } else {
        const errorData = await response.json();
        // Handle FastAPI validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `${err.loc[1]}: ${err.msg}`).join(', ');
          setError(errorMessages);
        } else {
          setError(errorData.detail || 'An error occurred during registration');
        }
      }
    } catch (err) {
      setError('An error occurred during registration');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 6, display: 'flex', alignItems: 'center', minHeight: '100vh' }}>
      <Paper 
        elevation={8} 
        sx={{ 
          p: 5,
          width: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 3,
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
        }}
      >
        {/* Header Section */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography 
            variant="h3" 
            component="h1" 
            sx={{ 
              color: 'white',
              fontWeight: 'bold',
              letterSpacing: '2px',
              mb: 1,
              textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
            }}
          >
            JOIN YOUR DIET MANAGER
          </Typography>
          <Typography 
            variant="subtitle1" 
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              fontWeight: 300,
              letterSpacing: '0.5px'
            }}
          >
            Create your account and start your health journey
          </Typography>
        </Box>

        <Divider sx={{ mb: 4, borderColor: 'rgba(255,255,255,0.2)' }} />

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
            {/* Registration Code Field */}
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
                Registration Code *
              </InputLabel>
              <TextField
                fullWidth
                name="registrationCode"
                value={formData.registrationCode}
                onChange={handleChange}
                required
                placeholder="Enter your registration code"
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

            {/* Email Field */}
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
                Email Address *
              </InputLabel>
              <TextField
                fullWidth
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="Enter your email address"
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
                Password *
              </InputLabel>
              <TextField
                fullWidth
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="Create a strong password"
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

            {/* Confirm Password Field */}
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
                Confirm Password *
              </InputLabel>
              <TextField
                fullWidth
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                placeholder="Confirm your password"
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

            {/* Consent Agreement */}
            <Box sx={{ mt: 2 }}>
              {signatureData ? (
                <Box sx={{ 
                  p: 2, 
                  bgcolor: 'rgba(76, 175, 80, 0.1)', 
                  border: '1px solid rgba(76, 175, 80, 0.3)',
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2
                }}>
                  <Typography sx={{ color: '#4caf50', fontSize: '1.2rem' }}>✓</Typography>
                  <Box>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)', fontWeight: 500 }}>
                      Consent Agreement Signed
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                      Signed by: {signatureData.signature} on {new Date(signatureData.timestamp).toLocaleDateString()}
                    </Typography>
                  </Box>
                  <MuiButton
                    onClick={handleOpenConsentForm}
                    size="small"
                    sx={{
                      color: 'rgba(255,255,255,0.8)',
                      textDecoration: 'underline',
                      textTransform: 'none',
                      fontSize: '0.75rem',
                      '&:hover': {
                        backgroundColor: 'transparent',
                        textDecoration: 'underline'
                      }
                    }}
                  >
                    Review
                  </MuiButton>
                </Box>
              ) : (
                <Button
                  onClick={handleOpenConsentForm}
                  variant="outlined"
                  fullWidth
                  sx={{
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white',
                    py: 1.5,
                    fontSize: '1rem',
                    textTransform: 'none',
                    '&:hover': {
                      borderColor: 'rgba(255,255,255,0.6)',
                      backgroundColor: 'rgba(255,255,255,0.1)'
                    }
                  }}
                >
                  📋 Sign Consent Agreement (Required)
                </Button>
              )}
            </Box>

            {/* Action Button */}
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
                Create Account
              </Button>
            </Box>

            {/* Login Link */}
            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Already have an account?{' '}
                <Link
                  component="button"
                  variant="body2"
                  onClick={() => navigate('/login')}
                  sx={{ 
                    color: 'white', 
                    fontWeight: 600,
                    textDecoration: 'underline',
                    '&:hover': { 
                      color: 'rgba(255,255,255,0.8)' 
                    }
                  }}
                >
                  Sign in here
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
        mode="registration"
      />
    </Container>
  );
};

export default Register; 