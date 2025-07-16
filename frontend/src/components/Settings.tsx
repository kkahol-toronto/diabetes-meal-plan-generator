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
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { api } from '../utils/api';
import { handleAuthError } from '../utils/auth';

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

  const getExportSizeEstimate = () => {
    const sizes = { 'Small': 1, 'Medium': 5, 'Large': 20 };
    const totalMB = selectedDataTypes.reduce((total, type) => {
      const option = dataTypeOptions.find(opt => opt.id === type);
      return total + (sizes[option?.size as keyof typeof sizes] || 1);
    }, 0);
    return `~${totalMB}MB`;
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <SecurityIcon sx={{ mr: 2, color: 'primary.main' }} />
          Privacy & Data Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your personal data, privacy preferences, and exercise your data rights in compliance with GDPR and privacy regulations.
        </Typography>
      </Box>
      
      <Alert 
        severity="info" 
        sx={{ mb: 4 }}
        action={
          <Tooltip title="Learn more about your privacy rights">
            <IconButton size="small" color="inherit">
              <InfoIcon />
            </IconButton>
          </Tooltip>
        }
      >
        You have full control over your personal health data. Export, modify consent preferences, or delete your account at any time.
      </Alert>

      <Grid container spacing={3}>
        {/* Data Export Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <DownloadIcon sx={{ mr: 1, color: 'primary.main' }} />
                Download My Data
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Export your personal health data in a professional format. Choose what data to include and your preferred format.
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Chip 
                  label="GDPR Compliant" 
                  color="success" 
                  size="small" 
                  icon={<CheckIcon />}
                  sx={{ mr: 1 }}
                />
                <Chip 
                  label="Secure Export" 
                  color="primary" 
                  size="small" 
                  icon={<SecurityIcon />}
                />
              </Box>

              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() => setExportDialogOpen(true)}
                fullWidth
                sx={{ mt: 2 }}
              >
                Export My Data
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Consent Management */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
                Privacy Preferences
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Manage your consent preferences and data usage settings.
              </Typography>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Current Settings:</strong>
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Marketing Communications</Typography>
                    <Switch 
                      checked={consentSettings.marketing_consent} 
                      size="small"
                      disabled
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Analytics & Insights</Typography>
                    <Switch 
                      checked={consentSettings.analytics_consent} 
                      size="small"
                      disabled
                    />
                  </Box>
                </Box>
              </Box>

              <Button
                variant="outlined"
                onClick={() => setConsentDialogOpen(true)}
                fullWidth
                sx={{ mt: 2 }}
              >
                Update Preferences
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Account Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Email</Typography>
                  <Typography variant="body1">{userInfo?.email || 'Loading...'}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Account Type</Typography>
                  <Typography variant="body1">
                    {userInfo?.is_admin ? 'Administrator' : 'Standard User'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Data Policy Version</Typography>
                  <Typography variant="body1">{userInfo?.policy_version || '1.0'}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Member Since</Typography>
                  <Typography variant="body1">
                    {userInfo?.consent_timestamp ? 
                      new Date(userInfo.consent_timestamp).toLocaleDateString() : 
                      'Unknown'
                    }
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Danger Zone */}
        <Grid item xs={12}>
          <Card sx={{ borderColor: 'error.main', borderWidth: 1, borderStyle: 'solid' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
                <WarningIcon sx={{ mr: 1 }} />
                Danger Zone
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Permanently delete your account and all associated data. This action cannot be undone.
              </Typography>
              
              <Alert severity="warning" sx={{ mb: 2 }}>
                Account deletion will remove all your health data, meal plans, consumption history, and chat conversations.
              </Alert>

              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => setDeleteDialogOpen(true)}
              >
                Delete My Account
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
    </Container>
  );
};

export default Settings; 