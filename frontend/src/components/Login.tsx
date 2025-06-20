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
  InputLabel,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ConsentModal from './ConsentModal';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
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
    
    if (!consentGiven) {
      setError('You must agree to the terms and conditions to continue');
      return;
    }
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('username', formData.username);
      formDataToSend.append('password', formData.password);

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
        // Check if the error is due to consent required
        if (errorData.detail === 'Consent required') {
          handleUpdateConsent();
        } else {
          // Handle FastAPI validation errors
          if (errorData.detail && Array.isArray(errorData.detail)) {
            const errorMessages = errorData.detail.map((err: any) => `${err.loc[1]}: ${err.msg}`).join(', ');
            setError(errorMessages);
          } else {
            setError(errorData.detail || 'Invalid credentials');
          }
        }
      }
    } catch (err) {
      setError('An error occurred during login');
    }
  };

  const handleScrolled = () => {
    setHasScrolledToBottom(true);
  };

  const openConsentModal = (event: React.MouseEvent) => {
    event.preventDefault();
    setConsentModalOpen(true);
  };

  const handleUpdateConsent = async () => {
    if (!consentGiven) {
      setError('You must agree to the terms and conditions to continue');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/update-consent-unauthenticated', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: formData.username,
          password: formData.password,
          consent_given: consentGiven
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Save the token and redirect
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
        setError(errorData.detail || 'Failed to update consent');
      }
    } catch (err) {
      setError('An error occurred while updating consent');
    }
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
            Meet Your Planner
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2, bgcolor: 'rgba(255,255,255,0.9)' }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 3 }}>
            <InputLabel 
              htmlFor="username" 
              sx={{ 
                color: 'white', 
                mb: 1, 
                fontWeight: 500,
                fontSize: '0.9rem',
                textAlign: 'left'
              }}
            >
              Username
            </InputLabel>
            <TextField
              id="username"
              fullWidth
              name="username"
              value={formData.username}
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
                fontWeight: 'bold',
                px: 4,
                py: 1,
                boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
              }}
            >
              LOGIN
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

export default Login; 