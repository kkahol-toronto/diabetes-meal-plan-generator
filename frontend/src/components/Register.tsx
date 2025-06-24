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
  Grid,
  InputLabel,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ConsentModal from './ConsentModal';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    registration_code: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const [consentGiven, setConsentGiven] = useState(false);
  const [consentModalOpen, setConsentModalOpen] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleConsentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setConsentGiven(event.target.checked);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Validation checks
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!consentGiven) {
      setError('You must agree to the terms and conditions to continue');
      return;
    }

    if (!formData.registration_code) {
      setError('Registration code is required');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          registration_code: formData.registration_code,
          email: formData.email,
          password: formData.password,
          first_name: formData.first_name,
          last_name: formData.last_name,
          consent_given: consentGiven
        }),
      });

      if (response.ok) {
        // Automatic login after registration
        const loginFormData = new FormData();
        loginFormData.append('username', formData.email);
        loginFormData.append('password', formData.password);

        const loginResponse = await fetch('http://localhost:8000/login', {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
          },
          body: loginFormData,
        });

        if (loginResponse.ok) {
          const loginData = await loginResponse.json();
          localStorage.setItem('token', loginData.access_token);
          navigate('/');
          window.location.reload();
        } else {
          // If login fails, still go to login page
          navigate('/login');
        }
      } else {
        const errorData = await response.json();
        // Handle FastAPI validation errors
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map((err: any) => `${err.loc[1]}: ${err.msg}`).join(', ');
          setError(errorMessages);
        } else {
          setError(errorData.detail || 'Registration failed');
        }
      }
    } catch (err) {
      setError('An error occurred during registration');
    }
  };

  const handleScrolled = () => {
    setHasScrolledToBottom(true);
  };

  const openConsentModal = (event: React.MouseEvent) => {
    event.preventDefault();
    setConsentModalOpen(true);
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 2,
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)'
        }}
      >
        <Box sx={{ 
          mb: 4, 
          pb: 2, 
          borderBottom: '1px solid rgba(255,255,255,0.2)'
        }}>
          <Typography 
            variant="h3" 
            component="h1" 
            align="center" 
            sx={{ 
              color: '#ffffff', 
              fontWeight: 700,
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              letterSpacing: '0.5px'
            }}
          >
            Create Account
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.9)' }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 2 }}>
            <InputLabel 
              htmlFor="registration_code" 
              sx={{ 
                color: 'white', 
                mb: 1, 
                fontWeight: 500,
                fontSize: '0.9rem',
                textAlign: 'left'
              }}
            >
              Registration Code
            </InputLabel>
            <TextField
              id="registration_code"
              fullWidth
              name="registration_code"
              value={formData.registration_code}
              onChange={handleChange}
              required
              variant="outlined"
              placeholder="Enter your registration code"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255,255,255,0.1)',
                  color: 'white',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                  '&.Mui-focused fieldset': { borderColor: 'white' }
                },
                '& .MuiInputLabel-root': { display: 'none' },
              }}
              InputLabelProps={{ shrink: true }}
            />
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Box sx={{ mb: 2 }}>
                <InputLabel 
                  htmlFor="first_name" 
                  sx={{ 
                    color: 'white', 
                    mb: 1, 
                    fontWeight: 500,
                    fontSize: '0.9rem',
                    textAlign: 'left'
                  }}
                >
                  First Name
                </InputLabel>
                <TextField
                  id="first_name"
                  fullWidth
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  required
                  variant="outlined"
                  placeholder="Enter your first name"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.1)',
                      color: 'white',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                      '&.Mui-focused fieldset': { borderColor: 'white' }
                    },
                    '& .MuiInputLabel-root': { display: 'none' },
                  }}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box sx={{ mb: 2 }}>
                <InputLabel 
                  htmlFor="last_name" 
                  sx={{ 
                    color: 'white', 
                    mb: 1, 
                    fontWeight: 500,
                    fontSize: '0.9rem',
                    textAlign: 'left'
                  }}
                >
                  Last Name
                </InputLabel>
                <TextField
                  id="last_name"
                  fullWidth
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  required
                  variant="outlined"
                  placeholder="Enter your last name"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: 'rgba(255,255,255,0.1)',
                      color: 'white',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                      '&.Mui-focused fieldset': { borderColor: 'white' }
                    },
                    '& .MuiInputLabel-root': { display: 'none' },
                  }}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
            </Grid>
          </Grid>

          <Box sx={{ mb: 3 }}>
            <InputLabel 
              htmlFor="email" 
              sx={{ 
                color: 'white', 
                mb: 1, 
                fontWeight: 500,
                fontSize: '0.9rem',
                textAlign: 'left'
              }}
            >
              Email
            </InputLabel>
            <TextField
              id="email"
              fullWidth
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
              variant="outlined"
              placeholder="Enter your email"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255,255,255,0.1)',
                  color: 'white',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                  '&.Mui-focused fieldset': { borderColor: 'white' }
                },
                '& .MuiInputLabel-root': { display: 'none' },
              }}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
          
          <Box sx={{ mb: 3 }}>
            <InputLabel 
              htmlFor="password" 
              sx={{ 
                color: 'white', 
                mb: 1, 
                fontWeight: 500,
                fontSize: '0.9rem',
                textAlign: 'left'
              }}
            >
              Password
            </InputLabel>
            <TextField
              id="password"
              fullWidth
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              variant="outlined"
              placeholder="Enter your password"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255,255,255,0.1)',
                  color: 'white',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                  '&.Mui-focused fieldset': { borderColor: 'white' }
                },
                '& .MuiInputLabel-root': { display: 'none' },
              }}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
          
          <Box sx={{ mb: 3 }}>
            <InputLabel 
              htmlFor="confirmPassword" 
              sx={{ 
                color: 'white', 
                mb: 1, 
                fontWeight: 500,
                fontSize: '0.9rem',
                textAlign: 'left'
              }}
            >
              Confirm Password
            </InputLabel>
            <TextField
              id="confirmPassword"
              fullWidth
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              variant="outlined"
              placeholder="Confirm your password"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255,255,255,0.1)',
                  color: 'white',
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                  '&.Mui-focused fieldset': { borderColor: 'white' }
                },
                '& .MuiInputLabel-root': { display: 'none' },
              }}
              InputLabelProps={{ shrink: true }}
            />
          </Box>

          <Box sx={{ mt: 2, mb: 3, display: 'flex', alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={consentGiven}
                  onChange={handleConsentChange}
                  disabled={!hasScrolledToBottom}
                  sx={{
                    color: 'rgba(255,255,255,0.7)',
                    '&.Mui-checked': { color: 'white' },
                    '&.Mui-disabled': { color: 'rgba(255,255,255,0.5)' },
                    padding: '0 8px 0 0',
                  }}
                />
              }
              label={
                <Typography variant="body2" sx={{ color: 'white', ml: 0 }}>
                  I agree to the{' '}
                  <Link 
                    component="button"
                    variant="body2"
                    onClick={openConsentModal}
                    sx={{ color: 'rgba(255,255,255,0.8)', fontWeight: 'bold', textDecoration: 'underline', '&:hover': { color: 'white' } }}
                  >
                    Terms and Conditions
                  </Link>
                </Typography>
              }
              sx={{ 
                margin: 0,
                alignItems: 'flex-start'
              }}
            />
          </Box>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/login')}
              sx={{ color: 'rgba(255,255,255,0.8)', '&:hover': { color: 'white' } }}
            >
              Already have an account? Login
            </Link>
            <Button
              type="submit"
              variant="contained"
              size="large"
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.2)', 
                color: 'white',
                fontWeight: 'bold',
                px: 4,
                py: 1,
                boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
              }}
            >
              REGISTER
            </Button>
          </Box>
        </form>
      </Paper>

      <ConsentModal
        open={consentModalOpen}
        onClose={() => setConsentModalOpen(false)}
        onScrolled={handleScrolled}
        hasScrolledToBottom={hasScrolledToBottom}
      />
    </Container>
  );
};

export default Register; 