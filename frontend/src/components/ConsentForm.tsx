import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
} from '@mui/material';

interface ConsentFormProps {
  open: boolean;
  onClose: () => void;
  onAccept: () => void;
}

const ConsentForm: React.FC<ConsentFormProps> = ({ open, onClose, onAccept }) => {
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle sx={{ color: '#0072C6' }}>
        Consent to Collect, Use, and Disclose Personal Health Information
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ fontFamily: 'Arial, sans-serif', lineHeight: 1.6 }}>
          <Typography variant="body1" gutterBottom>
            <strong>Effective Date:</strong> {new Date().toLocaleDateString()}
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" paragraph>
              Thank you for using our Diabetes Meal Planning Assistant. This tool uses artificial intelligence to help you generate personalized meal plans. As part of this service, we collect certain personal health information (PHI).
            </Typography>
            <Typography variant="body1" paragraph>
              Under Ontario's <em>Personal Health Information Protection Act, 2004</em> (PHIPA), we are required to obtain your informed consent before collecting, using, or disclosing your PHI. Please review the following carefully.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>1. What Information We Collect</Typography>
            <ul>
              <li>Name and contact details (email, phone)</li>
              <li>Health information (e.g., age, weight, diabetes type/status, dietary preferences)</li>
              <li>Responses you provide in the app (e.g., symptoms, goals)</li>
              <li>Chat interactions and meal plan history</li>
            </ul>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>2. Purpose of Collection</Typography>
            <Typography variant="body1">Your personal health information will be used to:</Typography>
            <ul>
              <li>Generate personalized meal and lifestyle recommendations</li>
              <li>Improve the accuracy and relevance of AI-generated content</li>
              <li>Send notifications or alerts about your plan (if opted-in)</li>
              <li>Provide usage analytics (de-identified) to improve the service</li>
            </ul>
            <Typography variant="body1">
              We do <strong>not</strong> use your information for marketing or sell it to third parties.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>3. How We Use AI</Typography>
            <Typography variant="body1" paragraph>
              This app uses AI models hosted in <strong>Microsoft Azure's Canadian data centers</strong> to generate your meal plans. Your data is <strong>not</strong> used to train external models. All processing is done securely and is strictly for generating recommendations—not for diagnosis or medical treatment.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>4. Who Has Access</Typography>
            <Typography variant="body1">Your data is accessed only by:</Typography>
            <ul>
              <li>You (through your account)</li>
              <li>Authorized members of our development or clinical team, for support or review</li>
            </ul>
            <Typography variant="body1">
              No one else will have access without your explicit permission or unless required by law.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>5. Data Protection and Storage</Typography>
            <ul>
              <li>Encryption in transit and at rest (TLS, AES-256)</li>
              <li>Secure storage in Azure Canada East region</li>
              <li>Role-based access control and monitoring</li>
            </ul>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>6. Data Retention</Typography>
            <Typography variant="body1">
              We retain your information only as long as necessary to provide the service or as required by law. You may request deletion of your data at any time.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>7. Your Rights</Typography>
            <Typography variant="body1">Under PHIPA, you have the right to:</Typography>
            <ul>
              <li>Access or correct your information</li>
              <li>Withdraw your consent at any time</li>
              <li>Request deletion or a copy of your data</li>
              <li>File a complaint with the Information and Privacy Commissioner of Ontario</li>
            </ul>
            <Typography variant="body1">
              To exercise your rights, contact us at:<br />
              📧 <strong>support@mirakalous.com</strong><br />
              📞 <strong>647-292-3991</strong>
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>8. Important Disclaimers</Typography>
            <ul>
              <li>This tool <strong>does not replace medical advice</strong>. Always consult a healthcare provider before making health decisions.</li>
              <li>AI-generated content may not be appropriate for all health conditions.</li>
            </ul>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
        <Button onClick={onAccept} color="primary" variant="contained">
          I Accept
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConsentForm; 