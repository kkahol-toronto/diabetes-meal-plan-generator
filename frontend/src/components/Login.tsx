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
  Fade,
  Slide,
  Zoom,
  keyframes,
  IconButton,
} from '@mui/material';
import {
  Google as GoogleIcon,
  Visibility,
  VisibilityOff,
  Person as PersonIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import config from '../config/environment';
import ConsentForm from './ConsentForm';

const CURRENT_POLICY_VERSION = '1.0.0';

// Enhanced Mobile Animations
const slideInUp = keyframes`
  0% { 
    opacity: 0;
    transform: translateY(30px);
  }
  100% { 
    opacity: 1;
    transform: translateY(0);
  }
`;

const fadeInScale = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.95);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

const shimmer = keyframes`
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const gradientShift = keyframes`
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
`;

const bounceIn = keyframes`
  0% { 
    opacity: 0;
    transform: scale(0.3);
  }
  50% { 
    opacity: 1;
    transform: scale(1.05);
  }
  70% { 
    transform: scale(0.9);
  }
  100% { 
    opacity: 1;
    transform: scale(1);
  }
`;

const glow = keyframes`
  0% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
  50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8), 0 0 30px rgba(102, 126, 234, 0.4); }
  100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
`;

const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-3px); }
  100% { transform: translateY(0px); }
`;

