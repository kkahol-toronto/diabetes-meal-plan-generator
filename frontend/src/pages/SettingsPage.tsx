import React, { useState } from 'react';
import { 
  Container, Typography, Button, Box, Paper, 
  Dialog, DialogActions, DialogContent, DialogContentText, 
  DialogTitle, Divider, Alert, CircularProgress,
  Stack
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SecurityIcon from '@mui/icons-material/Security';
import DownloadIcon from '@mui/icons-material/Download';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../contexts/AppContext';
import { deleteUserData, downloadUserData } from '../utils/api';

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showNotification } = useApp();
  const [isDeleting, setIsDeleting] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [loadingJSON, setLoadingJSON] = useState(false);
  const [loadingPDF, setLoadingPDF] = useState(false);

  const handleDeleteRequest = () => {
    setConfirmDialogOpen(true);
  };

  const handleCancelDelete = () => {
    setConfirmDialogOpen(false);
  };

  const handleConfirmDelete = async () => {
    setIsDeleting(true);
    setConfirmDialogOpen(false);
    
    try {
      await deleteUserData();
      showNotification('Your account and all associated data have been permanently deleted.', 'success');
      localStorage.removeItem('token');
      navigate('/register');
    } catch (error) {
      console.error('Failed to delete user data:', error);
      showNotification('Failed to delete your data. Please try again later.', 'error');
      setIsDeleting(false);
    }
  };

  const downloadJSON = async () => {
    setLoadingJSON(true);
    try {
      const response = await downloadUserData('json');
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'my-data.json';
      link.click();
      URL.revokeObjectURL(url);
      showNotification('Your data has been downloaded successfully.', 'success');
    } catch (error) {
      console.error('Failed to download data:', error);
      showNotification('Failed to download your data. Please try again later.', 'error');
    } finally {
      setLoadingJSON(false);
    }
  };

  const downloadPDF = async () => {
    setLoadingPDF(true);
    try {
      const response = await downloadUserData('pdf');
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'my-data.pdf';
      link.click();
      URL.revokeObjectURL(url);
      showNotification('Your PDF report has been downloaded successfully.', 'success');
    } catch (error) {
      console.error('Failed to download PDF:', error);
      showNotification('Failed to download your PDF report. Please try again later.', 'error');
    } finally {
      setLoadingPDF(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom fontWeight="500" color="primary">
        Settings
      </Typography>
      
      <Paper elevation={2} sx={{ mt: 4, p: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SecurityIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h5" component="h2" fontWeight="500">
            Data & Privacy
          </Typography>
        </Box>
        
        <Divider sx={{ mb: 3 }} />
        
        <Typography variant="body1" paragraph sx={{ mb: 3 }}>
          Your privacy and data security are important to us. Under data protection regulations,
          you have the right to request deletion of all your personal information stored in our system.
        </Typography>

        <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
          Export Your Data
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 2 }}>
          You can download all your personal data in JSON format for technical use or as a formatted PDF report.
        </Typography>
        
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 4 }}>
          <Button
            variant="outlined"
            color="primary"
            onClick={downloadJSON}
            disabled={loadingJSON}
            startIcon={loadingJSON ? <CircularProgress size={20} color="inherit" /> : <DownloadIcon />}
          >
            {loadingJSON ? 'Downloading...' : 'Download My Data (JSON)'}
          </Button>
          
          <Button
            variant="outlined"
            color="primary"
            onClick={downloadPDF}
            disabled={loadingPDF}
            startIcon={loadingPDF ? <CircularProgress size={20} color="inherit" /> : <PictureAsPdfIcon />}
          >
            {loadingPDF ? 'Generating PDF...' : 'Download My Data (PDF)'}
          </Button>
        </Stack>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          Deleting your account will permanently remove all your personal data, including meal plans,
          consumption records, and all health information. This action cannot be reversed.
        </Alert>
        
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-start' }}>
          <Button 
            variant="contained" 
            color="error" 
            onClick={handleDeleteRequest}
            disabled={isDeleting}
            startIcon={isDeleting ? <CircularProgress size={20} color="inherit" /> : <DeleteIcon />}
            sx={{ 
              fontWeight: 'medium',
              px: 3,
              py: 1
            }}
          >
            {isDeleting ? 'Deleting Account...' : 'Delete My Account and Data'}
          </Button>
        </Box>
      </Paper>
      
      <Dialog
        open={confirmDialogOpen}
        onClose={handleCancelDelete}
        aria-labelledby="delete-confirmation-dialog"
      >
        <DialogTitle id="delete-confirmation-dialog" color="error">
          Confirm Account Deletion
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you absolutely sure you want to delete your account and all associated data? 
            This action is permanent and cannot be undone. All your meal plans, consumption records, 
            health information, and account details will be permanently removed from our system.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2, pt: 0 }}>
          <Button onClick={handleCancelDelete} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} variant="contained" color="error" autoFocus>
            Yes, Delete My Account
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SettingsPage;
