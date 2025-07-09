import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Checkbox,
  FormControlLabel,
  TextField,
  Divider,
  Alert,
  Paper,
  Stack,
  IconButton,
} from '@mui/material';
import { Close as CloseIcon, Gavel as GavelIcon } from '@mui/icons-material';

interface ConsentFormProps {
  open: boolean;
  onClose: () => void;
  onAccept: (signatureData: {
    requiredConsent: boolean;
    researchConsent: boolean;
    signature: string;
    timestamp: string;
    ipAddress?: string;
  }) => void;
  mode?: 'registration' | 'login'; // Different modes for different contexts
}

const ConsentForm: React.FC<ConsentFormProps> = ({ 
  open, 
  onClose, 
  onAccept, 
  mode = 'registration' 
}) => {
  const [requiredConsent, setRequiredConsent] = useState(false);
  const [researchConsent, setResearchConsent] = useState(false);
  const [signature, setSignature] = useState('');
  const [consentText, setConsentText] = useState('');
  const [error, setError] = useState('');

  // Load consent text from public file
  useEffect(() => {
    if (open) {
      fetch('/consent.txt')
        .then(response => response.text())
        .then(text => setConsentText(text))
        .catch(error => {
          console.error('Error loading consent text:', error);
          setConsentText('Error loading consent form. Please contact support.');
        });
    }
  }, [open]);

  const handleSubmit = () => {
    if (!requiredConsent) {
      setError('You must agree to the required consent to continue.');
      return;
    }

    if (!signature.trim()) {
      setError('Electronic signature is required.');
      return;
    }

    const signatureData = {
      requiredConsent,
      researchConsent,
      signature: signature.trim(),
      timestamp: new Date().toISOString(),
      ipAddress: 'user-ip' // In production, get real IP
    };

    onAccept(signatureData);
    handleClose();
  };

  const handleClose = () => {
    setRequiredConsent(false);
    setResearchConsent(false);
    setSignature('');
    setError('');
    onClose();
  };

  const formatConsentText = (text: string) => {
    const sections = text.split(/(?=✅|🔒)/);
    return sections.map((section, index) => {
      if (section.trim() === '') return null;
      
      // Check if it's a section header
      if (section.startsWith('✅') || section.startsWith('🔒')) {
        const lines = section.split('\n');
        const title = lines[0];
        const content = lines.slice(1).join('\n');
        
        return (
          <Box key={index} sx={{ mb: 3 }}>
            <Typography 
              variant="h6" 
              sx={{ 
                color: '#1976d2', 
                fontWeight: 'bold', 
                mb: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              {title}
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                lineHeight: 1.6, 
                whiteSpace: 'pre-line',
                color: 'text.primary'
              }}
            >
              {content}
            </Typography>
          </Box>
        );
      }
      
      return (
        <Typography 
          key={index}
          variant="body2" 
          sx={{ 
            mb: 2, 
            lineHeight: 1.6, 
            whiteSpace: 'pre-line',
            color: 'text.primary'
          }}
        >
          {section}
        </Typography>
      );
    }).filter(Boolean);
  };

  return (
    <Dialog 
      open={open} 
      onClose={mode === 'registration' ? undefined : handleClose}
      maxWidth="md" 
      fullWidth
      sx={{
        '& .MuiDialog-paper': {
          maxHeight: '90vh',
          borderRadius: 2
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
        color: 'white',
        pb: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <GavelIcon />
          <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
            {mode === 'registration' ? 'Consent Agreement' : 'Updated Consent Required'}
          </Typography>
        </Box>
        {mode !== 'registration' && (
          <IconButton onClick={handleClose} sx={{ color: 'white' }}>
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      <DialogContent sx={{ p: 3 }}>
        <Paper 
          variant="outlined" 
          sx={{ 
            p: 3, 
            maxHeight: '400px', 
            overflow: 'auto',
            mb: 3,
            backgroundColor: '#fafafa'
          }}
        >
          {consentText ? formatConsentText(consentText) : (
            <Typography>Loading consent form...</Typography>
          )}
        </Paper>

        <Stack spacing={3}>
          {/* Required Consent */}
          <Paper variant="outlined" sx={{ p: 2, backgroundColor: '#fff3e0' }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={requiredConsent}
                  onChange={(e) => setRequiredConsent(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  <strong>Required:</strong> I agree to the collection and use of my personal health information as described above.
                </Typography>
              }
            />
          </Paper>

          {/* Optional Research Consent */}
          <Paper variant="outlined" sx={{ p: 2, backgroundColor: '#f3e5f5' }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={researchConsent}
                  onChange={(e) => setResearchConsent(e.target.checked)}
                  color="secondary"
                />
              }
              label={
                <Typography variant="body1">
                  <strong>Optional:</strong> I consent to the use of my de-identified data for research purposes.
                </Typography>
              }
            />
          </Paper>

          {/* Electronic Signature */}
          <Box>
            <Typography variant="h6" sx={{ mb: 2, color: '#1976d2' }}>
              Electronic Signature
            </Typography>
            <TextField
              fullWidth
              label="Type your full legal name as your electronic signature"
              value={signature}
              onChange={(e) => setSignature(e.target.value)}
              placeholder="e.g., John Smith"
              required
              variant="outlined"
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              By typing your name above, you are providing a legally binding electronic signature.
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          <Divider />

          <Alert severity="info" icon={<GavelIcon />}>
            <Typography variant="body2">
              <strong>Legal Notice:</strong> This electronic signature has the same legal effect as a handwritten signature. 
              You may withdraw your consent at any time by contacting our support team.
            </Typography>
          </Alert>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 3, gap: 2 }}>
        {mode !== 'registration' && (
          <Button onClick={handleClose} variant="outlined" size="large">
            Cancel
          </Button>
        )}
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          size="large"
          disabled={!requiredConsent || !signature.trim()}
          sx={{
            background: 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)',
            minWidth: 200,
            py: 1.5
          }}
        >
          {mode === 'registration' ? 'Sign & Continue Registration' : 'Sign & Continue Login'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConsentForm; 