// Declare global google object
declare global {
  interface Window {
    google: any;
  }
}

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
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  // Load Google Sign-In script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = () => {
      setGoogleLoaded(true);
      // Initialize Google Sign-In
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID || '1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com', // Replace with your actual client ID
          callback: handleGoogleSignIn,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  const handleGoogleSignIn = async (response: any) => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('Google Sign-In response received:', response);
      
      // Send the Google token to your backend for verification
      const backendResponse = await fetch(`${config.API_URL}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: response.credential,
        }),
      });

      const data = await backendResponse.json();
      console.log('Backend response:', data);

      if (backendResponse.ok) {
        // Check if consent is required
        if (data.token_type === 'consent_required') {
          setError(`Welcome ${data.user_name}! Please complete the consent form to continue.`);
          setNeedsConsent(true);
          // You could also auto-open the consent form here
          // setShowConsentForm(true);
          return;
        }
        
        // Successful login
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userId', data.user_id);
        console.log('Google Sign-In successful, navigating to home');
        navigate('/');
      } else {
        setError(data.detail || 'Google sign-in failed. Please try again.');
      }
    } catch (error) {
      console.error('Google Sign-In Error:', error);
      setError('Google sign-in failed. Please check your internet connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignInClick = () => {
    if (window.google && googleLoaded) {
      window.google.accounts.id.prompt();
    }
  };

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
    setIsLoading(true);
    setError(null);
    
    // If consent is needed but not checked, show error
    if (needsConsent && !consentChecked) {
      setError('You must agree to the Privacy Policy to login');
      setIsLoading(false);
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Box sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: { xs: 1, sm: 2 },
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
          animation: `${gradientShift} 8s ease infinite`,
          backgroundSize: '400% 400%',
          zIndex: 0,
        }
      }}>
      <Container maxWidth="sm" sx={{ 
        position: 'relative',
        zIndex: 1,
        py: 2
      }}>
        <Fade in={true} timeout={1000}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: { xs: 3, sm: 4 },
              width: '100%',
              borderRadius: '24px',
              background: 'rgba(255, 255, 255, 0.25)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
              animation: `${fadeInScale} 0.8s ease-out`,
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
                borderRadius: '24px',
                animation: `${shimmer} 3s ease-in-out infinite`,
                backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                backgroundSize: '200px 100%',
                backgroundRepeat: 'no-repeat',
              }
            }}
          >
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              {/* Header Section */}
              <Slide direction="down" in={true} timeout={800}>
                <Box sx={{ textAlign: 'center', mb: { xs: 3, sm: 4 } }}>
                  <Typography 
                    variant="h3" 
                    component="h1" 
                    sx={{ 
                      color: 'white',
                      fontWeight: 'bold',
                      letterSpacing: '2px',
                      mb: 2,
                      textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
                      fontSize: { xs: '1.8rem', sm: '2.5rem', md: '3rem' },
                      animation: `${bounceIn} 1s ease-out 0.3s both`
                    }}
                  >
                    🍽️ YOUR DIET MANAGER
                  </Typography>
                  <Typography 
                    variant="subtitle1" 
                    sx={{ 
                      color: 'rgba(255,255,255,0.9)',
                      fontWeight: 400,
                      letterSpacing: '0.5px',
                      fontSize: { xs: '0.9rem', sm: '1rem' },
                      textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                      animation: `${slideInUp} 0.8s ease-out 0.5s both`
                    }}
                  >
                    Welcome back! Please sign in to your account
                  </Typography>
                </Box>
              </Slide>

              <Divider sx={{ 
                mb: { xs: 3, sm: 4 }, 
                borderColor: 'rgba(255,255,255,0.2)',
                animation: `${slideInUp} 0.6s ease-out 0.7s both`
              }} />

              {error && (
                <Fade in={true} timeout={600}>
                  <Alert 
                    severity="error" 
                    sx={{ 
                      mb: 3,
                      borderRadius: '16px',
                      background: 'rgba(244, 67, 54, 0.1)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(244, 67, 54, 0.3)',
                      color: 'white',
                      '& .MuiAlert-icon': {
                        color: 'white'
                      }
                    }}
                  >
                    {error}
                  </Alert>
                </Fade>
              )}

              {/* Google Sign-In Button */}
              <Zoom in={true} timeout={800} style={{ transitionDelay: '0.9s' }}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<GoogleIcon />}
                  onClick={handleGoogleSignInClick}
                  disabled={!googleLoaded || isLoading}
                  sx={{
                    mb: 3,
                    background: 'linear-gradient(135deg, #4285f4 0%, #34a853 100%)',
                    color: 'white',
                    borderRadius: '50px',
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600,
                    textTransform: 'none',
                    boxShadow: '0 4px 15px rgba(66, 133, 244, 0.4)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #3367d6 0%, #2d8f47 100%)',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 6px 20px rgba(66, 133, 244, 0.5)',
                      animation: `${glow} 2s ease-in-out infinite`,
                    },
                    '&:disabled': {
                      background: 'rgba(255, 255, 255, 0.2)',
                      color: 'rgba(255, 255, 255, 0.5)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  {googleLoaded ? '🚀 Continue with Google' : 'Loading Google Sign-In...'}
                </Button>
              </Zoom>

              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                mb: 3,
                animation: `${slideInUp} 0.6s ease-out 1.1s both`
              }}>
                <Divider sx={{ flex: 1, borderColor: 'rgba(255,255,255,0.3)' }} />
                <Typography sx={{ 
                  px: 2, 
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: '0.9rem',
                  fontWeight: 500
                }}>
                  or sign in with email
                </Typography>
                <Divider sx={{ flex: 1, borderColor: 'rgba(255,255,255,0.3)' }} />
              </Box>

              <form onSubmit={handleSubmit}>
                <Stack spacing={3}>
                  {/* Username Field */}
                  <Slide direction="right" in={true} timeout={800} style={{ transitionDelay: '1.3s' }}>
                    <Box>
                      <InputLabel 
                        sx={{ 
                          color: 'white', 
                          mb: 1.5, 
                          fontSize: '1rem',
                          fontWeight: 600,
                          display: 'flex',
                          alignItems: 'center',
                          textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                        }}
                      >
                        <PersonIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
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
                            background: 'rgba(255,255,255,0.15)',
                            backdropFilter: 'blur(10px)',
                            color: 'white',
                            borderRadius: '20px',
                            fontSize: '1rem',
                            border: '1px solid rgba(255,255,255,0.3)',
                            '& fieldset': { 
                              border: 'none'
                            },
                            '&:hover': {
                              background: 'rgba(255,255,255,0.2)',
                              transform: 'translateY(-1px)',
                              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)',
                            },
                            '&.Mui-focused': {
                              background: 'rgba(255,255,255,0.25)',
                              transform: 'translateY(-2px)',
                              boxShadow: '0 6px 16px rgba(102, 126, 234, 0.3)',
                              animation: `${glow} 2s ease-in-out infinite`,
                            },
                            transition: 'all 0.3s ease',
                          },
                          '& .MuiOutlinedInput-input': {
                            padding: '16px 20px'
                          },
                          '& .MuiInputBase-input::placeholder': {
                            color: 'rgba(255,255,255,0.6)',
                            opacity: 1
                          }
                        }}
                      />
                    </Box>
                  </Slide>

                  {/* Password Field */}
                  <Slide direction="left" in={true} timeout={800} style={{ transitionDelay: '1.5s' }}>
                    <Box>
                      <InputLabel 
                        sx={{ 
                          color: 'white', 
                          mb: 1.5, 
                          fontSize: '1rem',
                          fontWeight: 600,
                          display: 'flex',
                          alignItems: 'center',
                          textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                        }}
                      >
                        <LockIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
                        Password
                      </InputLabel>
                      <TextField
                        fullWidth
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        value={formData.password}
                        onChange={handleChange}
                        required
                        placeholder="Enter your password"
                        InputProps={{
                          endAdornment: (
                            <IconButton
                              onClick={() => setShowPassword(!showPassword)}
                              edge="end"
                              sx={{ 
                                color: 'rgba(255,255,255,0.7)',
                                '&:hover': {
                                  color: 'white',
                                  transform: 'scale(1.1)',
                                }
                              }}
                            >
                              {showPassword ? <VisibilityOff /> : <Visibility />}
                            </IconButton>
                          ),
                        }}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            background: 'rgba(255,255,255,0.15)',
                            backdropFilter: 'blur(10px)',
                            color: 'white',
                            borderRadius: '20px',
                            fontSize: '1rem',
                            border: '1px solid rgba(255,255,255,0.3)',
                            '& fieldset': { 
                              border: 'none'
                            },
                            '&:hover': {
                              background: 'rgba(255,255,255,0.2)',
                              transform: 'translateY(-1px)',
                              boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)',
                            },
                            '&.Mui-focused': {
                              background: 'rgba(255,255,255,0.25)',
                              transform: 'translateY(-2px)',
                              boxShadow: '0 6px 16px rgba(102, 126, 234, 0.3)',
                              animation: `${glow} 2s ease-in-out infinite`,
                            },
                            transition: 'all 0.3s ease',
                          },
                          '& .MuiOutlinedInput-input': {
                            padding: '16px 20px'
                          },
                          '& .MuiInputBase-input::placeholder': {
                            color: 'rgba(255,255,255,0.6)',
                            opacity: 1
                          }
                        }}
                      />
                    </Box>
                  </Slide>

                  {/* Consent Checkbox - Only show when needed */}
                  {needsConsent && (
                    <Fade in={true} timeout={600}>
                      <Box sx={{ mt: 2 }}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={consentChecked}
                              onChange={handleConsentCheck}
                              sx={{ 
                                color: 'rgba(255,255,255,0.8)',
                                '&.Mui-checked': { 
                                  color: '#4CAF50',
                                  animation: `${pulse} 1s ease-in-out`
                                }
                              }}
                            />
                          }
                          label={
                            <Box component="span" sx={{ 
                              color: 'rgba(255,255,255,0.9)', 
                              fontSize: '0.9rem', 
                              lineHeight: 1.4,
                              textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                            }}>
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
                                  fontWeight: 600,
                                  '&:hover': {
                                    backgroundColor: 'transparent',
                                    textDecoration: 'underline',
                                    transform: 'scale(1.05)',
                                  }
                                }}
                              >
                                Privacy Policy
                              </MuiButton>
                            </Box>
                          }
                        />
                      </Box>
                    </Fade>
                  )}

                  {/* Sign In Button */}
                  <Zoom in={true} timeout={800} style={{ transitionDelay: '1.7s' }}>
                    <Button
                      type="submit"
                      fullWidth
                      variant="contained"
                      size="large"
                      disabled={isLoading}
                      sx={{ 
                        mt: 4,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        borderRadius: '50px',
                        py: 1.8,
                        fontSize: '1.1rem',
                        fontWeight: 600,
                        textTransform: 'none',
                        boxShadow: '0 6px 20px rgba(102, 126, 234, 0.4)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        '&:hover': { 
                          background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                          transform: 'translateY(-3px) scale(1.02)',
                          boxShadow: '0 8px 25px rgba(102, 126, 234, 0.5)',
                          animation: `${glow} 1.5s ease-in-out infinite`,
                        },
                        '&:disabled': {
                          background: 'rgba(255, 255, 255, 0.2)',
                          color: 'rgba(255, 255, 255, 0.5)',
                        },
                        transition: 'all 0.3s ease',
                      }}
                    >
                      {isLoading ? '🔄 Signing In...' : '🚀 Sign In'}
                    </Button>
                  </Zoom>

                  {/* Register Link */}
                  <Fade in={true} timeout={1000} style={{ transitionDelay: '1.9s' }}>
                    <Box sx={{ textAlign: 'center', mt: 3 }}>
                      <Typography variant="body2" sx={{ 
                        color: 'rgba(255,255,255,0.8)',
                        textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                      }}>
                        Don't have an account?{' '}
                        <Link
                          component="button"
                          variant="body2"
                          onClick={() => navigate('/register')}
                          sx={{ 
                            color: 'white', 
                            fontWeight: 600,
                            textDecoration: 'underline',
                            textShadow: '0 1px 2px rgba(0,0,0,0.2)',
                            '&:hover': { 
                              color: 'rgba(255,255,255,0.9)',
                              transform: 'scale(1.05)',
                              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                            },
                            transition: 'all 0.2s ease',
                          }}
                        >
                          Register here
                        </Link>
                      </Typography>
                    </Box>
                  </Fade>
                </Stack>
              </form>
            </Box>
          </Paper>
        </Fade>
      </Container>
    </Box>

      <ConsentForm
        open={showConsentForm}
        onClose={handleCloseConsentForm}
        onAccept={handleAcceptConsent}
        mode="login"
      />
    </>
  );
};

export default Login; 