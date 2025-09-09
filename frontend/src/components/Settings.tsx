import React, { useState, useEffect } from 'react';
import config from '../config/environment';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  TextField,
  Chip,
  LinearProgress,
  Switch,
  Grid,
  IconButton,
  Tooltip,
  Fade,
  Slide,
  Zoom,
  keyframes,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Security as SecurityIcon,
  Description as DescriptionIcon,
  PictureAsPdf as PdfIcon,
  DataObject as JsonIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Close as CloseIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { api } from '../utils/api';
import { handleAuthError } from '../utils/auth';

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

interface ConsentSettings {
  consent_given: boolean;
  marketing_consent: boolean;
  analytics_consent: boolean;
  data_retention_preference: string;
}

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const { showNotification } = useApp();
  
  // Dialog states
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [consentDialogOpen, setConsentDialogOpen] = useState(false);
  
  // Export options
  const [selectedDataTypes, setSelectedDataTypes] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'json' | 'docx'>('pdf');
  const [isExporting, setIsExporting] = useState(false);
  
  // Delete account
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deletionType, setDeletionType] = useState<'complete' | 'anonymize'>('complete');
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Consent settings
  const [consentSettings, setConsentSettings] = useState<ConsentSettings>({
    consent_given: true,
    marketing_consent: false,
    analytics_consent: true,
    data_retention_preference: 'standard'
  });
  
  // User info
  const [userInfo, setUserInfo] = useState<any>(null);

  const dataTypeOptions = [
    { 
      id: 'profile', 
      label: 'Profile & Health Information', 
      description: 'Medical conditions, medications, allergies, vital signs',
      icon: <SecurityIcon />,
      size: 'Small'
    },
    { 
      id: 'meal_plans', 
      label: 'Meal Plans', 
      description: 'Generated meal plans with nutritional information',
      icon: <DescriptionIcon />,
      size: 'Medium'
    },
    { 
      id: 'consumption_history', 
      label: 'Food Consumption History', 
      description: 'Logged foods with nutritional analysis and medical ratings',
      icon: <DescriptionIcon />,
      size: 'Large'
    },
    { 
      id: 'chat_history', 
      label: 'AI Coach Conversations', 
      description: 'Chat history with AI health coach',
      icon: <DescriptionIcon />,
      size: 'Large'
    },
    { 
      id: 'recipes', 
      label: 'Recipes', 
      description: 'Recipe collection and meal suggestions',
      icon: <DescriptionIcon />,
      size: 'Medium'
    },
    { 
      id: 'shopping_lists', 
      label: 'Shopping Lists', 
      description: 'Generated shopping lists',
      icon: <DescriptionIcon />,
      size: 'Small'
    },
  ];

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${config.API_URL}/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUserInfo(data);
        
        // Set consent settings from user data
        setConsentSettings({
          consent_given: data.consent_given || true,
          marketing_consent: data.marketing_consent || false,
          analytics_consent: data.analytics_consent || true,
          data_retention_preference: data.data_retention_preference || 'standard'
        });
      }
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
  };

  const handleExportData = async () => {
    if (selectedDataTypes.length === 0) {
      showNotification('Please select at least one data type to export', 'warning');
      return;
    }

    setIsExporting(true);
    try {
      // Make a direct fetch call for file downloads with proper error handling
      const downloadResponse = await fetch(`${config.API_URL}/privacy/export-data`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data_types: selectedDataTypes,
          format_type: exportFormat,
        }),
      });

      if (!downloadResponse.ok) {
        if (downloadResponse.status === 401) {
          handleAuthError(downloadResponse, navigate);
          return;
        }
        throw new Error(`Export failed: ${downloadResponse.statusText}`);
      }

      if (exportFormat === 'json') {
        const data = await downloadResponse.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health_data_export_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const blob = await downloadResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health_data_export_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
      
      showNotification('Data exported successfully!', 'success');
      setExportDialogOpen(false);
      setSelectedDataTypes([]);
    } catch (error: any) {
      console.error('Export error:', error);
      if (error.status === 401 || error.message?.includes('Authentication')) {
        handleAuthError(error, navigate);
      } else {
        showNotification(`Export failed: ${error.message || 'Unknown error'}`, 'error');
      }
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation.toUpperCase() !== 'DELETE') {
      showNotification('Please type "DELETE" to confirm account deletion', 'warning');
      return;
    }

    setIsDeleting(true);
    try {
      const response = await fetch(`${config.API_URL}/privacy/delete-account`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          deletion_type: deletionType,
          confirmation: deleteConfirmation,
        }),
      });

      if (response.ok) {
        showNotification('Account deleted successfully', 'success');
        localStorage.removeItem('token');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        const errorData = await response.json();
        showNotification(`Deletion failed: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Account deletion failed:', error);
      showNotification('Account deletion failed. Please try again.', 'error');
    } finally {
      setIsDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  const handleUpdateConsent = async () => {
    try {
      const response = await fetch(`${config.API_URL}/privacy/update-consent`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(consentSettings),
      });

      if (response.ok) {
        showNotification('Consent preferences updated successfully', 'success');
        setConsentDialogOpen(false);
        fetchUserInfo(); // Refresh user info
      } else {
        const errorData = await response.json();
        showNotification(`Update failed: ${errorData.detail}`, 'error');
      }
    } catch (error) {
      console.error('Consent update failed:', error);
      showNotification('Consent update failed. Please try again.', 'error');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    localStorage.removeItem('userProfile');
    localStorage.removeItem('userProfile_backup');
    showNotification('You have been logged out successfully', 'info');
    navigate('/login');
  };

  const getExportSizeEstimate = () => {
    const sizes = { 'Small': 1, 'Medium': 5, 'Large': 20 };
    const totalMB = selectedDataTypes.reduce((total, type) => {
      const option = dataTypeOptions.find(opt => opt.id === type);
      return total + (sizes[option?.size as keyof typeof sizes] || 1);
    }, 0);
    return `~${totalMB}MB`;
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      py: { xs: 1, sm: 2 },
      px: { xs: 1, sm: 2 },
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
          <Paper elevation={0} sx={{ 
            p: { xs: 2, sm: 3 },
            mb: 3,
            borderRadius: '24px',
            background: 'rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            animation: `${fadeInScale} 0.8s ease-out`,
            position: 'relative',
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
          }}>
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              <Slide direction="down" in={true} timeout={800}>
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h4" gutterBottom sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    color: 'white',
                    fontWeight: 'bold',
                    fontSize: { xs: '1.75rem', sm: '2.125rem' },
                    textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    animation: `${bounceIn} 1s ease-out 0.3s both`
                  }}>
                    <Box sx={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      borderRadius: '16px',
                      p: 1.5,
                      mr: 2,
                      boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                      animation: `${float} 3s ease-in-out infinite`
                    }}>
                      <SecurityIcon sx={{ color: 'white', fontSize: '1.5rem' }} />
                    </Box>
                    🔒 Privacy & Settings
                  </Typography>
                  <Typography variant="body1" sx={{
                    color: 'rgba(255, 255, 255, 0.9)',
                    textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                    animation: `${slideInUp} 0.8s ease-out 0.5s both`
                  }}>
                    Manage your personal data, privacy preferences, and exercise your data rights
                  </Typography>
                </Box>
              </Slide>
            </Box>
          </Paper>
        </Fade>
        <Slide direction="up" in={true} timeout={1200}>
          <Alert 
            severity="info" 
            sx={{ 
              mb: 4,
              borderRadius: '16px',
              background: 'rgba(33, 150, 243, 0.1)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(33, 150, 243, 0.3)',
              color: 'white',
              '& .MuiAlert-icon': {
                color: 'white'
              },
              animation: `${slideInUp} 0.8s ease-out 0.7s both`
            }}
            action={
              <Tooltip title="Learn more about your privacy rights">
                <IconButton size="small" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                  <InfoIcon />
                </IconButton>
              </Tooltip>
            }
          >
            <Typography sx={{ 
              color: 'white',
              fontWeight: 500,
              textShadow: '0 1px 2px rgba(0,0,0,0.1)'
            }}>
              🛡️ You have full control over your personal health data. Export, modify consent preferences, or delete your account at any time.
            </Typography>
          </Alert>
        </Slide>

        <Grid container spacing={3}>
          {/* Data Export Section */}
          <Grid item xs={12}>
            <Zoom in={true} timeout={600} style={{ transitionDelay: '0.9s' }}>
              <Card sx={{ 
                borderRadius: '20px',
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
                  borderRadius: '20px',
                  animation: `${shimmer} 4s ease-in-out infinite`,
                  backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
                  backgroundSize: '200px 100%',
                  backgroundRepeat: 'no-repeat',
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(102, 126, 234, 0.2)',
                  background: 'rgba(255, 255, 255, 0.15)',
                },
              }}>
                <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    color: 'white',
                    fontWeight: 600,
                    textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                  }}>
                    <Box sx={{
                      background: 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
                      borderRadius: '12px',
                      p: 1,
                      mr: 2,
                      boxShadow: '0 3px 10px rgba(33, 150, 243, 0.3)',
                      animation: `${float} 3s ease-in-out infinite`
                    }}>
                      <DownloadIcon sx={{ color: 'white', fontSize: '1.2rem' }} />
                    </Box>
                    📥 Download My Data
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    mb: 3,
                    color: 'rgba(255, 255, 255, 0.8)',
                    textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                    lineHeight: 1.5
                  }}>
                    Export your personal health data in a professional format. Choose what data to include and your preferred format.
                  </Typography>
                  
                  <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip 
                      label="✅ GDPR Compliant" 
                      size="small" 
                      icon={<CheckIcon />}
                      sx={{
                        background: 'rgba(76, 175, 80, 0.2)',
                        color: 'rgba(255, 255, 255, 0.9)',
                        border: '1px solid rgba(76, 175, 80, 0.3)',
                        fontWeight: 500,
                      }}
                    />
                    <Chip 
                      label="🔒 Secure Export" 
                      size="small" 
                      icon={<SecurityIcon />}
                      sx={{
                        background: 'rgba(102, 126, 234, 0.2)',
                        color: 'rgba(255, 255, 255, 0.9)',
                        border: '1px solid rgba(102, 126, 234, 0.3)',
                        fontWeight: 500,
                      }}
                    />
                  </Box>

                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={() => setExportDialogOpen(true)}
                    fullWidth
                    sx={{
                      background: 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
                      color: 'white',
                      borderRadius: '50px',
                      py: 1.5,
                      fontWeight: 600,
                      textTransform: 'none',
                      fontSize: '1rem',
                      boxShadow: '0 4px 15px rgba(33, 150, 243, 0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #1976D2 0%, #1565C0 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(33, 150, 243, 0.5)',
                        animation: `${glow} 2s ease-in-out infinite`,
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    📤 Export My Data
                  </Button>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>

          {/* Privacy Preferences */}
          <Grid item xs={12}>
            <Zoom in={true} timeout={600} style={{ transitionDelay: '1.1s' }}>
              <Card sx={{ 
                borderRadius: '20px',
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
                  borderRadius: '20px',
                  animation: `${shimmer} 4s ease-in-out infinite`,
                  backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
                  backgroundSize: '200px 100%',
                  backgroundRepeat: 'no-repeat',
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(102, 126, 234, 0.2)',
                  background: 'rgba(255, 255, 255, 0.15)',
                },
              }}>
                <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    color: 'white',
                    fontWeight: 600,
                    textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                  }}>
                    <Box sx={{
                      background: 'linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%)',
                      borderRadius: '12px',
                      p: 1,
                      mr: 2,
                      boxShadow: '0 3px 10px rgba(156, 39, 176, 0.3)',
                      animation: `${float} 3s ease-in-out infinite`
                    }}>
                      <SecurityIcon sx={{ color: 'white', fontSize: '1.2rem' }} />
                    </Box>
                    🔐 Privacy Preferences
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    mb: 3,
                    color: 'rgba(255, 255, 255, 0.8)',
                    textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                    lineHeight: 1.5
                  }}>
                    Manage your consent preferences and data usage settings.
                  </Typography>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" sx={{ 
                      mb: 2,
                      color: 'rgba(255, 255, 255, 0.9)',
                      fontWeight: 600,
                      textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                    }}>
                      ⚙️ Current Settings:
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        p: 2,
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        <Typography variant="body2" sx={{ 
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontWeight: 500
                        }}>
                          📧 Marketing Communications
                        </Typography>
                        <Switch 
                          checked={consentSettings.marketing_consent} 
                          size="small"
                          onChange={(e) => {
                            setConsentSettings({
                              ...consentSettings,
                              marketing_consent: e.target.checked
                            });
                            showNotification(
                              `Marketing Communications ${e.target.checked ? 'enabled' : 'disabled'}`,
                              'success'
                            );
                          }}
                          sx={{
                            '& .MuiSwitch-thumb': {
                              backgroundColor: consentSettings.marketing_consent ? '#4CAF50' : '#f44336',
                            },
                            '& .MuiSwitch-track': {
                              backgroundColor: 'rgba(255, 255, 255, 0.3)',
                            }
                          }}
                        />
                      </Box>
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        p: 2,
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        <Typography variant="body2" sx={{ 
                          color: 'rgba(255, 255, 255, 0.9)',
                          fontWeight: 500
                        }}>
                          📊 Analytics & Insights
                        </Typography>
                        <Switch 
                          checked={consentSettings.analytics_consent} 
                          size="small"
                          onChange={(e) => {
                            setConsentSettings({
                              ...consentSettings,
                              analytics_consent: e.target.checked
                            });
                            showNotification(
                              `Analytics & Insights ${e.target.checked ? 'enabled' : 'disabled'}`,
                              'success'
                            );
                          }}
                          sx={{
                            '& .MuiSwitch-thumb': {
                              backgroundColor: consentSettings.analytics_consent ? '#4CAF50' : '#f44336',
                            },
                            '& .MuiSwitch-track': {
                              backgroundColor: 'rgba(255, 255, 255, 0.3)',
                            }
                          }}
                        />
                      </Box>
                    </Box>
                  </Box>

                  <Button
                    variant="contained"
                    onClick={() => setConsentDialogOpen(true)}
                    fullWidth
                    sx={{
                      background: 'linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%)',
                      color: 'white',
                      borderRadius: '50px',
                      py: 1.5,
                      fontWeight: 600,
                      textTransform: 'none',
                      fontSize: '1rem',
                      boxShadow: '0 4px 15px rgba(156, 39, 176, 0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #7B1FA2 0%, #6A1B9A 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(156, 39, 176, 0.5)',
                        animation: `${glow} 2s ease-in-out infinite`,
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    ⚙️ Update Preferences
                  </Button>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>

          {/* Account Information */}
          <Grid item xs={12}>
            <Zoom in={true} timeout={600} style={{ transitionDelay: '1.3s' }}>
              <Card sx={{ 
                borderRadius: '20px',
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
                  borderRadius: '20px',
                  animation: `${shimmer} 4s ease-in-out infinite`,
                  backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
                  backgroundSize: '200px 100%',
                  backgroundRepeat: 'no-repeat',
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(102, 126, 234, 0.2)',
                  background: 'rgba(255, 255, 255, 0.15)',
                },
              }}>
                <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{
                    color: 'white',
                    fontWeight: 600,
                    textShadow: '0 1px 3px rgba(0,0,0,0.2)',
                    mb: 3
                  }}>
                    👤 Account Information
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{
                        p: 2,
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        <Typography variant="body2" sx={{ 
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontSize: '0.8rem',
                          mb: 0.5
                        }}>
                          📧 Email
                        </Typography>
                        <Typography variant="body1" sx={{
                          color: 'white',
                          fontWeight: 500,
                          textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}>
                          {userInfo?.email || 'Loading...'}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{
                        p: 2,
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        <Typography variant="body2" sx={{ 
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontSize: '0.8rem',
                          mb: 0.5
                        }}>
                          👑 Account Type
                        </Typography>
                        <Typography variant="body1" sx={{
                          color: 'white',
                          fontWeight: 500,
                          textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}>
                          {userInfo?.is_admin ? '👑 Administrator' : '👤 Standard User'}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{
                        p: 2,
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        <Typography variant="body2" sx={{ 
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontSize: '0.8rem',
                          mb: 0.5
                        }}>
                          📋 Data Policy Version
                        </Typography>
                        <Typography variant="body1" sx={{
                          color: 'white',
                          fontWeight: 500,
                          textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}>
                          v{userInfo?.policy_version || '1.0'}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{
                        p: 2,
                        borderRadius: '12px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        <Typography variant="body2" sx={{ 
                          color: 'rgba(255, 255, 255, 0.7)',
                          fontSize: '0.8rem',
                          mb: 0.5
                        }}>
                          📅 Member Since
                        </Typography>
                        <Typography variant="body1" sx={{
                          color: 'white',
                          fontWeight: 500,
                          textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                        }}>
                          {userInfo?.consent_timestamp ? 
                            new Date(userInfo.consent_timestamp).toLocaleDateString() : 
                            'Unknown'
                          }
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>

          {/* Account Actions */}
          <Grid item xs={12}>
            <Zoom in={true} timeout={600} style={{ transitionDelay: '1.5s' }}>
              <Card sx={{ 
                borderRadius: '20px',
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
                  borderRadius: '20px',
                  animation: `${shimmer} 4s ease-in-out infinite`,
                  backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
                  backgroundSize: '200px 100%',
                  backgroundRepeat: 'no-repeat',
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(102, 126, 234, 0.2)',
                  background: 'rgba(255, 255, 255, 0.15)',
                },
              }}>
                <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    color: 'white',
                    fontWeight: 600,
                    textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                  }}>
                    <Box sx={{
                      background: 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)',
                      borderRadius: '12px',
                      p: 1,
                      mr: 2,
                      boxShadow: '0 3px 10px rgba(255, 107, 107, 0.3)',
                      animation: `${float} 3s ease-in-out infinite`
                    }}>
                      <LogoutIcon sx={{ color: 'white', fontSize: '1.2rem' }} />
                    </Box>
                    🚪 Account Actions
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    mb: 3,
                    color: 'rgba(255, 255, 255, 0.8)',
                    textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                    lineHeight: 1.5
                  }}>
                    Sign out of your account or manage your session.
                  </Typography>
                  
                  <Button
                    variant="contained"
                    startIcon={<LogoutIcon />}
                    onClick={handleLogout}
                    fullWidth
                    sx={{
                      background: 'linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%)',
                      color: 'white',
                      borderRadius: '50px',
                      py: 1.5,
                      fontWeight: 600,
                      textTransform: 'none',
                      fontSize: '1rem',
                      boxShadow: '0 4px 15px rgba(255, 107, 107, 0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #FF5252 0%, #26A69A 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(255, 107, 107, 0.5)',
                        animation: `${glow} 2s ease-in-out infinite`,
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    🚪 Sign Out
                  </Button>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>

          {/* Danger Zone */}
          <Grid item xs={12}>
            <Zoom in={true} timeout={600} style={{ transitionDelay: '1.7s' }}>
              <Card sx={{ 
                borderRadius: '20px',
                background: 'rgba(244, 67, 54, 0.1)',
                backdropFilter: 'blur(20px)',
                border: '2px solid rgba(244, 67, 54, 0.3)',
                boxShadow: '0 8px 32px rgba(244, 67, 54, 0.1)',
                transition: 'all 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(45deg, rgba(244, 67, 54, 0.05), rgba(244, 67, 54, 0.02))',
                  borderRadius: '20px',
                  animation: `${shimmer} 4s ease-in-out infinite`,
                  backgroundImage: 'linear-gradient(45deg, transparent 30%, rgba(244, 67, 54, 0.1) 50%, transparent 70%)',
                  backgroundSize: '200px 100%',
                  backgroundRepeat: 'no-repeat',
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 12px 40px rgba(244, 67, 54, 0.2)',
                  background: 'rgba(244, 67, 54, 0.15)',
                  animation: `${pulse} 2s ease-in-out infinite`,
                },
              }}>
                <CardContent sx={{ position: 'relative', zIndex: 1, p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    color: '#ff6b6b',
                    fontWeight: 600,
                    textShadow: '0 1px 3px rgba(0,0,0,0.2)'
                  }}>
                    <Box sx={{
                      background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                      borderRadius: '12px',
                      p: 1,
                      mr: 2,
                      boxShadow: '0 3px 10px rgba(244, 67, 54, 0.3)',
                      animation: `${float} 3s ease-in-out infinite`
                    }}>
                      <WarningIcon sx={{ color: 'white', fontSize: '1.2rem' }} />
                    </Box>
                    ⚠️ Danger Zone
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    mb: 3,
                    color: 'rgba(255, 255, 255, 0.8)',
                    textShadow: '0 1px 2px rgba(0,0,0,0.1)',
                    lineHeight: 1.5
                  }}>
                    Permanently delete your account and all associated data. This action cannot be undone.
                  </Typography>
                  
                  <Alert 
                    severity="warning" 
                    sx={{ 
                      mb: 3,
                      borderRadius: '12px',
                      background: 'rgba(255, 152, 0, 0.1)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255, 152, 0, 0.3)',
                      color: 'white',
                      '& .MuiAlert-icon': {
                        color: '#ffab40'
                      }
                    }}
                  >
                    <Typography sx={{ 
                      color: 'white',
                      fontWeight: 500,
                      textShadow: '0 1px 2px rgba(0,0,0,0.1)'
                    }}>
                      🗑️ Account deletion will remove all your health data, meal plans, consumption history, and chat conversations.
                    </Typography>
                  </Alert>

                  <Button
                    variant="contained"
                    startIcon={<DeleteIcon />}
                    onClick={() => setDeleteDialogOpen(true)}
                    fullWidth
                    sx={{
                      background: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
                      color: 'white',
                      borderRadius: '50px',
                      py: 1.5,
                      fontWeight: 600,
                      textTransform: 'none',
                      fontSize: '1rem',
                      boxShadow: '0 4px 15px rgba(244, 67, 54, 0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #d32f2f 0%, #c62828 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(244, 67, 54, 0.5)',
                        animation: `${pulse} 1s ease-in-out infinite`,
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    🗑️ Delete My Account
                  </Button>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>
        </Grid>
      </Container>
      
      {/* Dialogs */}
      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          Export Your Health Data
          <IconButton onClick={() => setExportDialogOpen(false)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select the data types you want to include in your export:
          </Typography>
          
          <FormGroup>
            {dataTypeOptions.map((option) => (
              <FormControlLabel
                key={option.id}
                control={
                  <Checkbox
                    checked={selectedDataTypes.includes(option.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDataTypes([...selectedDataTypes, option.id]);
                      } else {
                        setSelectedDataTypes(selectedDataTypes.filter(id => id !== option.id));
                      }
                    }}
                  />
                }
                label={
                  <Box sx={{ ml: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                      {option.icon}
                      <Typography variant="body1" sx={{ ml: 1, fontWeight: 'medium' }}>
                        {option.label}
                      </Typography>
                      <Chip 
                        label={option.size} 
                        size="small" 
                        variant="outlined" 
                        sx={{ ml: 'auto' }} 
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 4 }}>
                      {option.description}
                    </Typography>
                  </Box>
                }
                sx={{ alignItems: 'flex-start', mb: 2 }}
              />
            ))}
          </FormGroup>

          {selectedDataTypes.length > 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Estimated export size: {getExportSizeEstimate()}
            </Alert>
          )}

          <Divider sx={{ my: 3 }} />
          
          <Typography variant="subtitle1" gutterBottom>Export Format:</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              variant={exportFormat === 'pdf' ? 'contained' : 'outlined'}
              startIcon={<PdfIcon />}
              onClick={() => setExportFormat('pdf')}
              size="small"
            >
              PDF Report
            </Button>
            <Button
              variant={exportFormat === 'json' ? 'contained' : 'outlined'}
              startIcon={<JsonIcon />}
              onClick={() => setExportFormat('json')}
              size="small"
            >
              JSON Data
            </Button>
            <Button
              variant={exportFormat === 'docx' ? 'contained' : 'outlined'}
              startIcon={<DescriptionIcon />}
              onClick={() => setExportFormat('docx')}
              size="small"
              disabled
            >
              Word Document
            </Button>
          </Box>

          {isExporting && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>Preparing your export...</Typography>
              <LinearProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)} disabled={isExporting}>
            Cancel
          </Button>
          <Button 
            onClick={handleExportData} 
            variant="contained"
            disabled={selectedDataTypes.length === 0 || isExporting}
            startIcon={isExporting ? null : <DownloadIcon />}
          >
            {isExporting ? 'Exporting...' : 'Export Data'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Consent Update Dialog */}
      <Dialog open={consentDialogOpen} onClose={() => setConsentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Update Privacy Preferences</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Manage how your data is used within the application:
          </Typography>
          
          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  checked={consentSettings.marketing_consent}
                  onChange={(e) => setConsentSettings({
                    ...consentSettings,
                    marketing_consent: e.target.checked
                  })}
                />
              }
              label={
                <Box>
                  <Typography variant="body1">Marketing Communications</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Receive updates about new features and health tips
                  </Typography>
                </Box>
              }
            />
            <FormControlLabel
              control={
                <Switch
                  checked={consentSettings.analytics_consent}
                  onChange={(e) => setConsentSettings({
                    ...consentSettings,
                    analytics_consent: e.target.checked
                  })}
                />
              }
              label={
                <Box>
                  <Typography variant="body1">Analytics & Insights</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Help improve the app with anonymous usage analytics
                  </Typography>
                </Box>
              }
            />
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConsentDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpdateConsent} variant="contained">
            Update Preferences
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle color="error" sx={{ display: 'flex', alignItems: 'center' }}>
          <WarningIcon sx={{ mr: 1 }} />
          Delete Account
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              This action will permanently delete:
            </Typography>
            <List dense>
              <ListItem sx={{ py: 0 }}>
                <ListItemText primary="• Profile and health information" />
              </ListItem>
              <ListItem sx={{ py: 0 }}>
                <ListItemText primary="• All meal plans and recipes" />
              </ListItem>
              <ListItem sx={{ py: 0 }}>
                <ListItemText primary="• Food consumption history" />
              </ListItem>
              <ListItem sx={{ py: 0 }}>
                <ListItemText primary="• Chat conversations with AI coach" />
              </ListItem>
            </List>
          </Alert>

          <Typography variant="body2" sx={{ mb: 2 }}>
            Type <strong>DELETE</strong> to confirm:
          </Typography>
          <TextField
            fullWidth
            value={deleteConfirmation}
            onChange={(e) => setDeleteConfirmation(e.target.value)}
            placeholder="Type DELETE to confirm"
            error={deleteConfirmation !== '' && deleteConfirmation.toUpperCase() !== 'DELETE'}
            sx={{ mb: 2 }}
          />

          {isDeleting && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>Deleting your account...</Typography>
              <LinearProgress color="error" />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={isDeleting}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteAccount} 
            color="error" 
            variant="contained"
            disabled={deleteConfirmation.toUpperCase() !== 'DELETE' || isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Account'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings; 