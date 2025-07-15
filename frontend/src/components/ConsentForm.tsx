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
  Link,
} from '@mui/material';
import { Close as CloseIcon, Gavel as GavelIcon, Policy as PolicyIcon } from '@mui/icons-material';

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
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);

  // Privacy Policy content
  const privacyPolicyContent = `Thank you for using our Diabetes Meal Planning Assistant. This tool uses artificial intelligence to help you generate personalized meal plans. As part of this service, we collect certain personal health information (PHI).

Under Ontario's Personal Health Information Protection Act, 2004 (PHIPA), we are required to obtain your informed consent before collecting, using, or disclosing your PHI. Please review the following carefully.

1. What Information We Collect
* Name and contact details (email, phone)
* Health information (e.g., age, weight, diabetes type/status, dietary preferences)
* Responses you provide in the app (e.g., symptoms, goals)
* Chat interactions and meal plan history

2. Purpose of Collection
Your personal health information will be used to:
* Generate personalized meal and lifestyle recommendations
* Improve the accuracy and relevance of AI-generated content
* Send notifications or alerts about your plan (if opted-in)
* Provide usage analytics (de-identified) to improve the service

We do not use your information for marketing or sell it to third parties.

3. How We Use AI
This app uses AI models hosted in Microsoft Azure's Canadian data centers to generate your meal plans. Your data is not used to train external models. All processing is done securely and is strictly for generating recommendations—not for diagnosis or medical treatment.

4. Who Has Access
Your data is accessed only by:
* You (through your account)
* Authorized members of our development or clinical team, for support or review

No one else will have access without your explicit permission or unless required by law.

5. Data Protection and Storage
* Encryption in transit and at rest (TLS, AES-256)
* Secure storage in Azure Canada East region
* Role-based access control and monitoring

6. Data Retention
We retain your information only as long as necessary to provide the service or as required by law. You may request deletion of your data at any time.

7. Your Rights
Under PHIPA, you have the right to:
* Access or correct your information
* Withdraw your consent at any time
* Request deletion or a copy of your data
* File a complaint with the Information and Privacy Commissioner of Ontario

To exercise your rights, contact us at: support@mirakalous.com or 647-292-3991

8. Important Disclaimers
* This tool does not replace medical advice. Always consult a healthcare provider before making health decisions.
* AI-generated content may not be appropriate for all health conditions.`;

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

  const handleOpenPrivacyPolicy = () => {
    setShowPrivacyPolicy(true);
  };

  const handleClosePrivacyPolicy = () => {
    setShowPrivacyPolicy(false);
  };

  const formatConsentText = (text: string) => {
    // Split by common section headers instead of emojis
    const sections = text.split(/(?=Service Use|Optional Research Use|Privacy Policy – Adjusted Sections)/);
    return sections.map((section, index) => {
      if (section.trim() === '') return null;
      
      // Check if it's a section header
      if (section.startsWith('Service Use') || section.startsWith('Optional Research Use') || section.startsWith('Privacy Policy – Adjusted Sections')) {
        const lines = section.split('\n');
        const title = lines[0];
        const content = lines.slice(1).join('\n');
        
        // Process content to handle [Privacy Policy] link
        const processedContent = content.replace(
          /\[Privacy Policy\]/g,
          'PRIVACY_POLICY_LINK'
        );
        
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
              {processedContent.split('PRIVACY_POLICY_LINK').map((part, i) => (
                <React.Fragment key={i}>
                  {part}
                  {i < processedContent.split('PRIVACY_POLICY_LINK').length - 1 && (
                    <Link
                      component="button"
                      variant="body2"
                      onClick={handleOpenPrivacyPolicy}
                      sx={{
                        color: '#1976d2',
                        textDecoration: 'underline',
                        cursor: 'pointer',
                        fontWeight: 'bold'
                      }}
                    >
                      Privacy Policy
                    </Link>
                  )}
                </React.Fragment>
              ))}
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
    <>
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
                You may withdraw your consent at any time by contacting E-mail: support@mirakalous.com or at +1 (647) 292-3991.
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

      {/* Privacy Policy Modal */}
      <Dialog 
        open={showPrivacyPolicy} 
        onClose={handleClosePrivacyPolicy}
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
          background: 'linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)',
          color: 'white',
          pb: 2
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PolicyIcon />
            <Typography variant="h5" component="div" sx={{ fontWeight: 'bold' }}>
              Privacy Policy
            </Typography>
          </Box>
          <IconButton onClick={handleClosePrivacyPolicy} sx={{ color: 'white' }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ p: 3 }}>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 3, 
              maxHeight: '500px', 
              overflow: 'auto',
              backgroundColor: '#fafafa'
            }}
          >
            <Typography 
              variant="body2" 
              sx={{ 
                lineHeight: 1.6, 
                whiteSpace: 'pre-line',
                color: 'text.primary'
              }}
            >
              {privacyPolicyContent}
            </Typography>
          </Paper>
        </DialogContent>

        <DialogActions sx={{ p: 3 }}>
          <Button 
            onClick={handleClosePrivacyPolicy} 
            variant="contained" 
            size="large"
            sx={{
              background: 'linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%)',
              minWidth: 150
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ConsentForm; 